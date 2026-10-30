"""Tabla de horarios, lista de matriculados y límite de salida en Perú."""
from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

import pytest

from tests.test_general_attendance import attendance, admin, api, enroll
from application.services.attendance_service import LIMA
from domain.services.attendance_status import LATE_EXIT_MESSAGE
from infrastructure.repositories.attendance_history_repository import AttendanceHistoryRepository
from infrastructure.supabase_client import RowsPage
from application.read_models import AttendanceCriteria, PageRequest
from infrastructure.repositories.mappers.attendance import _attendance_to_remote, _map_attendance
from infrastructure.repositories.attendance_repository import AttendanceRepository
from infrastructure.repositories.gym_cache import GymCache


def set_time(service, hour, day="2026-10-07"):
    service.clock = lambda: datetime.fromisoformat(f"{day}T{hour}-05:00")


def test_tabla_y_lista_solo_incluyen_matriculas_activas_del_horario(attendance):
    enroll(attendance)
    state = attendance.gym.state
    state["horarios_servicio"].extend([
        {**state["horarios_servicio"][0], "id_horario_servicio": 2, "dia": "jueves"},
        {**state["horarios_servicio"][0], "id_horario_servicio": 3, "activo": False},
    ])
    state["matriculas_horario"].extend([
        {"id_matricula": 2, "id_cliente": 2, "id_horario_servicio": 1, "estado": "CANCELADA"},
        {"id_matricula": 3, "id_cliente": 2, "id_horario_servicio": 2, "estado": "ACTIVA", "fecha_clase": "2026-10-08"},
    ])
    catalog = attendance.schedules()
    assert [s["id_horario_servicio"] for s in catalog["horarios"]] == [1, 2]
    assert [s["matriculados"] for s in catalog["horarios"]] == [1, 1]
    roster = attendance.roster(1)
    assert roster["fecha"] == "2026-10-07"
    assert [s["cliente"]["dni"] for s in roster["clientes"]] == ["11111111"]
    assert roster["clientes"][0]["puede_entrar"]
    assert "password_hash" not in roster["clientes"][0]["cliente"]
    assert attendance.roster(2)["clientes"] == []
    assert "el día de esta sesión" in attendance.roster(2, "2026-10-08")["clientes"][0]["motivo"]
    with pytest.raises(ValueError, match="no está disponible"):
        attendance.roster(3)


@pytest.mark.parametrize("hour,allowed", [("09:59:59", False), ("10:00:00", True),
    ("13:59:59", True), ("14:00:00", False)])
def test_lista_informa_si_la_entrada_esta_dentro_del_horario(attendance, hour, allowed):
    enroll(attendance)
    set_time(attendance, hour)
    student = attendance.roster(1)["clientes"][0]
    assert student["puede_entrar"] is allowed
    assert bool(student["motivo"]) is not allowed


@pytest.mark.parametrize("hour,status", [("10:30:00", "completada"), ("14:30:00", "completada"),
    ("15:00:00", "completada"), ("15:00:01", "incompleta"), ("23:59:59", "incompleta")])
def test_salida_se_guarda_y_superar_una_hora_deja_asistencia_incompleta(attendance, admin, hour, status):
    enroll(attendance)
    row = attendance.enter({"id_matricula": 1}, admin)
    assert row["limite_salida"] == "2026-10-07T15:00:00-05:00"
    set_time(attendance, hour)
    saved = attendance.exit(row["id_asistencia"], admin)
    assert saved["estado"] == status
    assert saved["hora_salida"] == hour
    assert saved["salida_tardia"] is (status == "incompleta")
    assert saved["aviso"] == (LATE_EXIT_MESSAGE if status == "incompleta" else "")
    assert saved["auditoria"][-1]["accion"] == "salida"
    assert attendance.summary(admin)["dentro"] == 0
    # Reintento y consultas posteriores conservan la primera salida.
    set_time(attendance, "23:59:59")
    assert attendance.exit(row["id_asistencia"], admin)["hora_salida"] == hour
    assert attendance.records(admin)[0]["estado"] == status


def test_falta_de_salida_pasa_a_incompleta_sin_inventar_hora_ni_dejar_de_contar_aforo(attendance, admin):
    enroll(attendance)
    row = attendance.enter({"id_matricula": 1}, admin)
    set_time(attendance, "15:00:00")
    assert attendance.roster(1)["clientes"][0]["asistencia"]["estado"] == "dentro"
    set_time(attendance, "15:00:01")
    pending = attendance.roster(1)["clientes"][0]["asistencia"]
    assert pending["estado"] == "incompleta" and pending["aviso"] == LATE_EXIT_MESSAGE
    assert not pending["hora_salida"]
    assert attendance.gym.state["asistencia"][0]["version"] == 1
    assert attendance.summary(admin)["dentro"] == 1
    assert attendance.records(admin, estado="dentro") == []
    assert attendance.records(admin, estado="completada") == []
    assert attendance.records(admin, estado="incompleta")[0]["id_asistencia"] == row["id_asistencia"]


