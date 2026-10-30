"""Coordina reglas y persistencia mediante un repositorio inyectado."""
from __future__ import annotations

from typing import Any, Callable

from application.ports.gym_repository import GymRepository
from application.operations.special import (ExpireMembershipsCommand, EnrollScheduleCommand, UpdateGymSettingsCommand,
    MembershipPaymentQuery, AttendanceHistoryQuery, AttendanceEnrollmentsQuery, LatestMembershipQuery,
    ResolveAttendanceClientQuery, AccountForSessionQuery, LegacySnapshotQuery)
from domain.models.resources import Resource
from application.services.operation_executor import OperationExecutor
from application.ports.integrations import IdentityProvider, SessionProvider, PaymentGateway
from domain.ports import PasswordHasher
from domain.services.gym_domain_service import GymDomainService
from application.services.modules.accounts import AccountsOperations
from application.services.modules.memberships import MembershipsOperations
from application.services.modules.attendance import AttendanceOperations
from application.services.modules.inventory import InventoryOperations
from application.services.modules.configuration import ConfigurationOperations
from application.services.modules.schedules import SchedulesOperations
from application.services.modules.store import StoreOperations


class GymService:
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

    @property
    def executor(self):
        return OperationExecutor(self.repository, self.passwords)

    def ensure_fresh(self, resources=None):
        """Refresca la caché. Persistir vencimientos es un comando explícito."""
        self.repository.refresh(resources)

    def expire_memberships(self):
        return self.executor.execute(ExpireMembershipsCommand())

    def _snapshot(self, *resources):
        return self.executor.query(LegacySnapshotQuery(tuple(Resource(r) for r in resources) or tuple(Resource)))

    def membership_payment_data(self):
        return self.executor.query(MembershipPaymentQuery())

    def attendance_page(self, criteria, request):
        return self.repository.attendance_page(criteria, request)

    def attendance_summary(self, day, client_id=None):
        return self.repository.attendance_summary(day, client_id)

    def attendance_history_data(self):
        return self.executor.query(AttendanceHistoryQuery())

    def attendance_enrollments(self, client_id=None):
        return self.executor.query(AttendanceEnrollmentsQuery(client_id))

    def latest_membership(self, client_id):
        return self.executor.query(LatestMembershipQuery(client_id))

    def membership(self, client_id, membership_id):
        return next((row for row in self.membresias_por_cliente(client_id)
                     if int(row.get("id_membresia") or 0) == int(membership_id)), None)

    def parse_client_id(self, value):
        return self._rules({}).parse_client_id(value)

    def resolve_attendance_client(self, payload):
        return self.executor.query(ResolveAttendanceClientQuery(payload))

    def account_for_session(self, subject, client=False):
        return self.executor.query(AccountForSessionQuery(subject, client))

    def validate_admin_registration_schema(self):
        self.repository.validate_admin_registration_schema()

    def matricular_cliente_horario(self, payload: dict[str, Any]):
        result = self.repository.enroll(payload)
        return result if result is not None else self.executor.execute(EnrollScheduleCommand(payload))

    def actualizar_configuracion_gimnasio(self, payload: dict[str, Any]):
        result = self.repository.save_settings(payload)
        return result if result is not None else self.executor.execute(UpdateGymSettingsCommand(payload))

    def save_attendance(self, row, expected_version, audit):
        return self.repository.save_attendance(row, expected_version, audit)

    def apply_local_attendance(self, row, expected_version, audit, timestamp):
        from application.operations.attendance_save import SaveAttendanceCommand
        return self.executor.execute(SaveAttendanceCommand(row, expected_version, audit, timestamp))

    def change_attendance(self, operation):
        """Compatibilidad con integraciones anteriores; los casos nuevos usan comandos."""
        return self.repository.change(operation)

    def productos_tienda(self) -> list[dict[str, Any]]:
        return StoreOperations(self.executor).productos_tienda()

    def get_producto_tienda(self, id_producto: int) -> dict[str, Any] | None:
        return StoreOperations(self.executor).get_producto_tienda(id_producto)

    def upsert_producto_tienda(self, payload: dict[str, Any], actor: Any=None) -> dict[str, Any]:
        return StoreOperations(self.executor).upsert_producto_tienda(payload, actor)

    def delete_producto_tienda(self, id_producto: int) -> dict[str, Any] | None:
        return StoreOperations(self.executor).delete_producto_tienda(id_producto)

    def pedidos_tienda(self) -> list[dict[str, Any]]:
        return StoreOperations(self.executor).pedidos_tienda()

    def crear_pedido_tienda(self, payload: dict[str, Any]) -> dict[str, Any]:
        return StoreOperations(self.executor).crear_pedido_tienda(payload)

    def crear_pedido_tienda_pago_pendiente(self, payload: dict[str, Any]) -> dict[str, Any]:
        return StoreOperations(self.executor).crear_pedido_tienda_pago_pendiente(payload)

    def get_pedido_tienda(self, id_pedido: int) -> dict[str, Any] | None:
        return StoreOperations(self.executor).get_pedido_tienda(id_pedido)

    def pedidos_pago_pendiente(self) -> list[dict[str, Any]]:
        return StoreOperations(self.executor).pedidos_pago_pendiente()

    def minutos_desde_creacion(self, pedido: dict[str, Any]) -> float | None:
        return StoreOperations(self.executor).minutos_desde_creacion(pedido)

    def registrar_sesion_pago_pedido(self, id_pedido: int, session_id: str) -> dict[str, Any]:
        return StoreOperations(self.executor).registrar_sesion_pago_pedido(id_pedido, session_id)

    def confirmar_pago_pedido_tienda(self, id_pedido: int, payload: dict[str, Any]) -> dict[str, Any]:
        return StoreOperations(self.executor).confirmar_pago_pedido_tienda(id_pedido, payload)

    def cancelar_pedido_pago_pendiente(self, id_pedido: int, observacion: str='') -> dict[str, Any]:
        return StoreOperations(self.executor).cancelar_pedido_pago_pendiente(id_pedido, observacion)

    def actualizar_pedido_tienda(self, id_pedido: int, payload: dict[str, Any], actor: Any=None) -> dict[str, Any]:
        return StoreOperations(self.executor).actualizar_pedido_tienda(id_pedido, payload, actor)

    def planes_membresia(self) -> list[dict[str, Any]]:
        return MembershipsOperations(self.executor).planes_membresia()

    def get_plan_membresia(self, id_pm: int) -> dict[str, Any] | None:
        return MembershipsOperations(self.executor).get_plan_membresia(id_pm)

    def upsert_plan_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        return MembershipsOperations(self.executor).upsert_plan_membresia(payload)

    def delete_plan_membresia(self, id_pm: int) -> None:
        return MembershipsOperations(self.executor).delete_plan_membresia(id_pm)

    def promociones(self) -> list[dict[str, Any]]:
        return MembershipsOperations(self.executor).promociones()

    def upsert_promocion(self, payload: dict[str, Any]) -> dict[str, Any]:
        return MembershipsOperations(self.executor).upsert_promocion(payload)

    def delete_promocion(self, id_promocion: int) -> None:
        return MembershipsOperations(self.executor).delete_promocion(id_promocion)

    def get_promocion_vigente_para_plan(self, state: dict[str, Any], id_pm: int) -> dict[str, Any] | None:
        return MembershipsOperations(self.executor).get_promocion_vigente_para_plan(state, id_pm)

    def promociones_vigentes_publicas(self) -> list[dict[str, Any]]:
        return MembershipsOperations(self.executor).promociones_vigentes_publicas()

    def membresias(self) -> list[dict[str, Any]]:
        return MembershipsOperations(self.executor).membresias()

    def membresias_por_cliente(self, id_cliente: int) -> list[dict[str, Any]]:
        return MembershipsOperations(self.executor).membresias_por_cliente(id_cliente)

    def crear_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        return MembershipsOperations(self.executor).crear_membresia(payload)

    def registrar_cliente_con_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        return MembershipsOperations(self.executor).registrar_cliente_con_membresia(payload)

    def activar_membresia_cliente(self, id_cliente: int) -> dict[str, Any]:
        return MembershipsOperations(self.executor).activar_membresia_cliente(id_cliente)

    def get_usuario(self, id_usuario: Any) -> dict[str, Any] | None:
        return AccountsOperations(self.executor).get_usuario(id_usuario)

    def get_usuario_by_email(self, email: str) -> dict[str, Any] | None:
        return AccountsOperations(self.executor).get_usuario_by_email(email)

    def usuarios(self) -> list[dict[str, Any]]:
        return AccountsOperations(self.executor).usuarios()

    def usuarios_normalized(self) -> list[dict[str, Any]]:
        return AccountsOperations(self.executor).usuarios_normalized()

    def upsert_usuario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return AccountsOperations(self.executor).upsert_usuario(payload)

    def delete_usuario(self, id_usuario: Any) -> None:
        return AccountsOperations(self.executor).delete_usuario(id_usuario)

    def clientes(self) -> list[dict[str, Any]]:
        return AccountsOperations(self.executor).clientes()

    def clientes_normalized(self) -> list[dict[str, Any]]:
        return AccountsOperations(self.executor).clientes_normalized()

    def upsert_cliente(self, payload: dict[str, Any]) -> dict[str, Any]:
        return AccountsOperations(self.executor).upsert_cliente(payload)

    def get_cliente(self, id_cliente: int) -> dict[str, Any] | None:
        return AccountsOperations(self.executor).get_cliente(id_cliente)

    def get_cliente_by_dni(self, dni: str) -> dict[str, Any] | None:
        return AccountsOperations(self.executor).get_cliente_by_dni(dni)

    def get_cliente_by_email(self, email: str) -> dict[str, Any] | None:
        return AccountsOperations(self.executor).get_cliente_by_email(email)

    def get_account_by_google_sub(self, subject: str) -> tuple[str, dict[str, Any]] | None:
        return AccountsOperations(self.executor).get_account_by_google_sub(subject)

    def link_google_account(self, kind: str, account_id: str, subject: str) -> dict[str, Any]:
        return AccountsOperations(self.executor).link_google_account(kind, account_id, subject)

    def authenticate_usuario_password(self, correo: str, password: str) -> dict[str, Any] | None:
        return AccountsOperations(self.executor).authenticate_usuario_password(correo, password)

    def authenticate_cliente_password(self, correo: str, password: str) -> dict[str, Any] | None:
        return AccountsOperations(self.executor).authenticate_cliente_password(correo, password)

    def delete_cliente(self, id_cliente: int) -> None:
        return AccountsOperations(self.executor).delete_cliente(id_cliente)

    def registrar_cliente_publico(self, payload: dict[str, Any], *, origen_registro: str='PUBLICO') -> dict[str, Any]:
        return AccountsOperations(self.executor).registrar_cliente_publico(payload, origen_registro=origen_registro)

    def confirmar_pago_cliente_publico(self, id_cliente: int, payload: dict[str, Any]) -> dict[str, Any]:
        return AccountsOperations(self.executor).confirmar_pago_cliente_publico(id_cliente, payload)

    def confirmar_pago_manual_cliente(self, id_cliente: int) -> dict[str, Any]:
        return AccountsOperations(self.executor).confirmar_pago_manual_cliente(id_cliente)

    def tickets(self) -> list[dict[str, Any]]:
        return ConfigurationOperations(self.executor).tickets()

    def upsert_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        return ConfigurationOperations(self.executor).upsert_ticket(payload)

    def configuracion_gimnasio(self) -> dict[str, Any]:
        return ConfigurationOperations(self.executor).configuracion_gimnasio()

    def summary(self) -> dict[str, Any]:
        return ConfigurationOperations(self.executor).summary()

    def inventario(self) -> list[dict[str, Any]]:
        return InventoryOperations(self.executor).inventario()

    def get_item_inventario(self, id_item: int) -> dict[str, Any] | None:
        return InventoryOperations(self.executor).get_item_inventario(id_item)

    def upsert_inventario(self, payload: dict[str, Any], actor: Any=None) -> dict[str, Any]:
        return InventoryOperations(self.executor).upsert_inventario(payload, actor)

    def delete_inventario(self, id_item: int) -> dict[str, Any] | None:
        return InventoryOperations(self.executor).delete_inventario(id_item)

    def movimientos_inventario(self) -> list[dict[str, Any]]:
        return InventoryOperations(self.executor).movimientos_inventario()

    def registrar_movimiento_inventario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return InventoryOperations(self.executor).registrar_movimiento_inventario(payload)

    def actualizar_movimiento_inventario(self, id_mov: int, payload: dict[str, Any]) -> dict[str, Any]:
        return InventoryOperations(self.executor).actualizar_movimiento_inventario(id_mov, payload)

    def catalogo_rutina(self) -> list[dict[str, Any]]:
        return SchedulesOperations(self.executor).catalogo_rutina()

    def upsert_rutina(self, payload: dict[str, Any]) -> dict[str, Any]:
        return SchedulesOperations(self.executor).upsert_rutina(payload)

    def horarios(self) -> list[dict[str, Any]]:
        return SchedulesOperations(self.executor).horarios()

    def upsert_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return SchedulesOperations(self.executor).upsert_horario(payload)

    def horarios_servicio(self, solo_activos: bool=False) -> list[dict[str, Any]]:
        return SchedulesOperations(self.executor).horarios_servicio(solo_activos)

    def get_horario_servicio(self, id_horario_servicio: int) -> dict[str, Any] | None:
        return SchedulesOperations(self.executor).get_horario_servicio(id_horario_servicio)

    def upsert_horario_servicio(self, payload: dict[str, Any]) -> dict[str, Any]:
        return SchedulesOperations(self.executor).upsert_horario_servicio(payload)

    def delete_horario_servicio(self, id_horario_servicio: int) -> None:
        return SchedulesOperations(self.executor).delete_horario_servicio(id_horario_servicio)

    def matriculas_horario(self, id_cliente: int | None=None, dni: str | None=None, solo_activas: bool=False) -> list[dict[str, Any]]:
        return SchedulesOperations(self.executor).matriculas_horario(id_cliente, dni, solo_activas)

    def get_matricula_horario(self, id_matricula: int) -> dict[str, Any] | None:
        return SchedulesOperations(self.executor).get_matricula_horario(id_matricula)

    def asignar_rutina_matricula(self, id_matricula: int, id_rutina: int) -> dict[str, Any]:
        return SchedulesOperations(self.executor).asignar_rutina_matricula(id_matricula, id_rutina)

    def trainer_rutinas_cliente(self, dni: str) -> dict[str, Any]:
        return SchedulesOperations(self.executor).trainer_rutinas_cliente(dni)

    def registrar_progreso_rutina(self, id_matricula: int, payload: dict[str, Any]) -> dict[str, Any]:
        return SchedulesOperations(self.executor).registrar_progreso_rutina(id_matricula, payload)

    def trainer_overview(self) -> dict[str, Any]:
        return SchedulesOperations(self.executor).trainer_overview()

    def cancelar_matricula_horario(self, id_matricula: int, id_cliente: int | None=None) -> None:
        return SchedulesOperations(self.executor).cancelar_matricula_horario(id_matricula, id_cliente)

    def asistencia(self) -> list[dict[str, Any]]:
        return AttendanceOperations(self.executor).asistencia()

    def registrar_asistencia(self, id_cliente: int) -> dict[str, Any]:
        return AttendanceOperations(self.executor).registrar_asistencia(id_cliente)

    def registrar_asistencia_detallada(self, payload: dict[str, Any]) -> dict[str, Any]:
        return AttendanceOperations(self.executor).registrar_asistencia_detallada(payload)

    def registrar_entrada_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return AttendanceOperations(self.executor).registrar_entrada_horario(payload)

    def registrar_salida_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return AttendanceOperations(self.executor).registrar_salida_horario(payload)

    def actualizar_asistencia(self, id_asistencia: int, payload: dict[str, Any]) -> dict[str, Any]:
        return AttendanceOperations(self.executor).actualizar_asistencia(id_asistencia, payload)

    def eliminar_asistencia(self, id_asistencia: int) -> None:
        return AttendanceOperations(self.executor).eliminar_asistencia(id_asistencia)

    def registrar_asistencia_por_dni(self, dni: str) -> dict[str, Any]:
        return AttendanceOperations(self.executor).registrar_asistencia_por_dni(dni)
