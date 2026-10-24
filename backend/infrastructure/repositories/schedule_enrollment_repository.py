"""Persistencia específica de enroll, independiente de la fachada global."""
from typing import Any
from application.errors import SchemaNotReady
from infrastructure.http_transport import database_code
from domain.services.gym_domain_service import GymDomainService
from infrastructure.repositories.enrollment_errors import raise_schedule_enrollment_error
from infrastructure.repositories.mappers import schedules

from infrastructure.repositories.gym_cache import GymCache
from infrastructure.repositories.gym_snapshot_reader import GymSnapshotReader


class ScheduleEnrollmentRepository:
    RESOURCES = ("clientes", "membresia", "catalogo_rutina", "horarios_servicio", "matriculas_horario")

    def __init__(self, database, cache: GymCache, reader: GymSnapshotReader):
        self.database, self.cache, self.reader = database, cache, reader

    def enroll(self, payload: dict[str, Any]) -> dict[str, Any]:

        """Crea la matrícula únicamente mediante la operación atómica de la base."""
        with self.cache.lock:
            # Una matrícula siempre parte del estado remoto más reciente, incluso
            # si la caché general todavía no alcanzó su TTL.
            self.reader.load(self.RESOURCES)
            if payload.get("dni"):
                cliente = GymDomainService(self.cache.state).get_cliente_by_dni(str(payload.get("dni") or "").strip())
                if not cliente:
                    raise ValueError("Cliente no encontrado")
                id_cliente = int(cliente.get("id_cliente", 0) or 0)
            else:
                id_cliente = GymDomainService(self.cache.state).parse_client_id(payload.get("id_cliente"))

            id_horario = int(payload.get("id_horario_servicio", 0) or 0)
            if id_cliente <= 0:
                raise ValueError("Cliente no encontrado")
            if id_horario <= 0:
                raise ValueError("Horario no disponible")

            GymDomainService(self.cache.state).validate_enrollment(id_cliente, id_horario)

            admin_id = str(payload.get("_admin_id") or "")
            rpc_name = "matricular_cliente_horario_admin" if admin_id else "matricular_cliente_horario"
            rpc_body: dict[str, Any] = {"p_id_cliente": id_cliente, "p_id_horario_servicio": id_horario}
            if admin_id:
                rpc_body["p_admin_id"] = admin_id
            try:
                created = self.database.rpc(rpc_name, rpc_body)
            except RuntimeError as error:
                if database_code(error) in {"PGRST202", "42883"}:
                    if admin_id:
                        raise SchemaNotReady("006_schedule_email_notifications.sql") from error
                    raise SchemaNotReady("002_harden_schedule_enrollment.sql") from error
                else:
                    raise_schedule_enrollment_error(error)

            if isinstance(created, list):
                created = created[0] if created else None
            if not isinstance(created, dict):
                raise RuntimeError("Supabase no devolvió la matrícula creada")

            enrollment = schedules._map_schedule_enrollment(created)
            if int(enrollment.get("id_matricula", 0) or 0) <= 0:
                raise RuntimeError("Supabase devolvió una matrícula sin identificador")

            self.cache.state.setdefault("matriculas_horario", [])
            self.cache.state["matriculas_horario"] = [
                row
                for row in self.cache.state["matriculas_horario"]
                if int(row.get("id_matricula", 0) or 0) != int(enrollment["id_matricula"])
            ]
            self.cache.state["matriculas_horario"].insert(0, enrollment)
            GymDomainService(self.cache.state).recount_schedule()
            # La siguiente petición recarga también las matrículas creadas por
            # cualquier otra instancia del backend.
            self.cache.last_refresh_at = 0.0
            for resource in ("horarios_servicio", "matriculas_horario"):
                self.cache.resource_refreshed_at.pop(resource, None)

            result = next(
                row
                for row in GymDomainService(self.cache.state).matriculas_horario(id_cliente=id_cliente, solo_activas=True)
                if int(row.get("id_matricula", 0) or 0) == int(enrollment["id_matricula"])
            )
            if admin_id:
                result["_email_notification_queued"] = True
            return result