def test_limite_original_sobrevive_a_edicion_del_horario_y_recarga(attendance, admin):
    enroll(attendance)
    row = attendance.enter({"id_matricula": 1}, admin)
    mapped = _map_attendance(_attendance_to_remote(row))
    assert mapped["limite_salida"] == row["limite_salida"]
    attendance.gym.state["asistencia"][0] = mapped
    attendance.gym.state["horarios_servicio"][0]["hora_fin"] = "20:00"
    set_time(attendance, "15:00:01")
    saved = attendance.exit(row["id_asistencia"], admin)
    assert saved["estado"] == "incompleta"
    assert _map_attendance(_attendance_to_remote(saved))["salida_tardia"]


def test_limite_y_salida_cruzan_medianoche(attendance, admin):
    enroll(attendance)
    attendance.gym.state["horarios_servicio"][0].update(hora_inicio="22:30", hora_fin="23:30")
    set_time(attendance, "23:00:00")
    row = attendance.enter({"id_matricula": 1}, admin)
    assert row["limite_salida"] == "2026-10-08T00:30:00-05:00"
    set_time(attendance, "00:30:01", "2026-10-08")
    saved = attendance.exit(row["id_asistencia"], admin)
    assert saved["estado"] == "incompleta" and saved["fecha_salida"] == "2026-10-08"


def test_cliente_solo_consulta_su_incompleta_sin_auditoria(attendance, admin):
    enroll(attendance)
    attendance.enter({"id_matricula": 1}, admin)
    set_time(attendance, "15:00:01")
    rows = attendance.records(SimpleNamespace(role="user", id_cliente=1), estado="incompleta")
    assert len(rows) == 1 and "auditoria" not in rows[0]
    assert "id_usuario_registra" not in rows[0]
    assert attendance.records(SimpleNamespace(role="user", id_cliente=2), estado="incompleta") == []


@pytest.mark.parametrize("role", ["staff", "trainer", "user"])
def test_listas_de_matriculados_requieren_administrador(api, role):
    from presentation.dependencies import get_current_user
    client, app = api
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role=role, id_cliente=1)
    assert client.get("/asistencia/horarios").status_code == 403
    assert client.get("/asistencia/horarios/1/clientes").status_code == 403


def test_recorrido_http_lista_entrada_y_salida_incompleta(api, attendance):
    enroll(attendance)
    client, _ = api
    assert client.get("/asistencia/horarios").json()["horarios"][0]["matriculados"] == 1
    enrollment = client.get("/asistencia/horarios/1/clientes").json()["clientes"][0]["id_matricula"]
    row = client.post("/asistencia/entrada", json={"id_matricula": enrollment}).json()
    set_time(attendance, "15:00:01")
    response = client.post("/asistencia/salida", json={"id_asistencia": row["id_asistencia"]})
    assert response.status_code == 200 and response.json()["estado"] == "incompleta"
    assert response.json()["aviso"] == LATE_EXIT_MESSAGE
    history = client.get("/asistencia/historial?estado=incompleta").json()
    assert history["total"] == 1 and history["items"][0]["estado"] == "incompleta"


@pytest.mark.parametrize("status,condition", [("incompleta", "salida_tardia.eq.true"),
    ("dentro", "limite_salida.gte."), ("completada", "salida_tardia.eq.false")])
def test_estado_incompleto_se_filtra_en_persistencia_con_paginacion(status, condition):
    calls = []
    class Database:
        def select_page(self, table, filters, **kwargs):
            calls.append((table, filters, kwargs))
            return RowsPage([], 0)
    AttendanceHistoryRepository(Database()).page(AttendanceCriteria(client_id=1,
        status=status, at="2026-10-07T15:00:01-05:00"), PageRequest(2, 10))
    table, filters, bounds = calls[0]
    assert table == "ASISTENCIA" and filters["id_cliente"] == "in.(1)"
    assert bounds["offset"] == 10 and condition in filters["and"]
    assert "anulado.eq.false" in filters["and"]


def test_esquema_sin_migracion_018_rechaza_antes_de_escribir():
    class Database:
        def validate_columns(self, table, columns):
            assert table == "ASISTENCIA" and columns == {"limite_salida", "salida_tardia"}
            raise RuntimeError("Faltan columnas de migración 018")
        def rpc(self, *_args):
            pytest.fail("No debe escribir una asistencia que perdería su límite")
    with pytest.raises(RuntimeError, match="018"):
        AttendanceRepository(Database(), GymCache()).save_attendance({}, None, {})
