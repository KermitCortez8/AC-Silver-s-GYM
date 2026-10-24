"""Comando local de asistencia con la misma validación dentro de la transacción."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar
from application.operations.contracts import Record
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from domain.services.client_identifiers import parse_client_id
from domain.errors import AttendanceConflict


@dataclass(frozen=True)
class AttendanceDomainAccess:
    """Capacidades de lectura que utiliza la política de admisión de asistencia."""
    rules: DomainComponents

    parse_client_id = staticmethod(parse_client_id)

    def get_cliente(self, identity):
        return self.rules.accounts.get_cliente(identity)

    def membresias_por_cliente(self, identity):
        return self.rules.memberships.membresias_por_cliente(identity)

    def configuracion_gimnasio(self):
        return self.rules.schedules.configuracion_gimnasio()

    def asistencia(self):
        return self.rules.attendance.asistencia()

    def get_horario_servicio(self, identity):
        return self.rules.schedules.get_horario_servicio(identity)


@dataclass(frozen=True)
class SaveAttendanceCommand:
    row: Record
    expected_version: int | None
    audit: Record
    timestamp: datetime
    operation_kind: ClassVar[str] = "command"
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.ASISTENCIA,
        Resource.CLIENTES,
        Resource.MEMBRESIA,
        Resource.MATRICULAS_HORARIO,
        Resource.HORARIOS_SERVICIO,
        Resource.CONFIGURACION_GIMNASIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        from application.services.attendance_service import AttendanceService
        policy = AttendanceService(AttendanceDomainAccess(rules), clock=lambda: self.timestamp)
        return apply_record(policy, rules.context.state, deepcopy(self.row), self.expected_version, deepcopy(self.audit))


def apply_record(policy, state, row, expected, audit):
    operation = audit["accion"]
    request_id = audit.get("request_id")
    rows = state.setdefault("asistencia", [])
    old = next((r for r in rows if r.get("id_asistencia") == row.get("id_asistencia")), None)
    if expected is None:
        if policy.kind(row) == "general":
            duplicate = policy.general_retry(rows, policy.client_id(row), request_id)
        else:
            duplicate = next((r for r in rows if not r.get("anulado")
                              and policy.client_id(r) == policy.client_id(row)
                              and r.get("id_matricula") == row.get("id_matricula")
                              and r.get("fecha") == row["fecha"]), None)
        if duplicate:
            return duplicate
        if policy.kind(row) == "general":
            policy.general_context(policy.client_id(row), policy.now())
        else:
            enrollment = next(e for e in state["matriculas_horario"] if e["id_matricula"] == row["id_matricula"])
            policy.entry_context(enrollment, policy.now())
        row["id_asistencia"] = max((r["id_asistencia"] for r in rows), default=0) + 1
    elif not old or int(old.get("version") or 0) != expected:
        if operation == "salida" and old and old.get("hora_salida") and not old.get("anulado"):
            return old
        raise AttendanceConflict("El registro cambió. Actualiza el historial e inténtalo de nuevo.")
    if not row.get("anulado"):
        for other in rows:
            if other.get("id_asistencia") == row.get("id_asistencia") or other.get("anulado") or policy.client_id(other) != policy.client_id(row):
                continue
            if (row.get("id_matricula") and other.get("id_matricula") == row["id_matricula"] and other["fecha"] == row["fecha"]) or (not row.get("hora_salida") and not other.get("hora_salida")):
                raise AttendanceConflict("El cliente ya tiene una asistencia para ese horario y día, o una entrada sin salida.")
    fields = ("fecha", "hora_entrada", "hora_salida", "fecha_salida", "anulado")
    audit["antes"] = {k: old.get(k) for k in fields} if old else None
    audit["despues"] = {k: row.get(k) for k in fields}
    row["auditoria"] = [*(old or {}).get("auditoria", []), audit]
    row["version"] = int((old or {}).get("version") or 0) + 1
    if old:
        rows[rows.index(old)] = deepcopy(row)
    else:
        rows.insert(0, deepcopy(row))
    return row
