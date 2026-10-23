"""Coordina el estado remoto, la caché y las transacciones del gimnasio."""
from __future__ import annotations

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from typing import Any, NoReturn

from application.errors import SchemaNotReady
from domain.errors import AttendanceConflict
from infrastructure.repositories.enrollment_errors import raise_schedule_enrollment_error
from infrastructure.http_transport import database_code, error_payload
from infrastructure.repositories.schema_policy import missing_column, prepare_write
from domain.services.gym_domain_service import GymDomainService, _today_iso
from domain.services.membership_lifecycle import apply_membership_expiration
from infrastructure.supabase_client import SupabaseRestClient
from infrastructure.repositories.atomic_changes import SnapshotConflict, commit_snapshot, table_changes

from infrastructure.repositories.mappers import accounts, attendance, common, configuration, inventory, memberships, schedules, store


class SupabaseGymRepository:
    def validate_admin_registration_schema(self) -> None:
        self._filter_remote_columns("CLIENTES", {"origen_registro": "ADMIN"})

    REFRESH_TTL_SECONDS = 5.0
    PAYMENT_COLUMNS = {
        "estado_pago",
        "fecha_pago",
        "metodo_pago",
        "monto_pago",
        "referencia_pago",
    }
    # Columnas que va a tener VENTA
    STORE_PAYMENT_COLUMNS = {"estado_pago", "referencia_pago"}
    CORE_TABLES = {
        "planes_membresia": ("PLANES_MEMBRESIA", "id_pm", "id_PM"),
        "promociones": ("PROMOCIONES", "id_promocion", "id_promocion"),
        "clientes": ("CLIENTES", "id_cliente", "id_cliente"),
        "membresia": ("MEMBRESIA", "id_membresia", "id_membresia"),
        "usuario": ("USUARIO", "id_usuario", "id_usuario"),
        "inventario": ("INVENTARIO", "id_item", "id_item"),
        "productos_tienda": ("TIENDA_PRODUCTOS", "id_producto", "id_producto"),
        "catalogo_rutina": ("CATALOGO_RUTINA", "id_rutina", "id_rutina"),
        "horario": ("HORARIO", "id_horario", "id_horario"),
        "horarios_servicio": ("HORARIOS_SERVICIO", "id_horario_servicio", "id_horario_servicio"),
        "matriculas_horario": ("MATRICULAS_HORARIO", "id_matricula", "id_matricula"),
        "rutina_progreso": ("RUTINA_PROGRESO", "id_progreso", "id_progreso"),
        "mov_inv": ("MOV_INV", "id_mov", "id_mov"),
        "tickets_atencion": ("TICKETS_ATENCION", "id_ticket", "id_ticket"),
        "asistencia": ("ASISTENCIA", "id_asistencia", "id_asistencia"),
    }
    SYNC_STATE_KEYS = tuple(CORE_TABLES.keys()) + ("pedidos_tienda",)
    READ_STATE_KEYS = SYNC_STATE_KEYS + ("configuracion_gimnasio",)
    # Estos pares se publican juntos: vigencia, stock y cupos usan ambas tablas.
    RELATED_READS = (
        frozenset(("clientes", "membresia")),
        frozenset(("inventario", "productos_tienda")),
        frozenset(("horarios_servicio", "matriculas_horario")),
    )

    # Inicializa la clase.
    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        self.supabase = SupabaseRestClient(supabase_url, supabase_key)
        self.lock = threading.Lock()
        self.remote_columns: dict[str, set[str]] = {}
        self._raw_rows = {}
        self.missing_remote_tables: set[str] = set()
        self.state = GymDomainService().state
        self._last_refresh_at = 0.0
        self._resource_refreshed_at: dict[str, float] = {}
        self._validate_payment_schema()
        self._validate_store_payment_schema()

    def _validate_payment_schema(self) -> None:
        try:
            self.supabase.validate_columns("MEMBRESIA", self.PAYMENT_COLUMNS)
        except RuntimeError as error:
            if missing_column(error):
                raise SchemaNotReady("001_add_membership_payment_fields.sql") from error
            raise

    @staticmethod
    def _is_missing_column_error(error: RuntimeError) -> bool:
        return missing_column(error)

    def _validate_store_payment_schema(self) -> None:
        """Falla al arrancar si falta la migración 009, en vez de perder datos en silencio."""
        try:
            self.supabase.validate_columns("VENTAS", self.STORE_PAYMENT_COLUMNS)
        except RuntimeError as error:
            if self._is_missing_column_error(error):
                raise SchemaNotReady("009_add_store_order_payment_fields.sql") from error
            raise
    # Procesa esta operación.
    def _remember_remote_columns(self, table: str, rows: list[dict[str, Any]]) -> None:
        if rows:
            self.remote_columns[table] = set(rows[0].keys())
        self.missing_remote_tables.discard(table)

    # Procesa esta operación.
    def _select_required(self, table: str, order: str | None = None) -> list[dict[str, Any]]:
        rows = self.supabase.select_all(table, order=order or "1")
        self._remember_remote_columns(table, rows)
        return rows

    # Procesa esta operación.
    def _select_optional(self, table: str, order: str | None = None) -> list[dict[str, Any]]:
        try:
            rows = self.supabase.select_all(table, order=order or "1")
            self._remember_remote_columns(table, rows)
            return rows
        except RuntimeError as error:
            if database_code(error) in {"PGRST205", "42P01"}:
                self.missing_remote_tables.add(table)
                return []
            raise

    # Procesa esta operación.
    def _filter_remote_columns(self, table: str, body: dict[str, Any]) -> dict[str, Any]:
        return prepare_write(table, body, self.remote_columns, lambda table, columns: self.supabase.validate_columns(table, columns))

    # Actualiza el registro correspondiente.
    def _read_resources(self, resources=None) -> set[str]:
        selected = set(self.READ_STATE_KEYS if resources is None else resources)
        if selected - set(self.READ_STATE_KEYS):
            raise ValueError("Recurso de lectura desconocido")
        if "pedidos_tienda" in selected:
            selected.update(("inventario", "productos_tienda"))
        for related in self.RELATED_READS:
            if selected & related:
                selected.update(related)
        return selected

    def _refresh_remote_state(self, resources=None) -> None:
        selected = self._read_resources(resources)
        # Una lectura parcial conserva las secciones cargadas anteriormente.
        remote_state = dict(self.state)

        # Las lecturas son independientes; el estado se sustituye solo cuando todas terminan.
        # Se conserva el bloqueo de refresh/mutaciones y un límite de conexiones a Supabase.
        queries = [
            ("planes_membresia", self._select_required, "PLANES_MEMBRESIA", "id_PM.asc"),
            ("clientes", self.supabase.select_all, "CLIENTES", "id_cliente.asc"),
            ("membresia", self.supabase.select_all, "MEMBRESIA", "id_membresia.asc"),
            ("usuario", self._select_required, "USUARIO", "id_usuario.asc"),
            ("inventario", self._select_required, "INVENTARIO", "id_item.asc"),
            ("mov_inv", self._select_optional, "MOV_INV", "id_mov.desc"),
            ("productos_tienda", self._select_required, "TIENDA_PRODUCTOS", "id_producto.asc"),
            ("pedidos_tienda", self._select_required, "VENTAS", "id_venta.desc"),
            ("sale_details", self._select_required, "DETALLE_VENTA", "id_detalle.asc"),
            ("catalogo_rutina", self._select_required, "CATALOGO_RUTINA", "id_rutina.asc"),
            ("horario", self._select_required, "HORARIO", "id_horario.asc"),
            ("horarios_servicio", self._select_optional, "HORARIOS_SERVICIO", "id_horario_servicio.asc"),
            ("promociones", self._select_optional, "PROMOCIONES", "id_promocion.desc"),
            ("matriculas_horario", self.supabase.select_all, "MATRICULAS_HORARIO", "id_matricula.asc"),
            ("rutina_progreso", self._select_optional, "RUTINA_PROGRESO", "fecha.desc"),
            ("tickets_atencion", self._select_optional, "TICKETS_ATENCION", "id_ticket.desc"),
            ("configuracion_gimnasio", self._select_optional, "CONFIGURACION_GIMNASIO", "id_config.asc"),
            ("asistencia", self.supabase.select_all, "ASISTENCIA", "id_asistencia.asc"),
        ]
        queries = [query for query in queries if query[0] in selected or
                   (query[0] == "sale_details" and "pedidos_tienda" in selected)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            pending = {key: pool.submit(load, table, order=order) for key, load, table, order in queries}
            rows = {key: future.result() for key, future in pending.items()}

        mappers = {
            "planes_membresia": self._map_plan, "clientes": self._map_client,
            "membresia": self._map_membership, "usuario": self._map_user,
            "inventario": self._map_inventory, "mov_inv": self._map_inventory_move,
            "productos_tienda": self._map_product, "catalogo_rutina": self._map_routine,
            "horario": self._map_schedule, "horarios_servicio": self._map_service_schedule,
            "promociones": self._map_promotion, "matriculas_horario": self._map_schedule_enrollment,
            "rutina_progreso": self._map_routine_progress, "tickets_atencion": self._map_ticket,
            "asistencia": self._map_attendance,
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
                details_by_sale.setdefault(sale_id, []).append(self._map_sale_detail(detail, product_names))
            remote_state["pedidos_tienda"] = [
                self._map_sale(row, details_by_sale.get(int(row.get("id_venta", 0) or 0), []))
                for row in rows["pedidos_tienda"]
            ]
        if "configuracion_gimnasio" in selected:
            config_rows = rows["configuracion_gimnasio"]
            remote_state["configuracion_gimnasio"] = self._map_config(config_rows[0] if config_rows else {})
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
        raw = dict(getattr(self, "_raw_rows", {}))
        for key, _load, table, _order in queries:
            raw[table] = deepcopy(rows[key])
            if table not in self.missing_remote_tables:
                self._remember_remote_columns(table, rows[key])
        self._raw_rows = raw
        self.state = remote_state
        refreshed_at = time.monotonic()
        if not hasattr(self, "_resource_refreshed_at"):
            self._resource_refreshed_at = {}
        self._resource_refreshed_at.update(dict.fromkeys(selected, refreshed_at))
        # El reloj global solo acredita una carga completa, nunca una lectura parcial.
        if selected == set(self.READ_STATE_KEYS):
            self._last_refresh_at = refreshed_at

    # Guarda en INVENTARIO.Estado los estados automáticos que difieren de Supabase (por ejemplo,
    # tras cambiar un stock mínimo o al arrancar). Si falla, la lectura sigue y se reintenta luego.
    def _guardar_estados_automaticos(self, rows: list[dict[str, Any]], state: dict[str, Any]) -> None:
        if "INVENTARIO" in self.missing_remote_tables:
            return
        remotos = {int(row.get("id_item", 0) or 0): str(row.get("Estado") or "") for row in rows}
        for item in state.get("inventario", []):
            id_item = int(item.get("id_item", 0) or 0)
            estado = str(item.get("estado") or "")
            if not self.rules.is_store_inventory(item) or id_item not in remotos or remotos[id_item] == estado:
                continue
            try:
                self.supabase.update("INVENTARIO", "id_item", id_item, {"Estado": estado})
            except RuntimeError:
                item["estado"] = remotos[id_item]

    # Actualiza el registro correspondiente.
    def _refresh_remote_state_if_stale(self, resources=None) -> None:
        if resources is None:
            if time.monotonic() - self._last_refresh_at >= self.REFRESH_TTL_SECONDS:
                self._refresh_remote_state()
            return
        selected = self._read_resources(resources)
        now = time.monotonic()
        timestamps = getattr(self, "_resource_refreshed_at", {})
        stale = {key for key in selected
                 if now - timestamps.get(key, 0.0) >= self.REFRESH_TTL_SECONDS}
        if stale:
            self._refresh_remote_state(stale)

    # Procesa esta operación.
    def refresh(self, resources=None) -> None:
        with self.lock:
            self._refresh_remote_state_if_stale(resources)

    # Procesa esta operación.
    def _mutation_snapshot(self, resources=None) -> dict[str, Any]:
        selected = self._read_resources(resources)
        return {key: deepcopy(self.state.get(key, [])) for key in self.SYNC_STATE_KEYS if key in selected}

    # Procesa esta operación.
    def _changed_state_keys(self, previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
        return [key for key in previous if previous[key] != current.get(key, [])]

    # Procesa esta operación.
    def _mutate(self, fn, resources=None):
        with self.lock:
            for attempt in range(3):
                self._refresh_remote_state_if_stale(resources)
                previous = self._mutation_snapshot(resources)
                try:
                    table_names = [self.CORE_TABLES[key][0] for key in previous if key in self.CORE_TABLES
                                   and self.CORE_TABLES[key][0] not in self.missing_remote_tables]
                    if "pedidos_tienda" in previous:
                        table_names.append("VENTAS")
                    floors = self.supabase.rpc("gym_identity_floors", {"p_tables": sorted(table_names)})
                    if not isinstance(floors, dict):
                        raise SchemaNotReady("015_atomic_gym_transactions.sql")
                    self.state["_identity_floors"] = {
                        key: int(floors.get(table, 0)) for key, (table, _local, _remote) in self.CORE_TABLES.items()
                    }
                    self.state["_identity_floors"]["pedidos_tienda"] = int(floors.get("VENTAS", 0))
                    result = fn(self.state)
                    changed_keys = self._changed_state_keys(previous, self.state)
                    if changed_keys:
                        self._sync_remote_changes(previous, self.state, changed_keys)
                except Exception as error:
                    self.state.update(deepcopy(previous))
                    self._last_refresh_at = 0.0
                    getattr(self, "_resource_refreshed_at", {}).clear()
                    if database_code(error) in {"PGRST202", "42883"}:
                        raise SchemaNotReady("015_atomic_gym_transactions.sql") from error
                    if isinstance(error, SnapshotConflict) and attempt < 2:
                        # La RPC no escribió nada. Recalcula las reglas sobre datos actuales.
                        self._refresh_remote_state(resources)
                        continue
                    if isinstance(error, SnapshotConflict):
                        raise ValueError("Los datos cambiaron. Actualiza e inténtalo de nuevo.") from error
                    raise
                changed_at = time.monotonic()
                getattr(self, "_resource_refreshed_at", {}).update(dict.fromkeys(changed_keys, changed_at))
                return result

    @staticmethod
    def _raise_schedule_enrollment_error(error: RuntimeError) -> NoReturn:
        raise_schedule_enrollment_error(error)

    def enroll(self, payload: dict[str, Any]) -> dict[str, Any]:

        """Crea la matrícula únicamente mediante la operación atómica de la base."""
        with self.lock:
            # Una matrícula siempre parte del estado remoto más reciente, incluso
            # si la caché general todavía no alcanzó su TTL.
            self._refresh_remote_state()
            if payload.get("dni"):
                cliente = self.rules.get_cliente_by_dni(str(payload.get("dni") or "").strip())
                if not cliente:
                    raise ValueError("Cliente no encontrado")
                id_cliente = int(cliente.get("id_cliente", 0) or 0)
            else:
                id_cliente = self.rules.parse_client_id(payload.get("id_cliente"))

            id_horario = int(payload.get("id_horario_servicio", 0) or 0)
            if id_cliente <= 0:
                raise ValueError("Cliente no encontrado")
            if id_horario <= 0:
                raise ValueError("Horario no disponible")

            self.rules.validate_enrollment(id_cliente, id_horario)

            admin_id = str(payload.get("_admin_id") or "")
            rpc_name = "matricular_cliente_horario_admin" if admin_id else "matricular_cliente_horario"
            rpc_body: dict[str, Any] = {"p_id_cliente": id_cliente, "p_id_horario_servicio": id_horario}
            if admin_id:
                rpc_body["p_admin_id"] = admin_id
            try:
                created = self.supabase.rpc(rpc_name, rpc_body)
            except RuntimeError as error:
                if database_code(error) in {"PGRST202", "42883"}:
                    if admin_id:
                        raise RuntimeError("Falta ejecutar backend/migrations/006_schedule_email_notifications.sql en Supabase.") from error
                    raise RuntimeError("Falta ejecutar backend/migrations/002_harden_schedule_enrollment.sql en Supabase.") from error
                else:
                    self._raise_schedule_enrollment_error(error)

            if isinstance(created, list):
                created = created[0] if created else None
            if not isinstance(created, dict):
                raise RuntimeError("Supabase no devolvió la matrícula creada")

            enrollment = self._map_schedule_enrollment(created)
            if int(enrollment.get("id_matricula", 0) or 0) <= 0:
                raise RuntimeError("Supabase devolvió una matrícula sin identificador")

            self.state.setdefault("matriculas_horario", [])
            self.state["matriculas_horario"] = [
                row
                for row in self.state["matriculas_horario"]
                if int(row.get("id_matricula", 0) or 0) != int(enrollment["id_matricula"])
            ]
            self.state["matriculas_horario"].insert(0, enrollment)
            self.rules.recount_schedule()
            # La siguiente petición recarga también las matrículas creadas por
            # cualquier otra instancia del backend.
            self._last_refresh_at = 0.0
            getattr(self, "_resource_refreshed_at", {}).clear()

            result = next(
                row
                for row in self.rules.matriculas_horario(id_cliente=id_cliente, solo_activas=True)
                if int(row.get("id_matricula", 0) or 0) == int(enrollment["id_matricula"])
            )
            if admin_id:
                result["_email_notification_queued"] = True
            return result

    # Procesa esta operación.
    def configuracion_gimnasio(self) -> dict[str, Any]:
        return dict(self.state.get("configuracion_gimnasio") or {})

    # Procesa esta operación.
    def save_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"id_config": 1, **self._config_to_remote(payload)}
        with self.lock:
            for attempt in range(3):
                rows = self._select_optional("CONFIGURACION_GIMNASIO", "id_config.asc")
                try:
                    committed = commit_snapshot(self.supabase, {"CONFIGURACION_GIMNASIO": rows},
                        table_changes("CONFIGURACION_GIMNASIO", "id_config", rows, [body]))
                except SnapshotConflict:
                    if attempt < 2:
                        continue
                    raise ValueError("La configuración cambió. Actualiza e inténtalo de nuevo.")
                self._raw_rows = {**getattr(self, "_raw_rows", {}), **committed}
                self.state["configuracion_gimnasio"] = self._map_config(body)
                getattr(self, "_resource_refreshed_at", {}).update(configuracion_gimnasio=time.monotonic())
                return self.configuracion_gimnasio()

    # Actualiza el registro correspondiente.
    def _sync_remote_changes(self, previous, current, changed_keys, *_legacy_tracking):
        if not changed_keys:
            return
        operations = []
        for key in changed_keys:
            if key not in self.CORE_TABLES:
                continue
            table, _local_pk, remote_pk = self.CORE_TABLES[key]
            if table in self.missing_remote_tables:
                raise RuntimeError(f"La tabla {table} no está disponible; no se guardó ningún cambio")
            before = [self._filter_remote_columns(table, self._to_remote_body(key, row))
                      for row in previous.get(key, [])]
            after = [self._filter_remote_columns(table, self._to_remote_body(key, row))
                     for row in current.get(key, [])]
            operations.extend(table_changes(table, remote_pk, before, after))
        if "pedidos_tienda" in changed_keys:
            before = {int(row["id_pedido"]): row for row in previous.get("pedidos_tienda", [])}
            after = {int(row["id_pedido"]): row for row in current.get("pedidos_tienda", [])}
            operations.extend(table_changes("VENTAS", "id_venta",
                [self._filter_remote_columns("VENTAS", self._sale_to_remote(row)) for row in before.values()],
                [self._filter_remote_columns("VENTAS", self._sale_to_remote(row)) for row in after.values()]))
            for identity in before.keys() | after.keys():
                old, new = before.get(identity), after.get(identity)
                if old is None or new is None or old.get("items") != new.get("items"):
                    operations.append({"table": "DETALLE_VENTA", "pk": "id_detalle", "action": "delete_details",
                                       "id": identity})
                    for item in (new or {}).get("items", []):
                        operations.append({"table": "DETALLE_VENTA", "pk": "id_detalle", "action": "insert",
                                           "body": self._sale_detail_to_remote(identity, item)})
        if not operations:
            return
        raw = getattr(self, "_raw_rows", {})
        tables = {self.CORE_TABLES[key][0] for key in previous if key in self.CORE_TABLES}
        if "pedidos_tienda" in previous:
            tables.update(("VENTAS", "DETALLE_VENTA"))
        if "clientes" in previous and "CONFIGURACION_GIMNASIO" in raw:
            tables.add("CONFIGURACION_GIMNASIO")
        tables.difference_update(self.missing_remote_tables)
        if tables - raw.keys():
            raise RuntimeError("No hay una instantánea remota completa para confirmar los cambios")
        expected = {table: raw[table] for table in sorted(tables)}
        committed = commit_snapshot(self.supabase, expected, operations)
        self._raw_rows.update(committed)

    # Procesa esta operación.
    def _to_remote_body(self, state_key: str, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "planes_membresia": self._plan_to_remote,
            "promociones": self._promotion_to_remote,
            "clientes": self._client_to_remote,
            "membresia": self._membership_to_remote,
            "usuario": self._user_to_remote,
            "inventario": self._inventory_to_remote,
            "mov_inv": self._inventory_move_to_remote,
            "productos_tienda": self._product_to_remote,
            "catalogo_rutina": self._routine_to_remote,
            "horario": self._schedule_to_remote,
            "horarios_servicio": self._service_schedule_to_remote,
            "matriculas_horario": self._schedule_enrollment_to_remote,
            "rutina_progreso": self._routine_progress_to_remote,
            "tickets_atencion": self._ticket_to_remote,
            "asistencia": self._attendance_to_remote,
        }[state_key](row)

    # Compatibilidad con consumidores antiguos; los mapeos son funciones puras.
    _pk = staticmethod(common._pk)
    _remote_pk_value = staticmethod(common._remote_pk_value)
    _remote_user_id = staticmethod(common._remote_user_id)
    _remote_user_id_or_none = staticmethod(common._remote_user_id_or_none)
    _split_name = staticmethod(common._split_name)
    _phone_number = staticmethod(common._phone_number)
    _status_to_bool = staticmethod(common._status_to_bool)
    _bool_to_status = staticmethod(common._bool_to_status)
    _date_or_today = staticmethod(common._date_or_today)
    _date_or_none = staticmethod(common._date_or_none)
    _map_config = staticmethod(configuration._map_config)
    _config_to_remote = staticmethod(configuration._config_to_remote)
    _map_plan = staticmethod(memberships._map_plan)
    _plan_to_remote = staticmethod(memberships._plan_to_remote)
    _map_promotion = staticmethod(memberships._map_promotion)
    _promotion_to_remote = staticmethod(memberships._promotion_to_remote)
    _map_membership = staticmethod(memberships._map_membership)
    _membership_to_remote = staticmethod(memberships._membership_to_remote)
    _map_client = staticmethod(accounts._map_client)
    _client_to_remote = staticmethod(accounts._client_to_remote)
    _map_user = staticmethod(accounts._map_user)
    _map_user_legacy = staticmethod(accounts._map_user_legacy)
    _user_to_remote = staticmethod(accounts._user_to_remote)
    _map_inventory = staticmethod(inventory._map_inventory)
    _inventory_to_remote = staticmethod(inventory._inventory_to_remote)
    _map_inventory_move = staticmethod(inventory._map_inventory_move)
    _inventory_move_to_remote = staticmethod(inventory._inventory_move_to_remote)
    _map_product = staticmethod(inventory._map_product)
    _product_to_remote = staticmethod(inventory._product_to_remote)
    _map_sale_detail = staticmethod(store._map_sale_detail)
    _map_sale = staticmethod(store._map_sale)
    _sale_to_remote = staticmethod(store._sale_to_remote)
    _sale_detail_to_remote = staticmethod(store._sale_detail_to_remote)
    _map_routine = staticmethod(schedules._map_routine)
    _routine_to_remote = staticmethod(schedules._routine_to_remote)
    _map_schedule = staticmethod(schedules._map_schedule)
    _schedule_to_remote = staticmethod(schedules._schedule_to_remote)
    _map_service_schedule = staticmethod(schedules._map_service_schedule)
    _service_schedule_to_remote = staticmethod(schedules._service_schedule_to_remote)
    _map_schedule_enrollment = staticmethod(schedules._map_schedule_enrollment)
    _schedule_enrollment_to_remote = staticmethod(schedules._schedule_enrollment_to_remote)
    _map_routine_progress = staticmethod(schedules._map_routine_progress)
    _routine_progress_to_remote = staticmethod(schedules._routine_progress_to_remote)
    _map_ticket = staticmethod(schedules._map_ticket)
    _ticket_to_remote = staticmethod(schedules._ticket_to_remote)
    _map_attendance = staticmethod(attendance._map_attendance)
    _attendance_to_remote = staticmethod(attendance._attendance_to_remote)

    def save_attendance(self, row, expected_version, audit):

        with self.lock:
            try:
                saved = self.supabase.rpc("guardar_asistencia", {
                    "p_registro": self._attendance_to_remote(row),
                    "p_version": expected_version, "p_evento": audit,
                })
            except RuntimeError as error:
                if database_code(error) == "P0001":
                    message = error_payload(error).get("message") or "El registro cambió. Actualiza la asistencia e inténtalo de nuevo."
                    raise AttendanceConflict(message) from error
                raise
            mapped = self._map_attendance(saved)
            rows = self.state.setdefault("asistencia", [])
            index = next((i for i, r in enumerate(rows) if r["id_asistencia"] == mapped["id_asistencia"]), None)
            if index is None:
                rows.insert(0, mapped)
            else:
                rows[index] = mapped
            return deepcopy(mapped)


    @property
    def rules(self):
        return GymDomainService(getattr(self, "state", None))

    def read(self, operation, resources=None):
        with self.lock:
            return operation(deepcopy(self.state if resources is None else {key: self.state[key] for key in resources if key in self.state}))

    def change(self, operation, resources=None):
        return self._mutate(operation, resources)

