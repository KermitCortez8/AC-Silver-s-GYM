"""Carga y publica instantáneas; no ejecuta comandos de escritura."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import time
from typing import Any
from domain.services.gym_domain_service import GymDomainService, _today_iso
from domain.services.membership_lifecycle import apply_membership_expiration
from infrastructure.repositories.gym_tables import READ_STATE_KEYS, selected_resources
from infrastructure.repositories.mappers import accounts, attendance, configuration, inventory, memberships, schedules, store

from infrastructure.repositories.gym_cache import GymCache
from infrastructure.repositories.gym_table_access import GymTableAccess


class GymSnapshotReader:

    def __init__(self, database, cache: GymCache, tables: GymTableAccess, ttl: float):
        self.database, self.cache, self.tables, self.ttl = database, cache, tables, ttl

    def load(self, resources=None) -> None:
        selected = selected_resources(resources)
        # Una lectura parcial conserva las secciones cargadas anteriormente.
        remote_state = dict(self.cache.state)

        # Las lecturas son independientes; el estado se sustituye solo cuando todas terminan.
        # Se conserva el bloqueo de refresh/mutaciones y un límite de conexiones a Supabase.
        queries = [
            ("planes_membresia", self.tables.select_required, "PLANES_MEMBRESIA", "id_PM.asc"),
            ("clientes", self.database.select_all, "CLIENTES", "id_cliente.asc"),
            ("membresia", self.database.select_all, "MEMBRESIA", "id_membresia.asc"),
            ("usuario", self.tables.select_required, "USUARIO", "id_usuario.asc"),
            ("inventario", self.tables.select_required, "INVENTARIO", "id_item.asc"),
            ("mov_inv", self.tables.select_optional, "MOV_INV", "id_mov.desc"),
            ("productos_tienda", self.tables.select_required, "TIENDA_PRODUCTOS", "id_producto.asc"),
            ("pedidos_tienda", self.tables.select_required, "VENTAS", "id_venta.desc"),
            ("sale_details", self.tables.select_required, "DETALLE_VENTA", "id_detalle.asc"),
            ("catalogo_rutina", self.tables.select_required, "CATALOGO_RUTINA", "id_rutina.asc"),
            ("horario", self.tables.select_required, "HORARIO", "id_horario.asc"),
            ("horarios_servicio", self.tables.select_optional, "HORARIOS_SERVICIO", "id_horario_servicio.asc"),
            ("promociones", self.tables.select_optional, "PROMOCIONES", "id_promocion.desc"),
            ("matriculas_horario", self.database.select_all, "MATRICULAS_HORARIO", "id_matricula.asc"),
            ("rutina_progreso", self.tables.select_optional, "RUTINA_PROGRESO", "fecha.desc"),
            ("tickets_atencion", self.tables.select_optional, "TICKETS_ATENCION", "id_ticket.desc"),
            ("configuracion_gimnasio", self.tables.select_optional, "CONFIGURACION_GIMNASIO", "id_config.asc"),
            ("asistencia", self.database.select_all, "ASISTENCIA", "id_asistencia.asc"),
        ]
        queries = [query for query in queries if query[0] in selected or
                   (query[0] in {"sale_details", "productos_tienda"} and "pedidos_tienda" in selected)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            pending = {key: pool.submit(load, table, order=order) for key, load, table, order in queries}
            rows = {key: future.result() for key, future in pending.items()}

        mappers = {
            "planes_membresia": memberships._map_plan, "clientes": accounts._map_client,
            "membresia": memberships._map_membership, "usuario": accounts._map_user,
            "inventario": inventory._map_inventory, "mov_inv": inventory._map_inventory_move,
            "productos_tienda": inventory._map_product, "catalogo_rutina": schedules._map_routine,
            "horario": schedules._map_schedule, "horarios_servicio": schedules._map_service_schedule,
            "promociones": memberships._map_promotion, "matriculas_horario": schedules._map_schedule_enrollment,
            "rutina_progreso": schedules._map_routine_progress, "tickets_atencion": schedules._map_ticket,
            "asistencia": attendance._map_attendance,
        }
        for key, mapper in mappers.items():
            if key in selected:
                remote_state[key] = [mapper(row) for row in rows[key]]
        if "pedidos_tienda" in selected:
            product_names = {int(row.get("id_producto", 0) or 0): str(row.get("nombre_Producto") or "")
                             for row in rows["productos_tienda"]}
            details_by_sale: dict[int, list[dict[str, Any]]] = {}
            for detail in rows["sale_details"]:
                sale_id = int(detail.get("id_venta", 0) or 0)
                details_by_sale.setdefault(sale_id, []).append(store._map_sale_detail(detail, product_names))
            remote_state["pedidos_tienda"] = [
                store._map_sale(row, details_by_sale.get(int(row.get("id_venta", 0) or 0), []))
                for row in rows["pedidos_tienda"]
            ]
        if "configuracion_gimnasio" in selected:
            config_rows = rows["configuracion_gimnasio"]
            remote_state["configuracion_gimnasio"] = configuration._map_config(config_rows[0] if config_rows else {})
        # Recupera la etiqueta derivada sin volver a escribir Estado=false en cada lectura.
        # La vigencia se proyecta en consultas y se persiste con el comando explícito de vencimiento.
        if "clientes" in selected:
            apply_membership_expiration({
                "clientes": [row for row in remote_state["clientes"] if row["estado"] == "INACTIVO"],
                "membresia": [dict(row) for row in remote_state["membresia"]],
            }, _today_iso())
        if "horarios_servicio" in selected:
            GymDomainService(remote_state).recount_schedule()
        if "inventario" in selected:
            GymDomainService(remote_state).refresh_store_status()
        raw = dict(self.cache.raw_rows)
        for key, _load, table, _order in queries:
            # El catálogo auxiliar solo aporta nombres a pedidos. No publica una
            # versión remota nueva junto a un estado de productos todavía antiguo.
            if key != "productos_tienda" or key in selected:
                raw[table] = deepcopy(rows[key])
            if table not in self.tables.metadata.missing_tables:
                self.tables.remember_columns(table, rows[key])
        self.cache.raw_rows = raw
        self.cache.state = remote_state
        refreshed_at = time.monotonic()
        self.cache.resource_refreshed_at.update(dict.fromkeys(selected, refreshed_at))
        # El reloj global solo acredita una carga completa, nunca una lectura parcial.
        if selected == set(READ_STATE_KEYS):
            self.cache.last_refresh_at = refreshed_at

    def refresh_if_stale(self, resources=None) -> None:
        if resources is None:
            if time.monotonic() - self.cache.last_refresh_at >= self.ttl:
                self.load()
            return
        selected = selected_resources(resources)
        now = time.monotonic()
        timestamps = self.cache.resource_refreshed_at
        stale = {key for key in selected
                 if now - timestamps.get(key, 0.0) >= self.ttl}
        if stale:
            self.load(stale)

    def refresh(self, resources=None) -> None:
        with self.cache.lock:
            self.refresh_if_stale(resources)
