"""Agregado del gimnasio: reglas por módulo, sin acceso a persistencia."""
from __future__ import annotations

from typing import Any
from domain.services.membership_lifecycle import apply_membership_expiration, normalize_membership_status
from domain.ports import PasswordHasher
from domain.services.gym_values import (
    _LIMA,
    TIPO_TIENDA,
    ESTADO_DESCONTINUADO,
    ESTADO_DISPONIBLE,
    ESTADO_STOCK_BAJO,
    ESTADO_AGOTADO,
    DESTINO_TIENDA,
    DESTINO_VENTA,
    _MOVIMIENTO_PEDIDO,
    ESTADO_PAGO_PAGADO,
    ESTADO_PAGO_PENDIENTE,
    ESTADO_PEDIDO_CANCELADO,
    _today_iso,
    _now_iso,
    _now_time,
    _safe_date,
    _days_until,
    _pedido_pagado,
    _parse_utc,
    PedidoCanceladoConPagoError,
)
from domain.services.rule_context import RuleContext
from domain.services.domain_components import compose_domain
from domain.services.accounts_rules import AccountsRules
from domain.services.memberships_rules import MembershipsRules
from domain.services.store_rules import StoreRules
from domain.services.attendance_rules import AttendanceRules
from domain.services.schedules_rules import SchedulesRules
from domain.services.inventory_rules import InventoryRules
from domain.services.dashboard_rules import DashboardRules


