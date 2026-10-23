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
from domain.services.accounts_rules import AccountsRules
from domain.services.memberships_rules import MembershipsRules
from domain.services.store_rules import StoreRules
from domain.services.attendance_rules import AttendanceRules
from domain.services.schedules_rules import SchedulesRules
from domain.services.inventory_rules import InventoryRules
from domain.services.dashboard_rules import DashboardRules


class GymDomainService(
    AccountsRules, MembershipsRules, StoreRules, AttendanceRules,
    SchedulesRules, InventoryRules, DashboardRules,
):
    def __init__(self, state: dict[str, Any] | None = None, passwords: PasswordHasher | None = None) -> None:
        self.state = state if state is not None else self._seed()
        self.passwords = passwords

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
