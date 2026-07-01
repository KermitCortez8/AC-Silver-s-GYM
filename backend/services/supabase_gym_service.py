from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
import re
import threading
import time
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from services.gym_domain_service import GymDomainService, _now_iso, _today_iso


class SupabaseRestClient:
    def __init__(self, url: str, key: str) -> None:
        self.rest_url = f"{url.rstrip('/')}/rest/v1"
        self.key = key

    def _request(
        self,
        method: str,
        table: str,
        query: dict[str, Any] | None = None,
        body: Any | None = None,
        return_representation: bool = False,
    ) -> Any:
        encoded_table = quote(table, safe="")
        query_string = urlencode(query or {}, doseq=True, safe="*,().:")
        url = f"{self.rest_url}/{encoded_table}"
        if query_string:
            url = f"{url}?{query_string}"

        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": "return=representation" if return_representation else "return=minimal",
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase {method} {table} fallo ({error.code}): {details}") from error

        if not raw:
            return []
        return json.loads(raw)

    def select(self, table: str, order: str | None = None) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"select": "*"}
        if order:
            query["order"] = order
        rows = self._request("GET", table, query=query, return_representation=True)
        return rows if isinstance(rows, list) else []

    def insert(self, table: str, body: dict[str, Any] | list[dict[str, Any]]) -> None:
        self._request("POST", table, body=body)

    def update(self, table: str, pk_column: str, pk_value: Any, body: dict[str, Any]) -> None:
        self._request("PATCH", table, query={pk_column: f"eq.{pk_value}"}, body=body)

    def delete(self, table: str, pk_column: str, pk_value: Any) -> None:
        self._request("DELETE", table, query={pk_column: f"eq.{pk_value}"})

    def delete_where(self, table: str, column: str, value: Any) -> None:
        self._request("DELETE", table, query={column: f"eq.{value}"})


