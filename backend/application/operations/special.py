"""Operaciones de lectura y comandos compartidos por los servicios específicos."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.read_models import MembershipPaymentData, AttendanceHistoryData
from application.operations.contracts import Record, Identifier

CLIENTS = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA)
SCHEDULES = (*CLIENTS, Resource.MATRICULAS_HORARIO, Resource.HORARIOS_SERVICIO,
             Resource.CATALOGO_RUTINA, Resource.ASISTENCIA, Resource.RUTINA_PROGRESO)


@dataclass(frozen=True)
class ExpireMembershipsCommand:
    resources: ClassVar = CLIENTS

    def run(self, rules: DomainComponents) -> bool:
        return rules.context.expire_memberships()


@dataclass(frozen=True)
class EnrollScheduleCommand:
    payload: Record
    resources: ClassVar = SCHEDULES

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.matricular_cliente_horario(self.payload)


@dataclass(frozen=True)
class UpdateGymSettingsCommand:
    payload: Record
    resources: ClassVar = (Resource.CONFIGURACION_GIMNASIO,)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.actualizar_configuracion_gimnasio(self.payload)


@dataclass(frozen=True)
class MembershipPaymentQuery:
    resources: ClassVar = CLIENTS

    def run(self, rules: DomainComponents) -> MembershipPaymentData:
        return MembershipPaymentData(rules.accounts.clientes(), rules.memberships.planes_membresia(),
                                     rules.memberships.membresias())


@dataclass(frozen=True)
class AttendanceHistoryQuery:
    resources: ClassVar = (Resource.ASISTENCIA, Resource.CLIENTES)

    def run(self, rules: DomainComponents) -> AttendanceHistoryData:
        return AttendanceHistoryData(rules.attendance.asistencia(), rules.accounts.clientes())


@dataclass(frozen=True)
class AttendanceEnrollmentsQuery:
    client_id: int | None = None
    resources: ClassVar = SCHEDULES

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.matriculas_horario(id_cliente=self.client_id)


@dataclass(frozen=True)
class LatestMembershipQuery:
    client_id: int
    resources: ClassVar = CLIENTS

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.memberships._latest_membership_for_cliente(rules.context.state, self.client_id)


@dataclass(frozen=True)
class ResolveAttendanceClientQuery:
    payload: Record
    resources: ClassVar = CLIENTS

    def run(self, rules: DomainComponents) -> int:
        return rules.attendance._resolve_cliente_for_attendance(self.payload)


@dataclass(frozen=True)
class AccountForSessionQuery:
    subject: Identifier
    client: bool = False

    @property
    def resources(self) -> tuple[Resource, ...]:
        return CLIENTS if self.client else (Resource.USUARIO,)

    def run(self, rules: DomainComponents) -> Record | None:
        rows = rules.accounts.clientes() if self.client else rules.accounts.usuarios()
        return next((row for row in rows if str(row.get("id_usuario")) == str(self.subject)), None)


@dataclass(frozen=True)
class LegacySnapshotQuery:
    """Compatibilidad para consumidores anteriores que inspeccionan instantáneas."""
    resources: tuple[Resource, ...]

    def run(self, rules: DomainComponents) -> dict:
        return deepcopy({key: rules.context.state.get(key) for key in self.resources})
