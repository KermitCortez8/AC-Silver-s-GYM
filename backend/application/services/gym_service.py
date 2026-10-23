"""Coordina reglas y persistencia mediante un repositorio inyectado."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from application.ports.gym_repository import GymRepository
from application.ports.integrations import IdentityProvider, SessionProvider, PaymentGateway
from application.read_models import MembershipPaymentData, AttendanceHistoryData
from domain.ports import PasswordHasher
from domain.errors import raise_schedule_enrollment_error
from domain.services.gym_domain_service import GymDomainService
from domain.services import gym_domain_service as domain_clock
from domain.services.membership_lifecycle import apply_membership_expiration
from application.services.modules.accounts import AccountsOperations
from application.services.modules.memberships import MembershipsOperations
from application.services.modules.attendance import AttendanceOperations
from application.services.modules.inventory import InventoryOperations
from application.services.modules.configuration import ConfigurationOperations
from application.services.modules.schedules import SchedulesOperations
from application.services.modules.store import StoreOperations


class GymService(
    AccountsOperations, MembershipsOperations, AttendanceOperations, InventoryOperations,
    ConfigurationOperations, SchedulesOperations, StoreOperations,
):
    def __init__(
        self, repository: GymRepository, passwords: PasswordHasher, *,
        identity: IdentityProvider | None = None, sessions: SessionProvider | None = None,
        gateway_factory: Callable[[Any], PaymentGateway] | None = None,
    ):
        self.repository = repository
        self.passwords = passwords
        self.identity = identity
        self.sessions = sessions
        self.gateway_factory = gateway_factory

    def _rules(self, state):
        return GymDomainService(state, self.passwords)

    def _execute(self, name, write, *args, **kwargs):
        operation = lambda state: deepcopy(getattr(self._rules(state), name)(*args, **kwargs))
        if write:
            resources = ("usuario",) if name in {"upsert_usuario", "delete_usuario"} else None
            try:
                return self.repository.change(operation, resources=resources)
            except RuntimeError as error:
                if name == "asignar_rutina_matricula":
                    raise_schedule_enrollment_error(error)
                raise
        return self.repository.read(operation)

    def ensure_fresh(self, resources=None):
        self.repository.refresh(resources)
        if resources is None or "clientes" in resources or "membresia" in resources:
            self.expire_memberships()

    def expire_memberships(self):
        preview = self._snapshot("clientes", "membresia")
        if not apply_membership_expiration(preview, domain_clock._today_iso()):
            return False
        return self._execute("expire_memberships", True)

    def _snapshot(self, *resources):
        return self.repository.read(lambda state: deepcopy(
            {key: state.get(key) for key in resources} if resources else state
        ))

    def membership_payment_data(self):
        return self.repository.read(lambda state: MembershipPaymentData(
            deepcopy(state.get("clientes", [])), deepcopy(state.get("planes_membresia", [])),
            deepcopy(state.get("membresia", [])),
        ))

    def attendance_history_data(self):
        return self.repository.read(lambda state: AttendanceHistoryData(
            deepcopy(state.get("asistencia", [])), deepcopy(state.get("clientes", [])),
        ))

    def attendance_enrollments(self, client_id=None):
        return self.repository.read(lambda state: [deepcopy(row) for row in state.get("matriculas_horario", [])
                                    if client_id is None or int(row.get("id_cliente") or 0) == int(client_id)])

    def latest_membership(self, client_id):
        return self.repository.read(lambda state: deepcopy(
            self._rules(state).latest_membership(client_id)
        ))

    def membership(self, client_id, membership_id):
        return next((row for row in self.membresias_por_cliente(client_id)
                     if int(row.get("id_membresia") or 0) == int(membership_id)), None)

    def parse_client_id(self, value):
        return self._rules({}).parse_client_id(value)

    def resolve_attendance_client(self, payload):
        return self.repository.read(lambda state: self._rules(state).resolve_attendance_client(payload))

    def account_for_session(self, subject, client=False):
        resource = "clientes" if client else "usuario"
        return self.repository.read(lambda state: next(
            (deepcopy(row) for row in state.get(resource, []) if str(row.get("id_usuario")) == str(subject)), None
        ))

    def validate_admin_registration_schema(self):
        self.repository.validate_admin_registration_schema()

    def matricular_cliente_horario(self, payload: dict[str, Any]):
        result = self.repository.enroll(payload)
        return result if result is not None else self._execute("matricular_cliente_horario", True, payload)

    def actualizar_configuracion_gimnasio(self, payload: dict[str, Any]):
        result = self.repository.save_settings(payload)
        return result if result is not None else self._execute("actualizar_configuracion_gimnasio", True, payload)

    def save_attendance(self, row, expected_version, audit):
        return self.repository.save_attendance(row, expected_version, audit)

    def change_attendance(self, operation):
        return self.repository.change(operation)
