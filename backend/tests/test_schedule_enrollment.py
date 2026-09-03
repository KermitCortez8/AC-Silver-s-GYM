from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace
import threading
import unittest

from models.gym import MatriculaHorarioInput
from routes.gym_routes import create_matricula, delete_matricula, list_matriculas
from services.local_gym_service import LocalGymService
from services.supabase_gym_service import SupabaseGymService


def _schedule_service() -> LocalGymService:
    service = LocalGymService()
    today = date.today()
    service.state["clientes"] = [
        {"id_cliente": 1, "nombre": "Cliente Uno", "dni": "11111111"},
        {"id_cliente": 2, "nombre": "Cliente Dos", "dni": "22222222"},
    ]
    service.state["membresia"] = [
        {
            "id_membresia": client_id,
            "id_cliente": client_id,
            "estado": "Activa",
            "fecha_inicio": (today - timedelta(days=1)).isoformat(),
            "fecha_fin": (today + timedelta(days=30)).isoformat(),
        }
        for client_id in (1, 2)
    ]
    service.state["catalogo_rutina"] = [
        {
            "id_rutina": 7,
            "servicio": "fitness",
            "nombre_rutina": "Circuito funcional",
            "zonas_musculares": "Cuerpo completo",
            "color": "Azul",
        }
    ]
    service.state["horarios_servicio"] = [
        {
            "id_horario_servicio": 10,
            "servicio": "fitness",
            "id_rutina": 7,
            "codigo_dia": "LUN",
            "dia": "lunes",
            "hora_inicio": "08:00",
            "hora_fin": "09:00",
            "cupos": 1,
            "cupos_usados": 0,
            "activo": True,
        },
        {
            "id_horario_servicio": 11,
            "servicio": "fitness",
            "id_rutina": 7,
            "codigo_dia": "MAR",
            "dia": "martes",
            "hora_inicio": "08:00",
            "hora_fin": "09:00",
            "cupos": 5,
            "cupos_usados": 0,
            "activo": False,
        },
    ]
    service.state["matriculas_horario"] = []
    return service


class ScheduleEnrollmentDomainTests(unittest.TestCase):
    def test_schedule_catalog_includes_exercise_and_available_slots(self) -> None:
        service = _schedule_service()
        schedules = service.horarios_servicio(solo_activos=True)

        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0]["rutina_nombre"], "Circuito funcional")
        self.assertEqual(schedules[0]["cupos_disponibles"], 1)
        self.assertFalse(schedules[0]["esta_lleno"])

    def test_enrollment_moves_class_to_client_schedule_and_respects_capacity(self) -> None:
        service = _schedule_service()
        created = service.matricular_cliente_horario(
            {"id_cliente": 1, "id_horario_servicio": 10}
        )

        self.assertEqual(created["id_cliente"], 1)
        self.assertEqual(created["rutina_nombre"], "Circuito funcional")
        self.assertEqual(service.horarios_servicio()[0]["cupos_disponibles"], 0)
        self.assertEqual(
            service.matriculas_horario(id_cliente=1, solo_activas=True),
            [created],
        )

        with self.assertRaisesRegex(ValueError, "ya esta matriculado"):
            service.matricular_cliente_horario(
                {"id_cliente": 1, "id_horario_servicio": 10}
            )

        with self.assertRaisesRegex(ValueError, "sin cupos"):
            service.matricular_cliente_horario(
                {"id_cliente": 2, "id_horario_servicio": 10}
            )

    def test_client_can_only_cancel_own_enrollment(self) -> None:
        service = _schedule_service()
        created = service.matricular_cliente_horario(
            {"id_cliente": 1, "id_horario_servicio": 10}
        )

        with self.assertRaisesRegex(PermissionError, "otro cliente"):
            service.cancelar_matricula_horario(
                created["id_matricula"], id_cliente=2
            )

        service.cancelar_matricula_horario(created["id_matricula"], id_cliente=1)
        self.assertEqual(
            service.matriculas_horario(id_cliente=1, solo_activas=True), []
        )
        self.assertEqual(service.horarios_servicio()[0]["cupos_disponibles"], 1)


class _RouteService:
    def __init__(self) -> None:
        self.last_list = None
        self.last_create = None
        self.last_cancel = None

    def matriculas_horario(self, **kwargs):
        self.last_list = kwargs
        return []

    def matricular_cliente_horario(self, payload):
        self.last_create = payload
        return payload

    def cancelar_matricula_horario(self, id_matricula, id_cliente=None):
        self.last_cancel = (id_matricula, id_cliente)


class ScheduleEnrollmentRouteTests(unittest.TestCase):
    def test_user_routes_always_use_client_from_authenticated_session(self) -> None:
        service = _RouteService()
        current_user = SimpleNamespace(role="user", id_cliente=1)

        list_matriculas(
            id_cliente=999,
            dni="99999999",
            gym_service=service,
            current_user=current_user,
        )
        self.assertEqual(
            service.last_list, {"id_cliente": 1, "solo_activas": True}
        )

        created = create_matricula(
            MatriculaHorarioInput(
                id_cliente=999,
                dni="99999999",
                id_horario_servicio=10,
            ),
            gym_service=service,
            current_user=current_user,
        )
        self.assertEqual(created["id_cliente"], 1)
        self.assertEqual(created["dni"], "")

        delete_matricula(50, gym_service=service, current_user=current_user)
        self.assertEqual(service.last_cancel, (50, 1))


class _SupabaseWithoutScheduleRpc:
    def __init__(self) -> None:
        self.inserted = None

    def rpc(self, function_name, body):
        raise RuntimeError("PGRST202: Could not find the function")

    def insert(self, table, body, return_representation=False):
        self.inserted = (table, body, return_representation)
        return [
            {
                "id_matricula": 90,
                "id_cliente": body["id_cliente"],
                "id_horario_servicio": body["id_horario_servicio"],
                "estado": body["estado"],
                "fecha_matricula": date.today().isoformat(),
            }
        ]


class SupabaseScheduleCompatibilityTests(unittest.TestCase):
    def test_enrollment_falls_back_to_identity_insert_before_migration_002(self) -> None:
        local_service = _schedule_service()
        service = SupabaseGymService.__new__(SupabaseGymService)
        service.lock = threading.Lock()
        service.state = local_service.state
        service.supabase = _SupabaseWithoutScheduleRpc()
        service._last_refresh_at = 0.0
        service._refresh_remote_state = lambda: None

        created = service.matricular_cliente_horario(
            {"id_cliente": 1, "id_horario_servicio": 10}
        )

        self.assertEqual(created["id_matricula"], 90)
        table, body, returns_rows = service.supabase.inserted
        self.assertEqual(table, "MATRICULAS_HORARIO")
        self.assertNotIn("id_matricula", body)
        self.assertTrue(returns_rows)


if __name__ == "__main__":
    unittest.main()