class GymDomainService:
    def __init__(self, state: dict[str, Any] | None = None, passwords: PasswordHasher | None = None) -> None:
        self._context = RuleContext(state if state is not None else self._seed(), passwords,
                                    today_provider=lambda: _today_iso(), now_provider=lambda: _now_iso())

    @property
    def context(self):
        if "_context" not in self.__dict__:
            self._context = RuleContext(self.__dict__.pop("state", {}), self.__dict__.pop("passwords", None))
        return self._context

    @property
    def components(self):
        if "_components" not in self.__dict__:
            self._components = compose_domain(self.context)
        return self._components

    @property
    def state(self):
        return self.context.state

    @state.setter
    def state(self, value):
        self.context.state = value

    @property
    def passwords(self):
        return self.context.passwords

    @passwords.setter
    def passwords(self, value):
        self.context.passwords = value

    def _seed(self) -> dict[str, Any]:
        return {
            "inventario": [],
            "mov_inv": [],
            "productos_tienda": [],
            "pedidos_tienda": [],
            "usuario": [],
            "clientes": [],
            "tickets_atencion": [],
            "horario": [],
            "horarios_servicio": [],
            "matriculas_horario": [],
            "rutina_progreso": [],
            "catalogo_rutina": [],
            "asistencia": [],
            "membresia": [],
            "planes_membresia": [
                {
                    "id_pm": 1,
                    "nombre_plan": "MENSUAL",
                    "duracion": "30 dias",
                    "precio": 79,
                    "descripcion": "Acceso completo por 30 dias para entrenar con flexibilidad.",
                    "beneficios": "Uso de sala, horarios por servicio y control digital de asistencia.",
                    "activo": True,
                },
                {
                    "id_pm": 2,
                    "nombre_plan": "3 MESES",
                    "duracion": "90 dias",
                    "precio": 199,
                    "descripcion": "Plan trimestral para sostener progreso y ahorrar frente al pago mensual.",
                    "beneficios": "Acceso completo, matricula de horarios y seguimiento de rutina.",
                    "activo": True,
                },
                {
                    "id_pm": 3,
                    "nombre_plan": "ANUAL",
                    "duracion": "365 dias",
                    "precio": 699,
                    "descripcion": "Membresia anual para clientes constantes con mejor precio acumulado.",
                    "beneficios": "Acceso completo, prioridad operativa y seguimiento continuo.",
                    "activo": True,
                },
            ],
            "promociones": [],
            "configuracion_gimnasio": {
                "capacidad_total": 30,
                "capacidad_por_hora": 10,
            },
        }

    def _normalize(self, state: dict[str, Any]) -> dict[str, Any]:
        seed = self._seed()
        merged = {**seed, **(state or {})}

        # Garantiza las estructuras esperadas sin romper objetos tipo configuración.
        for key, value in seed.items():
            if isinstance(value, list) and not isinstance(merged.get(key), list):
                merged[key] = value
            elif isinstance(value, dict) and not isinstance(merged.get(key), dict):
                merged[key] = value

        merged["usuario"] = [self._normalize_usuario_record(row) for row in merged.get("usuario", []) if isinstance(row, dict)]
        merged["clientes"] = [self._normalize_cliente_record(row, index) for index, row in enumerate(merged.get("clientes", []), start=1) if isinstance(row, dict)]

        for membership in merged.get("membresia", []):
            membership["estado"] = normalize_membership_status(membership.get("estado"))

        # Migración de inventario: cada item debe tener número de activo único y datos comerciales.
        used_assets: set[int] = set()
        for index, item in enumerate(merged.get("inventario", []), start=1):
            try:
                current = int(item.get("n_activo") or 0)
            except Exception:
                current = 0
            if current <= 0 or current in used_assets:
                current = max(used_assets, default=0) + 1
            item["n_activo"] = current
            used_assets.add(current)
            item.setdefault("unidad_venta", "unidad")
            item.setdefault("precio_venta", 0)
            item.setdefault("stock_minimo", 1)
            item.setdefault("ubicacion", "Almacén")
            item.setdefault("observaciones", "")

        for index, asistencia in enumerate(merged.get("asistencia", []), start=1):
            asistencia.setdefault("id_asistencia", index)
            asistencia.setdefault("servicio", "fitness")

        for producto in merged.get("productos_tienda", []):
            producto.setdefault("id_item", None)
            producto.setdefault("unidad_venta", "unidad")

        merged["pedidos_tienda"] = [
            self._normalize_pedido_tienda(row, index)
            for index, row in enumerate(merged.get("pedidos_tienda", []), start=1)
            if isinstance(row, dict)
        ]
        merged["promociones"] = [
            self._normalize_promocion(row, index)
            for index, row in enumerate(merged.get("promociones", []), start=1)
            if isinstance(row, dict)
        ]

        merged["horarios_servicio"] = self._normalize_horarios_servicio(merged.get("horarios_servicio", seed["horarios_servicio"]))
        merged["matriculas_horario"] = [
            self._normalize_matricula_horario(row, index)
            for index, row in enumerate(merged.get("matriculas_horario", []), start=1)
            if isinstance(row, dict)
        ]
        merged["rutina_progreso"] = [
            self._normalize_rutina_progreso(row, index)
            for index, row in enumerate(merged.get("rutina_progreso", []), start=1)
            if isinstance(row, dict)
        ]
        self._recount_schedule_cupos(merged)

        cfg = {**seed["configuracion_gimnasio"], **merged.get("configuracion_gimnasio", {})}
        cfg["capacidad_total"] = max(1, int(cfg.get("capacidad_total") or 30))
        cfg["capacidad_por_hora"] = max(1, int(cfg.get("capacidad_por_hora") or 10))
        merged["configuracion_gimnasio"] = cfg

        for cliente in merged.get("clientes", []):
            self._ensure_membership_for_active_client(merged, cliente)

        return merged

    def _change(self, operation):
        """Aplica reglas al agregado; no consulta ni guarda datos externos."""
        return operation(self.state)

    def expire_memberships(self) -> bool:
        today = self.today()
        # Evita escrituras y cambios en el TTL cuando el estado ya está actualizado.
        preview = {
            key: [dict(row) for row in self.state.get(key, [])]
            for key in ("clientes", "membresia")
        }
        if not apply_membership_expiration(preview, today):
            return False
        return self._change(lambda state: apply_membership_expiration(state, today))

    def _next_int_id(self, table: str, key: str) -> int:
        rows = self.state[table]
        return max(int(self.state.get("_identity_floors", {}).get(table, 0)),
                   max((int(row.get(key, 0) or 0) for row in rows), default=0)) + 1

    def _next_int_id_in_state(self, state: dict[str, Any], table: str, key: str) -> int:
        rows = state.setdefault(table, [])
        return max(int(state.get("_identity_floors", {}).get(table, 0)),
                   max((int(row.get(key, 0) or 0) for row in rows), default=0)) + 1

    def today(self):
        return _today_iso()

    def now(self):
        return _now_iso()

    def safe_date(self, value):
        return value if value else self.today()

    def latest_membership(self, client_id):
        return self._latest_membership_for_cliente(self.state, client_id)

    def normalize(self):
        self.state = self._normalize(self.state)
        return self.state

    def parse_client_id(self, value):
        return self._parse_cliente_id(value)

    def resolve_attendance_client(self, payload):
        return self._resolve_cliente_for_attendance(payload)

    def recount_schedule(self):
        self._recount_schedule_cupos(self.state)

    def refresh_store_status(self):
        self._actualizar_estados_tienda(self.state)

    def is_store_inventory(self, item):
        return self._es_item_tienda(item)

    def user_role_prefix(self, role):
        return self._user_role_prefix(role)

    def schedule_day_code(self, day):
        return self._day_code(day)

    def normalize_schedule_day(self, day):
        return self._normalize_day(day)

    def validate_enrollment(self, client_id, schedule_id):
        return self._validate_new_schedule_enrollment(self.state, client_id, schedule_id)

    def _user_role_prefix(self, rol: str):
        return self.components.accounts._user_role_prefix(rol)

    def _normalize_usuario_id(self, value: Any):
        return self.components.accounts._normalize_usuario_id(value)

    def _next_usuario_code(self, state: dict[str, Any]):
        return self.components.accounts._next_usuario_code(state)

    def _normalize_usuario_record(self, row: dict[str, Any]):
        return self.components.accounts._normalize_usuario_record(row)

    def get_usuario(self, id_usuario: Any):
        return self.components.accounts.get_usuario(id_usuario)

    def get_usuario_by_email(self, email: str):
        return self.components.accounts.get_usuario_by_email(email)

    def usuarios(self):
        return self.components.accounts.usuarios()

    def usuarios_normalized(self):
        return self.components.accounts.usuarios_normalized()

    def _change_users(self, fn):
        return self.components.accounts._change_users(fn)

    def upsert_usuario(self, payload: dict[str, Any]):
        return self.components.accounts.upsert_usuario(payload)

    def delete_usuario(self, id_usuario: Any):
        return self.components.accounts.delete_usuario(id_usuario)

    def clientes(self):
        return self.components.accounts.clientes()

    def _normalize_cliente_record(self, row: dict[str, Any], fallback_index: int):
        return self.components.accounts._normalize_cliente_record(row, fallback_index)

    def clientes_normalized(self):
        return self.components.accounts.clientes_normalized()

    def upsert_cliente(self, payload: dict[str, Any]):
        return self.components.accounts.upsert_cliente(payload)

    def get_cliente(self, id_cliente: int):
        return self.components.accounts.get_cliente(id_cliente)

    def get_cliente_by_dni(self, dni: str):
        return self.components.accounts.get_cliente_by_dni(dni)

    def get_cliente_by_email(self, email: str):
        return self.components.accounts.get_cliente_by_email(email)

    def get_account_by_google_sub(self, subject: str):
        return self.components.accounts.get_account_by_google_sub(subject)

    def link_google_account(self, kind: str, account_id: str, subject: str):
        return self.components.accounts.link_google_account(kind, account_id, subject)

    def authenticate_usuario_password(self, correo: str, password: str):
        return self.components.accounts.authenticate_usuario_password(correo, password)

    def authenticate_cliente_password(self, correo: str, password: str):
        return self.components.accounts.authenticate_cliente_password(correo, password)

    def delete_cliente(self, id_cliente: int):
        return self.components.accounts.delete_cliente(id_cliente)

    def _normalize_pedido_tienda(self, row: dict[str, Any], fallback_id: int):
        return self.components.store._normalize_pedido_tienda(row, fallback_id)

    def productos_tienda(self):
        return self.components.store.productos_tienda()

    def get_producto_tienda(self, id_producto: int):
        return self.components.store.get_producto_tienda(id_producto)

    def upsert_producto_tienda(self, payload: dict[str, Any], actor: Any=None):
        return self.components.store.upsert_producto_tienda(payload, actor)

    def delete_producto_tienda(self, id_producto: int):
        return self.components.store.delete_producto_tienda(id_producto)

    def pedidos_tienda(self):
        return self.components.store.pedidos_tienda()

    def crear_pedido_tienda(self, payload: dict[str, Any]):
        return self.components.store.crear_pedido_tienda(payload)

    def crear_pedido_tienda_pago_pendiente(self, payload: dict[str, Any]):
        return self.components.store.crear_pedido_tienda_pago_pendiente(payload)

    def _crear_pedido_tienda(self, payload: dict[str, Any], pago_pendiente: bool):
        return self.components.store._crear_pedido_tienda(payload, pago_pendiente)

    def _devolver_stock_pedido(self, state: dict[str, Any], pedido: dict[str, Any]):
        return self.components.store._devolver_stock_pedido(state, pedido)

    _find_pedido_in_state = staticmethod(StoreRules._find_pedido_in_state)

    def get_pedido_tienda(self, id_pedido: int):
        return self.components.store.get_pedido_tienda(id_pedido)

    def pedidos_pago_pendiente(self):
        return self.components.store.pedidos_pago_pendiente()

    minutos_desde_creacion = staticmethod(StoreRules.minutos_desde_creacion)

    def registrar_sesion_pago_pedido(self, id_pedido: int, session_id: str):
        return self.components.store.registrar_sesion_pago_pedido(id_pedido, session_id)

    def confirmar_pago_pedido_tienda(self, id_pedido: int, payload: dict[str, Any]):
        return self.components.store.confirmar_pago_pedido_tienda(id_pedido, payload)

    def cancelar_pedido_pago_pendiente(self, id_pedido: int, observacion: str=''):
        return self.components.store.cancelar_pedido_pago_pendiente(id_pedido, observacion)

    def actualizar_pedido_tienda(self, id_pedido: int, payload: dict[str, Any], actor: Any=None):
        return self.components.store.actualizar_pedido_tienda(id_pedido, payload, actor)

    def _time_to_minutes(self, hora: str):
        return self.components.schedules._time_to_minutes(hora)

    def _date_day_name(self, fecha: str):
        return self.components.schedules._date_day_name(fecha)

    def _normalize_day(self, value: Any):
        return self.components.schedules._normalize_day(value)

    def _day_code(self, day: str):
        return self.components.schedules._day_code(day)

    def _validate_short_service_schedule_range(self, hora_inicio: str, hora_fin: str):
        return self.components.schedules._validate_short_service_schedule_range(hora_inicio, hora_fin)

    def _minutes_to_time(self, value: int):
        return self.components.schedules._minutes_to_time(value)

    def _short_service_schedule_range(self, hora_inicio: Any, hora_fin: Any):
        return self.components.schedules._short_service_schedule_range(hora_inicio, hora_fin)

    def _normalize_horarios_servicio(self, rows: Any):
        return self.components.schedules._normalize_horarios_servicio(rows)

    def _normalize_matricula_horario(self, row: dict[str, Any], fallback_index: int):
        return self.components.schedules._normalize_matricula_horario(row, fallback_index)

    def _normalize_rutina_progreso(self, row: dict[str, Any], fallback_index: int):
        return self.components.schedules._normalize_rutina_progreso(row, fallback_index)

    def _recount_schedule_cupos(self, state: dict[str, Any]):
        return self.components.schedules._recount_schedule_cupos(state)

    def _validate_service_schedule(self, state: dict[str, Any], servicio: str, fecha: str, hora: str):
        return self.components.schedules._validate_service_schedule(state, servicio, fecha, hora)

    def tickets(self):
        return self.components.schedules.tickets()

    def upsert_ticket(self, payload: dict[str, Any]):
        return self.components.schedules.upsert_ticket(payload)

    def catalogo_rutina(self):
        return self.components.schedules.catalogo_rutina()

    def upsert_rutina(self, payload: dict[str, Any]):
        return self.components.schedules.upsert_rutina(payload)

    def horarios(self):
        return self.components.schedules.horarios()

    def upsert_horario(self, payload: dict[str, Any]):
        return self.components.schedules.upsert_horario(payload)

    def configuracion_gimnasio(self):
        return self.components.schedules.configuracion_gimnasio()

    def actualizar_configuracion_gimnasio(self, payload: dict[str, Any]):
        return self.components.schedules.actualizar_configuracion_gimnasio(payload)

    def horarios_servicio(self, solo_activos: bool=False):
        return self.components.schedules.horarios_servicio(solo_activos)

    def get_horario_servicio(self, id_horario_servicio: int):
        return self.components.schedules.get_horario_servicio(id_horario_servicio)

    def upsert_horario_servicio(self, payload: dict[str, Any]):
        return self.components.schedules.upsert_horario_servicio(payload)

    def delete_horario_servicio(self, id_horario_servicio: int):
        return self.components.schedules.delete_horario_servicio(id_horario_servicio)

    def matriculas_horario(self, id_cliente: int | None=None, dni: str | None=None, solo_activas: bool=False):
        return self.components.schedules.matriculas_horario(id_cliente, dni, solo_activas)

    def get_matricula_horario(self, id_matricula: int):
        return self.components.schedules.get_matricula_horario(id_matricula)

    def asignar_rutina_matricula(self, id_matricula: int, id_rutina: int):
        return self.components.schedules.asignar_rutina_matricula(id_matricula, id_rutina)

    def trainer_rutinas_cliente(self, dni: str):
        return self.components.schedules.trainer_rutinas_cliente(dni)

    def registrar_progreso_rutina(self, id_matricula: int, payload: dict[str, Any]):
        return self.components.schedules.registrar_progreso_rutina(id_matricula, payload)

    def trainer_overview(self):
        return self.components.schedules.trainer_overview()

    def _validate_new_schedule_enrollment(self, state: dict[str, Any], id_cliente: int, id_horario: int):
        return self.components.schedules._validate_new_schedule_enrollment(state, id_cliente, id_horario)

    def matricular_cliente_horario(self, payload: dict[str, Any]):
        return self.components.schedules.matricular_cliente_horario(payload)

    def cancelar_matricula_horario(self, id_matricula: int, id_cliente: int | None=None):
        return self.components.schedules.cancelar_matricula_horario(id_matricula, id_cliente)

    def inventario(self):
        return self.components.inventory.inventario()

    def get_item_inventario(self, id_item: int):
        return self.components.inventory.get_item_inventario(id_item)

    _es_item_tienda = staticmethod(InventoryRules._es_item_tienda)

    _find_item_in_state = staticmethod(InventoryRules._find_item_in_state)

    _next_n_activo = staticmethod(InventoryRules._next_n_activo)

    def _actor_usuario_id(self, actor: Any):
        return self.components.inventory._actor_usuario_id(actor)

    def _aplicar_movimiento(self, state: dict[str, Any], item: dict[str, Any], tipo: str, cantidad: int, descripcion: str, id_usuario: str | None=None, fecha: str='', destino: str | None=None):
        return self.components.inventory._aplicar_movimiento(state, item, tipo, cantidad, descripcion, id_usuario, fecha, destino)

    _producto_de_item = staticmethod(InventoryRules._producto_de_item)

    _normalizar_destino = staticmethod(InventoryRules._normalizar_destino)

    def _actualizar_estados_tienda(self, state: dict[str, Any]):
        return self.components.inventory._actualizar_estados_tienda(state)

    def _actualizar_estados_items_tienda(self, state: dict[str, Any]):
        return self.components.inventory._actualizar_estados_items_tienda(state)

    def _crear_producto_para_item(self, state: dict[str, Any], item: dict[str, Any]):
        return self.components.inventory._crear_producto_para_item(state, item)

    def upsert_inventario(self, payload: dict[str, Any], actor: Any=None):
        return self.components.inventory.upsert_inventario(payload, actor)

    def delete_inventario(self, id_item: int):
        return self.components.inventory.delete_inventario(id_item)

    def movimientos_inventario(self):
        return self.components.inventory.movimientos_inventario()

    def registrar_movimiento_inventario(self, payload: dict[str, Any]):
        return self.components.inventory.registrar_movimiento_inventario(payload)

    def actualizar_movimiento_inventario(self, id_mov: int, payload: dict[str, Any]):
        return self.components.inventory.actualizar_movimiento_inventario(id_mov, payload)

    def _active_membership_for_cliente(self, state: dict[str, Any], id_cliente: int):
        return self.components.memberships._active_membership_for_cliente(state, id_cliente)

    def _latest_membership_for_cliente(self, state: dict[str, Any], id_cliente: int):
        return self.components.memberships._latest_membership_for_cliente(state, id_cliente)

    def _plan_duration_days(self, plan_name: str):
        return self.components.memberships._plan_duration_days(plan_name)

    def _duration_days(self, plan: dict[str, Any]):
        return self.components.memberships._duration_days(plan)

    def _normalize_promocion(self, row: dict[str, Any], fallback_id: int):
        return self.components.memberships._normalize_promocion(row, fallback_id)

    def _ensure_plan_for_client(self, state: dict[str, Any], plan_name: str):
        return self.components.memberships._ensure_plan_for_client(state, plan_name)

    def _ensure_membership_for_active_client(self, state: dict[str, Any], cliente: dict[str, Any]):
        return self.components.memberships._ensure_membership_for_active_client(state, cliente)

    def planes_membresia(self):
        return self.components.memberships.planes_membresia()

    def get_plan_membresia(self, id_pm: int):
        return self.components.memberships.get_plan_membresia(id_pm)

    def upsert_plan_membresia(self, payload: dict[str, Any]):
        return self.components.memberships.upsert_plan_membresia(payload)

    def delete_plan_membresia(self, id_pm: int):
        return self.components.memberships.delete_plan_membresia(id_pm)

    def _get_usos_promocion(self, state: dict[str, Any], promo: dict[str, Any]):
        return self.components.memberships._get_usos_promocion(state, promo)

    def promociones(self):
        return self.components.memberships.promociones()

    def upsert_promocion(self, payload: dict[str, Any]):
        return self.components.memberships.upsert_promocion(payload)

    def delete_promocion(self, id_promocion: int):
        return self.components.memberships.delete_promocion(id_promocion)

    def get_promocion_vigente_para_plan(self, state: dict[str, Any], id_pm: int):
        return self.components.memberships.get_promocion_vigente_para_plan(state, id_pm)

    def promociones_vigentes_publicas(self):
        return self.components.memberships.promociones_vigentes_publicas()

    def _apply_promocion_discount(self, state: dict[str, Any], id_pm: int, id_promocion: int | None):
        return self.components.memberships._apply_promocion_discount(state, id_pm, id_promocion)

    def _increment_promocion_usos(self, state: dict[str, Any], id_promocion: int | None):
        return self.components.memberships._increment_promocion_usos(state, id_promocion)

    def membresias(self):
        return self.components.memberships.membresias()

    def membresias_por_cliente(self, id_cliente: int):
        return self.components.memberships.membresias_por_cliente(id_cliente)

    def crear_membresia(self, payload: dict[str, Any]):
        return self.components.memberships.crear_membresia(payload)

    def _calcular_monto_con_descuento(self, id_pm: int, id_promocion: int | None):
        return self.components.memberships._calcular_monto_con_descuento(id_pm, id_promocion)

    def registrar_cliente_con_membresia(self, payload: dict[str, Any]):
        return self.components.memberships.registrar_cliente_con_membresia(payload)

    def registrar_cliente_publico(self, payload: dict[str, Any], *, origen_registro: str='PUBLICO'):
        return self.components.memberships.registrar_cliente_publico(payload, origen_registro=origen_registro)

    def confirmar_pago_cliente_publico(self, id_cliente: int, payload: dict[str, Any]):
        return self.components.memberships.confirmar_pago_cliente_publico(id_cliente, payload)

    def confirmar_pago_manual_cliente(self, id_cliente: int):
        return self.components.memberships.confirmar_pago_manual_cliente(id_cliente)

    def activar_membresia_cliente(self, id_cliente: int):
        return self.components.memberships.activar_membresia_cliente(id_cliente)

    def summary(self):
        return self.components.dashboard.summary()

    def asistencia(self):
        return self.components.attendance.asistencia()

    def registrar_asistencia(self, id_cliente: int):
        return self.components.attendance.registrar_asistencia(id_cliente)

    def _parse_cliente_id(self, raw_id_cliente: Any):
        return self.components.attendance._parse_cliente_id(raw_id_cliente)

    def _attendance_hour_key(self, hora: str):
        return self.components.attendance._attendance_hour_key(hora)

    def _validate_attendance_capacity(self, state: dict[str, Any], fecha: str, hora: str, exclude_id: int | None=None):
        return self.components.attendance._validate_attendance_capacity(state, fecha, hora, exclude_id)

    def registrar_asistencia_detallada(self, payload: dict[str, Any]):
        return self.components.attendance.registrar_asistencia_detallada(payload)

    def _resolve_cliente_for_attendance(self, payload: dict[str, Any]):
        return self.components.attendance._resolve_cliente_for_attendance(payload)

    def registrar_entrada_horario(self, payload: dict[str, Any]):
        return self.components.attendance.registrar_entrada_horario(payload)

    def registrar_salida_horario(self, payload: dict[str, Any]):
        return self.components.attendance.registrar_salida_horario(payload)

    def actualizar_asistencia(self, id_asistencia: int, payload: dict[str, Any]):
        return self.components.attendance.actualizar_asistencia(id_asistencia, payload)

    def eliminar_asistencia(self, id_asistencia: int):
        return self.components.attendance.eliminar_asistencia(id_asistencia)

    def registrar_asistencia_por_dni(self, dni: str):
        return self.components.attendance.registrar_asistencia_por_dni(dni)