class SupabaseGymService(GymDomainService):
    REFRESH_TTL_SECONDS = 5.0

    CORE_TABLES = {
        "planes_membresia": ("PLANES_MEMBRESIA", "id_pm", "id_PM"),
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

    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        self.supabase = SupabaseRestClient(supabase_url, supabase_key)
        self.lock = threading.Lock()
        self.state = self._seed()
        self._last_refresh_at = 0.0
        self._refresh_remote_state()

    def _select_optional(self, table: str, order: str | None = None) -> list[dict[str, Any]]:
        try:
            return self.supabase.select(table, order=order)
        except RuntimeError as error:
            message = str(error)
            if "PGRST" in message or "does not exist" in message or "Could not find" in message:
                return []
            raise

    def _refresh_remote_state(self) -> None:
        remote_state = self._seed()

        plans = self.supabase.select("PLANES_MEMBRESIA", order="id_PM.asc")
        clients = self.supabase.select("CLIENTES", order="id_cliente.desc")
        memberships = self.supabase.select("MEMBRESIA", order="id_membresia.desc")
        users = self.supabase.select("USUARIO", order="id_usuario.asc")
        inventory = self.supabase.select("INVENTARIO", order="id_item.asc")
        inventory_moves = self._select_optional("MOV_INV", order="id_mov.desc")
        products = self.supabase.select("TIENDA_PRODUCTOS", order="id_producto.asc")
        sales = self.supabase.select("VENTAS", order="id_venta.desc")
        sale_details = self.supabase.select("DETALLE_VENTA", order="id_detalle.asc")
        routines = self.supabase.select("CATALOGO_RUTINA", order="id_rutina.asc")
        schedules = self.supabase.select("HORARIO", order="id_horario.asc")
        service_schedules = self._select_optional("HORARIOS_SERVICIO", order="id_horario_servicio.asc")
        enrollments = self._select_optional("MATRICULAS_HORARIO", order="id_matricula.desc")
        routine_progress = self._select_optional("RUTINA_PROGRESO", order="fecha.desc")
        tickets = self._select_optional("TICKETS_ATENCION", order="id_ticket.desc")
        config_rows = self._select_optional("CONFIGURACION_GIMNASIO", order="id_config.asc")
        attendance = self.supabase.select("ASISTENCIA", order="Fecha.desc")

        product_names = {
            int(row.get("id_producto", 0) or 0): str(row.get("nombre_Producto") or "")
            for row in products
        }
        details_by_sale: dict[int, list[dict[str, Any]]] = {}
        for detail in sale_details:
            sale_id = int(detail.get("id_venta", 0) or 0)
            details_by_sale.setdefault(sale_id, []).append(self._map_sale_detail(detail, product_names))

        remote_state["planes_membresia"] = [self._map_plan(row) for row in plans]
        remote_state["clientes"] = [self._map_client(row) for row in clients]
        remote_state["membresia"] = [self._map_membership(row) for row in memberships]
        remote_state["usuario"] = [self._map_user(row) for row in users]
        remote_state["inventario"] = [self._map_inventory(row) for row in inventory]
        remote_state["mov_inv"] = [self._map_inventory_move(row) for row in inventory_moves]
        remote_state["productos_tienda"] = [self._map_product(row) for row in products]
        remote_state["pedidos_tienda"] = [self._map_sale(row, details_by_sale.get(int(row.get("id_venta", 0) or 0), [])) for row in sales]
        remote_state["catalogo_rutina"] = [self._map_routine(row) for row in routines]
        remote_state["horario"] = [self._map_schedule(row) for row in schedules]
        remote_state["horarios_servicio"] = [self._map_service_schedule(row) for row in service_schedules]
        remote_state["matriculas_horario"] = [self._map_schedule_enrollment(row) for row in enrollments]
        remote_state["rutina_progreso"] = [self._map_routine_progress(row) for row in routine_progress]
        remote_state["tickets_atencion"] = [self._map_ticket(row) for row in tickets]
        remote_state["configuracion_gimnasio"] = self._map_config(config_rows[0] if config_rows else {})
        remote_state["asistencia"] = [self._map_attendance(row) for row in attendance]
        self._recount_schedule_cupos(remote_state)
        self.state = remote_state
        self._last_refresh_at = time.monotonic()

    def _refresh_remote_state_if_stale(self) -> None:
        if time.monotonic() - self._last_refresh_at >= self.REFRESH_TTL_SECONDS:
            self._refresh_remote_state()

    def ensure_fresh(self) -> None:
        with self.lock:
            self._refresh_remote_state_if_stale()

    def _mutation_snapshot(self) -> dict[str, Any]:
        return {key: deepcopy(self.state.get(key, [])) for key in self.SYNC_STATE_KEYS}

    def _changed_state_keys(self, previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
        return [key for key in self.SYNC_STATE_KEYS if previous.get(key, []) != current.get(key, [])]

    def _mutate(self, fn):
        with self.lock:
            self._refresh_remote_state_if_stale()
            previous = self._mutation_snapshot()
            result = fn(self.state)
            changed_keys = self._changed_state_keys(previous, self.state)
            self._sync_remote_changes(previous, self.state, changed_keys)
            self._last_refresh_at = time.monotonic()
            return result

    def _save(self) -> None:
        return None

    def configuracion_gimnasio(self) -> dict[str, Any]:
        return dict(self.state.get("configuracion_gimnasio") or {})

    def actualizar_configuracion_gimnasio(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = self._config_to_remote(payload)
        with self.lock:
            rows = self._select_optional("CONFIGURACION_GIMNASIO")
            if rows:
                self.supabase.update("CONFIGURACION_GIMNASIO", "id_config", 1, body)
            else:
                self.supabase.insert("CONFIGURACION_GIMNASIO", {"id_config": 1, **body})
            self.state["configuracion_gimnasio"] = self._map_config(body)
            self._last_refresh_at = time.monotonic()
            return self.configuracion_gimnasio()

    def _sync_remote_changes(self, previous: dict[str, Any], current: dict[str, Any], changed_keys: list[str]) -> None:
        if not changed_keys:
            return

        for state_key in [key for key in changed_keys if key in self.CORE_TABLES]:
            self._sync_table(state_key, previous.get(state_key, []), current.get(state_key, []))

        if "pedidos_tienda" in changed_keys:
            self._sync_orders(previous.get("pedidos_tienda", []), current.get("pedidos_tienda", []))

    def _sync_table(self, state_key: str, previous_rows: list[dict[str, Any]], current_rows: list[dict[str, Any]]) -> None:
        table, local_pk, remote_pk = self.CORE_TABLES[state_key]
        previous_by_id = {self._pk(row, local_pk): row for row in previous_rows if self._pk(row, local_pk)}
        current_by_id = {self._pk(row, local_pk): row for row in current_rows if self._pk(row, local_pk)}

        for deleted_id in previous_by_id.keys() - current_by_id.keys():
            self.supabase.delete(table, remote_pk, self._remote_pk_value(state_key, previous_by_id[deleted_id], deleted_id))

        for row_id, row in current_by_id.items():
            body = self._to_remote_body(state_key, row)
            previous = previous_by_id.get(row_id)
            if previous and body == self._to_remote_body(state_key, previous):
                continue
            remote_id = self._remote_pk_value(state_key, row, row_id)
            if previous:
                self.supabase.update(table, remote_pk, remote_id, body)
            else:
                self.supabase.insert(table, body)

    def _sync_orders(self, previous_rows: list[dict[str, Any]], current_rows: list[dict[str, Any]]) -> None:
        previous_by_id = {int(row.get("id_pedido", 0) or 0): row for row in previous_rows if int(row.get("id_pedido", 0) or 0)}
        current_by_id = {int(row.get("id_pedido", 0) or 0): row for row in current_rows if int(row.get("id_pedido", 0) or 0)}

        for deleted_id in previous_by_id.keys() - current_by_id.keys():
            self.supabase.delete("VENTAS", "id_venta", deleted_id)

        for sale_id, row in current_by_id.items():
            previous = previous_by_id.get(sale_id)
            if previous and row == previous:
                continue

            sale_body = self._sale_to_remote(row)
            if previous:
                self.supabase.update("VENTAS", "id_venta", sale_id, sale_body)
            else:
                self.supabase.insert("VENTAS", sale_body)

            self.supabase.delete_where("DETALLE_VENTA", "id_venta", sale_id)
            detail_rows = [self._sale_detail_to_remote(sale_id, item) for item in row.get("items", [])]
            if detail_rows:
                self.supabase.insert("DETALLE_VENTA", detail_rows)

    def _to_remote_body(self, state_key: str, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "planes_membresia": self._plan_to_remote,
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

    def _pk(self, row: dict[str, Any], key: str) -> int:
        if key == "id_usuario":
            return self._remote_user_id(row.get(key))
        return int(row.get(key, 0) or 0)

    def _remote_pk_value(self, state_key: str, row: dict[str, Any], fallback: int) -> int:
        if state_key == "usuario":
            return self._remote_user_id(row.get("id_usuario")) or int(fallback)
        return int(fallback)

    def _remote_user_id(self, value: Any) -> int:
        raw = str(value or "").strip()
        if raw.isdigit():
            return int(raw)
        match = re.search(r"(\d+)$", raw)
        return int(match.group(1)) if match else 0

    def _remote_user_id_or_none(self, value: Any) -> int | None:
        user_id = self._remote_user_id(value)
        return user_id or None

    def _split_name(self, value: str) -> tuple[str, str]:
        parts = [part for part in str(value or "").strip().split() if part]
        if len(parts) <= 1:
            return (parts[0] if parts else "", "")
        return (" ".join(parts[:-1]), parts[-1])

    def _phone_number(self, value: Any) -> int | None:
        digits = re.sub(r"\D+", "", str(value or ""))
        return int(digits) if digits else None

    def _status_to_bool(self, value: Any) -> bool:
        status = str(value or "").strip().upper()
        return status in {"ACTIVO", "ACTIVA", "TRUE", "1", "SI", "SÍ"}

    def _bool_to_status(self, value: Any) -> str:
        return "ACTIVO" if bool(value) else "PENDIENTE_PAGO"

    def _date_or_today(self, value: Any) -> str:
        text = str(value or "").strip()
        return text[:10] if text else _today_iso()

    def _date_or_none(self, value: Any) -> str | None:
        text = str(value or "").strip()
        return text[:10] if text else None

    def _map_config(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "capacidad_total": max(1, int(row.get("capacidad_total") or 30)),
            "capacidad_por_hora": max(1, int(row.get("capacidad_por_hora") or 10)),
        }

    def _config_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "capacidad_total": max(1, int(row.get("capacidad_total") or 30)),
            "capacidad_por_hora": max(1, int(row.get("capacidad_por_hora") or 10)),
        }

    def _map_plan(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_pm": int(row.get("id_PM", 0) or 0),
            "nombre_plan": str(row.get("Nombre_Plan") or "MENSUAL").strip().upper(),
            "duracion": str(row.get("Duración") or "30 dias"),
            "precio": float(row.get("Precio") or 0),
            "activo": bool(row.get("Activo", True)),
        }

    def _plan_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_PM": int(row.get("id_pm", 0) or 0),
            "Nombre_Plan": str(row.get("nombre_plan") or "MENSUAL").strip().upper(),
            "Duración": str(row.get("duracion") or "30 dias"),
            "Precio": float(row.get("precio") or 0),
            "Activo": bool(row.get("activo", True)),
        }

    def _map_client(self, row: dict[str, Any]) -> dict[str, Any]:
        client_id = int(row.get("id_cliente", 0) or 0)
        name = " ".join([str(row.get("Nombres") or "").strip(), str(row.get("Apellidos") or "").strip()]).strip()
        return {
            "id_cliente": client_id,
            "id_usuario": f"SGCLI{client_id:03d}",
            "nombre": name,
            "correo": str(row.get("Correo") or row.get("Email") or ""),
            "telefono": str(row.get("Telefono") or ""),
            "dni": str(row.get("DNI") or ""),
            "plan": str(row.get("Plan") or "MENSUAL").strip().upper(),
            "promocion": "SIN PROMOCION",
            "estado": self._bool_to_status(row.get("Estado")),
            "password_hash": str(row.get("password_hash") or row.get("Password_Hash") or ""),
            "fecha_registro": str(row.get("Fecha_Registro") or ""),
        }

    def _client_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        nombres, apellidos = self._split_name(str(row.get("nombre") or ""))
        correo = str(row.get("correo") or row.get("email") or "").strip()
        return {
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "Nombres": nombres,
            "Apellidos": apellidos,
            "DNI": str(row.get("dni") or ""),
            "Telefono": self._phone_number(row.get("telefono")),
            "Email": correo,
            "Correo": correo,
            "Fecha_Registro": self._date_or_today(row.get("fecha_registro")),
            "Estado": self._status_to_bool(row.get("estado")),
            "Plan": str(row.get("plan") or "MENSUAL").strip().upper(),
            "password_hash": str(row.get("password_hash") or ""),
        }

    def _map_membership(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_membresia": int(row.get("id_membresia", 0) or 0),
            "fecha_inicio": str(row.get("Fecha_Inicio") or ""),
            "fecha_fin": str(row.get("Fecha_Fin") or ""),
            "estado": str(row.get("Estado") or "PENDIENTE_PAGO"),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_pm": int(row.get("id_PM", 0) or 0),
        }

    def _membership_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_membresia": int(row.get("id_membresia", 0) or 0),
            "Fecha_Inicio": self._date_or_today(row.get("fecha_inicio")),
            "Fecha_Fin": self._date_or_today(row.get("fecha_fin")),
            "Estado": str(row.get("estado") or "PENDIENTE_PAGO"),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_PM": int(row.get("id_pm", 0) or 0) or None,
        }

    def _map_user_legacy(self, row: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
        password = str(row.get("Contraseña") or local.get("password_hash") or "")
        return {
            "id_usuario": int(row.get("id_usuario", 0) or 0),
            "nombre": str(local.get("nombre") or f"Usuario {row.get('id_usuario', '')}"),
            "correo": str(local.get("correo") or ""),
            "telefono": str(local.get("telefono") or ""),
            "dni": str(row.get("DNI") or local.get("dni") or ""),
            "rol": str(row.get("Rol") or local.get("rol") or "staff").strip().lower(),
            "estado": "ACTIVO" if bool(row.get("Estado", True)) else "INACTIVO",
            "password_hash": password,
        }

    def _map_user(self, row: dict[str, Any]) -> dict[str, Any]:
        user_id = int(row.get("id_usuario", 0) or 0)
        role = str(row.get("Rol") or "staff").strip().lower()
        prefix = self._user_role_prefix(role)
        return {
            "id_usuario": f"SG{prefix}{user_id:03d}" if user_id else "",
            "nombre": str(row.get("Nombre") or f"Usuario {row.get('id_usuario', '')}"),
            "correo": str(row.get("Correo") or row.get("Email") or ""),
            "telefono": str(row.get("Telefono") or ""),
            "dni": str(row.get("DNI") or ""),
            "rol": role,
            "estado": "ACTIVO" if bool(row.get("Estado", True)) else "INACTIVO",
            "password_hash": str(row.get("Contraseña") or row.get("ContraseÃ±a") or ""),
        }

    def _user_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_usuario": self._remote_user_id(row.get("id_usuario")),
            "Nombre": str(row.get("nombre") or ""),
            "Correo": str(row.get("correo") or row.get("email") or ""),
            "Telefono": str(row.get("telefono") or ""),
            "DNI": str(row.get("dni") or ""),
            "Contraseña": str(row.get("password_hash") or ""),
            "Rol": str(row.get("rol") or "staff").strip().lower(),
            "Estado": self._status_to_bool(row.get("estado") or "ACTIVO"),
        }

    def _map_inventory(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_item": int(row.get("id_item", 0) or 0),
            "nombre_item": str(row.get("Nombre_item") or ""),
            "tipo": str(row.get("Tipo") or "General"),
            "cantidad_stock": int(row.get("Cantidad_Stock_E", 0) or 0),
            "estado": str(row.get("Estado") or "Operativo"),
            "n_activo": row.get("N_ACTIVO"),
            "unidad_venta": "unidad",
            "precio_venta": 0,
            "stock_minimo": 1,
            "ubicacion": "Almacen",
            "observaciones": "",
        }

    def _inventory_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_item": int(row.get("id_item", 0) or 0),
            "Nombre_item": str(row.get("nombre_item") or ""),
            "Tipo": str(row.get("tipo") or "General"),
            "Cantidad_Stock_E": int(row.get("cantidad_stock", 0) or 0),
            "Estado": str(row.get("estado") or "Operativo"),
            "N_ACTIVO": int(row.get("n_activo")) if row.get("n_activo") else None,
        }

    def _map_inventory_move(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_mov": int(row.get("id_mov", 0) or 0),
            "id_item": int(row.get("id_item", 0) or 0),
            "id_usuario": int(row.get("id_usuario", 0) or 0) if row.get("id_usuario") else None,
            "tipo_movimiento": str(row.get("tipo_movimiento") or "entrada"),
            "fecha_movimiento": str(row.get("fecha_movimiento") or ""),
            "descripcion": str(row.get("descripcion") or ""),
            "cantidad": int(row.get("cantidad", 1) or 1),
        }

    def _inventory_move_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_mov": int(row.get("id_mov", 0) or 0),
            "id_item": int(row.get("id_item", 0) or 0),
            "id_usuario": self._remote_user_id_or_none(row.get("id_usuario")),
            "tipo_movimiento": str(row.get("tipo_movimiento") or "entrada").strip().lower(),
            "fecha_movimiento": self._date_or_today(row.get("fecha_movimiento")),
            "descripcion": str(row.get("descripcion") or ""),
            "cantidad": max(1, int(row.get("cantidad", 1) or 1)),
        }

    def _map_product(self, row: dict[str, Any]) -> dict[str, Any]:
        stock = int(row.get("cantidad_stock", 0) or 0)
        return {
            "id_producto": int(row.get("id_producto", 0) or 0),
            "id_item": None,
            "nombre_producto": str(row.get("nombre_Producto") or ""),
            "descripcion": "",
            "categoria": str(row.get("categoria") or "General"),
            "unidad_venta": "unidad",
            "precio_venta": float(row.get("precio_Venta") or 0),
            "cantidad_stock": stock,
            "stock_minimo": int(row.get("stock_minimo", 5) or 5),
            "estado": "Disponible" if stock > 0 else "Sin stock",
        }

    def _product_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_producto": int(row.get("id_producto", 0) or 0),
            "nombre_Producto": str(row.get("nombre_producto") or ""),
            "categoria": str(row.get("categoria") or "General"),
            "precio_Venta": float(row.get("precio_venta") or 0),
            "cantidad_stock": int(row.get("cantidad_stock", 0) or 0),
            "stock_minimo": int(row.get("stock_minimo", 5) or 5),
        }

    def _map_sale_detail(self, row: dict[str, Any], product_names: dict[int, str]) -> dict[str, Any]:
        product_id = int(row.get("id_producto", 0) or 0)
        return {
            "id_producto": product_id,
            "nombre_producto": product_names.get(product_id, ""),
            "cantidad": int(row.get("Cantidad", 1) or 1),
            "precio_unitario": float(row.get("Precio_Unitario") or 0),
            "subtotal": float(row.get("Subtotal") or 0),
        }

    def _map_sale(self, row: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
        total = float(row.get("total_Venta") or 0)
        return {
            "id_pedido": int(row.get("id_venta", 0) or 0),
            "id_cliente": None,
            "cliente_nombre": "Cliente",
            "cliente_correo": "",
            "cliente_dni": "",
            "fecha_pedido": str(row.get("Fecha_Venta") or _now_iso()),
            "metodo_pago": str(row.get("metodo_Pago") or ""),
            "referencia_pago": "",
            "estado_pago": "PAGADO",
            "estado_pedido": "COMPLETADO",
            "subtotal": total,
            "igv": 0,
            "total": total,
            "items": items,
        }

    def _sale_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_venta": int(row.get("id_pedido", 0) or 0),
            "Fecha_Venta": self._date_or_today(row.get("fecha_pedido")),
            "total_Venta": float(row.get("total") or row.get("subtotal") or 0),
            "metodo_Pago": str(row.get("metodo_pago") or "tarjeta"),
        }

    def _sale_detail_to_remote(self, sale_id: int, row: dict[str, Any]) -> dict[str, Any]:
        quantity = int(row.get("cantidad", 1) or 1)
        price = float(row.get("precio_unitario") or row.get("precio") or 0)
        return {
            "id_venta": int(sale_id),
            "id_producto": int(row.get("id_producto", 0) or 0),
            "Cantidad": quantity,
            "Precio_Unitario": price,
            "Subtotal": float(row.get("subtotal") or price * quantity),
        }

    def _map_routine(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_rutina": int(row.get("id_rutina", 0) or 0),
            "servicio": str(row.get("servicio") or "fitness").strip().lower(),
            "nombre_rutina": str(row.get("Nombre_rutina") or ""),
            "zonas_musculares": str(row.get("Zonas_musculares") or ""),
            "color": str(row.get("Color") or "Azul"),
        }

    def _routine_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_rutina": int(row.get("id_rutina", 0) or 0),
            "servicio": str(row.get("servicio") or "fitness").strip().lower(),
            "Nombre_rutina": str(row.get("nombre_rutina") or ""),
            "Zonas_musculares": str(row.get("zonas_musculares") or ""),
            "Color": str(row.get("color") or "Azul"),
        }

    def _map_schedule(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_horario": int(row.get("id_horario", 0) or 0),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_rutina": int(row.get("id_rutina", 0) or 0),
            "dia_semana": str(row.get("Dia_semana") or "Lunes"),
            "hora_inicio": str(row.get("Hora_inicio") or "06:00"),
            "hora_fin": str(row.get("Hora_fin") or "07:00"),
            "capacidad_maxima": 1,
            "cupos_usados": 1,
        }

    def _schedule_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_horario": int(row.get("id_horario", 0) or 0),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_rutina": int(row.get("id_rutina", 0) or 0),
            "Dia_semana": str(row.get("dia_semana") or "Lunes"),
            "Hora_inicio": str(row.get("hora_inicio") or "06:00"),
            "Hora_fin": str(row.get("hora_fin") or "07:00"),
        }

    def _map_service_schedule(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
            "servicio": str(row.get("servicio") or "fitness"),
            "id_rutina": int(row.get("id_rutina", 0) or 0),
            "codigo_dia": str(row.get("codigo_dia") or "LUN"),
            "dia": str(row.get("dia") or "lunes"),
            "hora_inicio": str(row.get("hora_inicio") or "06:00"),
            "hora_fin": str(row.get("hora_fin") or "07:00"),
            "cupos": max(1, int(row.get("cupos", 10) or 10)),
            "cupos_usados": 0,
            "activo": bool(row.get("activo", True)),
        }

    def _service_schedule_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
            "servicio": str(row.get("servicio") or "fitness").strip().lower(),
            "id_rutina": int(row.get("id_rutina", 0) or 0) or None,
            "codigo_dia": str(row.get("codigo_dia") or self._day_code(row.get("dia"))).strip().upper(),
            "dia": self._normalize_day(row.get("dia")) or "lunes",
            "hora_inicio": str(row.get("hora_inicio") or "06:00"),
            "hora_fin": str(row.get("hora_fin") or "07:00"),
            "cupos": max(1, int(row.get("cupos", 10) or 10)),
            "activo": bool(row.get("activo", True)),
        }

    def _map_schedule_enrollment(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_matricula": int(row.get("id_matricula", 0) or 0),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
            "id_rutina": int(row.get("id_rutina", 0) or 0) or None,
            "fecha_matricula": str(row.get("fecha_matricula") or ""),
            "estado": str(row.get("estado") or "ACTIVA").strip().upper(),
        }

    def _schedule_enrollment_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_matricula": int(row.get("id_matricula", 0) or 0),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
            "id_rutina": int(row.get("id_rutina", 0) or 0) or None,
            "fecha_matricula": self._date_or_today(row.get("fecha_matricula")),
            "estado": str(row.get("estado") or "ACTIVA").strip().upper(),
        }

    def _map_routine_progress(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_progreso": int(row.get("id_progreso", 0) or 0),
            "id_matricula": int(row.get("id_matricula", 0) or 0),
            "id_rutina": int(row.get("id_rutina", 0) or 0),
            "fecha": str(row.get("fecha") or ""),
            "estado": str(row.get("estado") or "REALIZADO").strip().upper(),
            "observacion": str(row.get("observacion") or ""),
            "id_usuario": row.get("id_usuario"),
        }

    def _routine_progress_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_progreso": int(row.get("id_progreso", 0) or 0),
            "id_matricula": int(row.get("id_matricula", 0) or 0),
            "id_rutina": int(row.get("id_rutina", 0) or 0),
            "fecha": self._date_or_today(row.get("fecha")),
            "estado": str(row.get("estado") or "REALIZADO").strip().upper(),
            "observacion": str(row.get("observacion") or ""),
            "id_usuario": self._remote_user_id_or_none(row.get("id_usuario")),
        }

    def _map_ticket(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_ticket": int(row.get("id_ticket", 0) or 0),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_usuario": int(row.get("id_usuario", 0) or 0) if row.get("id_usuario") else None,
            "tipo_ticket": str(row.get("tipo_ticket") or ""),
            "descripcion": str(row.get("descripcion") or ""),
            "estado_ticket": str(row.get("estado_ticket") or "Abierto"),
            "fecha_emitido": str(row.get("fecha_emitido") or ""),
            "fecha_cierre": str(row.get("fecha_cierre") or ""),
        }

    def _ticket_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_ticket": int(row.get("id_ticket", 0) or 0),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_usuario": self._remote_user_id_or_none(row.get("id_usuario")),
            "tipo_ticket": str(row.get("tipo_ticket") or ""),
            "descripcion": str(row.get("descripcion") or ""),
            "estado_ticket": str(row.get("estado_ticket") or "Abierto"),
            "fecha_emitido": self._date_or_today(row.get("fecha_emitido")),
            "fecha_cierre": self._date_or_none(row.get("fecha_cierre")),
        }

    def _map_attendance(self, row: dict[str, Any]) -> dict[str, Any]:
        client_id = int(row.get("id_cliente", 0) or 0)
        hour = str(row.get("Hora") or row.get("hora_entrada") or "")
        return {
            "id_asistencia": int(row.get("id_asistencia", 0) or 0),
            "id_cliente": f"SGCLI{client_id:03d}",
            "id_cliente_num": client_id,
            "fecha": str(row.get("Fecha") or ""),
            "hora": hour,
            "hora_entrada": str(row.get("hora_entrada") or hour),
            "hora_salida": str(row.get("hora_salida") or ""),
            "servicio": str(row.get("servicio") or "fitness"),
            "id_usuario_registra": row.get("id_usuario_registra"),
            "id_membresia": row.get("id_membresia"),
            "id_matricula": row.get("id_matricula"),
            "id_horario_servicio": row.get("id_horario_servicio"),
            "validacion": bool(row.get("Validación", True)),
        }

    def _attendance_to_remote(self, row: dict[str, Any]) -> dict[str, Any]:
        hour = str(row.get("hora") or row.get("hora_entrada") or "00:00")
        return {
            "id_asistencia": int(row.get("id_asistencia", 0) or 0),
            "id_cliente": int(row.get("id_cliente_num") or self._parse_cliente_id(row.get("id_cliente"))),
            "id_membresia": int(row.get("id_membresia")) if row.get("id_membresia") else None,
            "Fecha": self._date_or_today(row.get("fecha")),
            "Hora": hour,
            "Validación": bool(row.get("validacion", True)),
            "servicio": str(row.get("servicio") or "fitness").strip().lower(),
            "id_usuario_registra": self._remote_user_id_or_none(row.get("id_usuario_registra")),
            "id_matricula": int(row.get("id_matricula")) if row.get("id_matricula") else None,
            "id_horario_servicio": int(row.get("id_horario_servicio")) if row.get("id_horario_servicio") else None,
            "hora_entrada": str(row.get("hora_entrada") or hour),
            "hora_salida": str(row.get("hora_salida") or ""),
        }
