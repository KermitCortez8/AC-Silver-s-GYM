from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies import get_current_user
from routes import attendance_routes
from services.attendance_service import AttendanceConflict, AttendanceService, LIMA
from services.local_gym_service import LocalGymService
from services.supabase_gym_service import SupabaseGymService


@pytest.fixture
def attendance():
    gym = LocalGymService()
    gym.state.update(
        clientes=[{"id_cliente": i, "nombre": f"Cliente {i}", "dni": str(i) * 8, "estado": "ACTIVO"}
                  for i in (1, 2)],
        membresia=[{"id_membresia": i, "id_cliente": i, "estado": "ACTIVA", "estado_pago": "PAGADO",
                    "fecha_inicio": "2026-10-01", "fecha_fin": "2026-10-31"} for i in (1, 2)],
        asistencia=[], matriculas_horario=[], horarios_servicio=[],
        configuracion_gimnasio={"capacidad_total": 2},
    )
    current = [datetime(2026, 10, 7, 10, 30, tzinfo=LIMA)]
    service = AttendanceService(gym, clock=lambda: current[0])
    service.advance = lambda: current.__setitem__(0, current[0] + timedelta(hours=1))
    return service


@pytest.fixture
def admin():
    return SimpleNamespace(role="admin", id="admin", id_usuario="SGUSU001", name="Recepción", id_cliente=None)


def enter(service, actor, dni="11111111"):
    return service.enter_general(dni, str(uuid4()), actor)


def enroll(service):
    service.gym.state["matriculas_horario"] = [{"id_matricula": 1, "id_cliente": 1,
                                               "id_horario_servicio": 1, "estado": "ACTIVA"}]
    service.gym.state["horarios_servicio"] = [{"id_horario_servicio": 1, "dia": "miercoles",
                                             "hora_inicio": "10:00", "hora_fin": "14:00",
                                             "servicio": "fitness", "activo": True}]


def test_entry_without_enrollment_and_exit_use_server_clock(attendance, admin):
    lookup = attendance.lookup("11111111")
    assert lookup["horarios"] == []
    assert lookup["general"]["puede_entrar"]
    row = enter(attendance, admin)
    assert (row["tipo"], row["id_matricula"], row["id_horario_servicio"]) == ("general", None, None)
    assert (row["fecha"], row["hora_entrada"], row["estado"]) == ("2026-10-07", "10:30:00", "dentro")
    attendance.advance()
    closed = attendance.exit(row["id_asistencia"], admin)
    assert (closed["hora_salida"], closed["estado"], closed["version"]) == ("11:30:00", "completada", 2)
    attendance.advance()
    assert attendance.exit(row["id_asistencia"], admin)["hora_salida"] == "11:30:00"


def test_retries_do_not_duplicate_even_after_exit(attendance, admin):
    request_id = str(uuid4())
    first = attendance.enter_general("11111111", request_id, admin)
    assert attendance.enter_general("11111111", request_id, admin)["id_asistencia"] == first["id_asistencia"]
    attendance.advance()
    attendance.exit(first["id_asistencia"], admin)
    assert attendance.enter_general("11111111", request_id, admin)["estado"] == "completada"
    assert len(attendance.gym.state["asistencia"]) == 1
    assert enter(attendance, admin)["id_asistencia"] != first["id_asistencia"]


@pytest.mark.parametrize("field,value", [("estado", "INACTIVO"), ("estado_pago", "PENDIENTE"),
                                          ("fecha_fin", "2026-10-06"), ("fecha_inicio", "2026-10-08")])
def test_entry_requires_current_paid_membership(attendance, admin, field, value):
    attendance.gym.state["membresia"][0][field] = value
    with pytest.raises(ValueError, match="membresía activa, pagada y vigente"):
        enter(attendance, admin)
    assert not attendance.lookup("11111111")["general"]["puede_entrar"]
    assert attendance.gym.state["asistencia"] == []


def test_entry_requires_active_account_and_known_dni(attendance, admin):
    with pytest.raises(ValueError, match="No se encontró"):
        enter(attendance, admin, "99999999")
    attendance.gym.state["clientes"][0]["estado"] = "INACTIVO"
    with pytest.raises(ValueError, match="activada"):
        enter(attendance, admin)


@pytest.mark.parametrize("first_kind", ["general", "horario"])
def test_open_entry_blocks_other_kind(attendance, admin, first_kind):
    enroll(attendance)
    if first_kind == "general":
        row = enter(attendance, admin)
        with pytest.raises(ValueError, match="entrada sin salida"):
            attendance.enter({"id_matricula": 1}, admin)
    else:
        row = attendance.enter({"id_matricula": 1}, admin)
        with pytest.raises(ValueError, match="entrada sin salida"):
            enter(attendance, admin)
    assert attendance.lookup("11111111")["general"]["asistencia_abierta"]["id_asistencia"] == row["id_asistencia"]
    attendance.exit(row["id_asistencia"], admin)
    assert attendance.lookup("11111111")["general"]["puede_entrar"]


def test_capacity_is_shared_by_general_and_schedule_entries(attendance, admin):
    enroll(attendance)
    attendance.gym.state["configuracion_gimnasio"]["capacidad_total"] = 1
    row = attendance.enter({"id_matricula": 1}, admin)
    with pytest.raises(ValueError, match="aforo"):
        enter(attendance, admin, "22222222")
    summary = attendance.summary(admin)
    assert (summary["dentro"], summary["capacidad"], summary["disponibles"]) == (1, 1, 0)
    attendance.exit(row["id_asistencia"], admin)
    enter(attendance, admin, "22222222")
    assert attendance.summary(admin)["entradas"] == 2


def test_stale_parallel_writes_cannot_exceed_capacity(attendance, admin):
    attendance.gym.state["configuracion_gimnasio"]["capacidad_total"] = 1
    first = enter(attendance, admin)
    template = deepcopy(attendance.gym.state["asistencia"][0])
    attendance.gym.state["asistencia"].clear()

    def attempt(client_id):
        row = {**template, "id_cliente": client_id, "id_cliente_num": client_id, "id_membresia": client_id}
        row.pop("id_asistencia")
        try:
            return attendance.save(row, None, "entrada", admin, request_id=str(uuid4()))
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, [1, 2]))
    assert sum(result is not None for result in results) == 1
    assert attendance.summary(admin)["dentro"] == 1
    assert first["tipo"] == "general"


def test_history_filters_and_client_privacy(attendance, admin):
    general = enter(attendance, admin)
    attendance.exit(general["id_asistencia"], admin)
    enroll(attendance)
    attendance.enter({"id_matricula": 1}, admin)
    enter(attendance, admin, "22222222")
    assert len(attendance.records(admin, tipo="general")) == 2
    assert len(attendance.records(admin, tipo="horario")) == 1
    assert len(attendance.records(admin, servicio="gimnasio", dni="11111111")) == 1
    user = SimpleNamespace(role="user", id_cliente=1)
    rows = attendance.records(user, tipo="general")
    assert len(rows) == 1
    assert "auditoria" not in rows[0] and "id_usuario_registra" not in rows[0]


def test_general_corrections_and_annulment_remain_audited(attendance, admin):
    row = enter(attendance, admin)
    changed = attendance.correct(row["id_asistencia"], {"version": 1, "motivo": "Corregir hora",
                                 "fecha": "2026-10-07", "hora_entrada": "10:00:00",
                                 "hora_salida": "", "fecha_salida": None}, admin)
    assert changed["tipo"] == "general" and changed["version"] == 2
    with pytest.raises(AttendanceConflict):
        attendance.correct(row["id_asistencia"], {"version": 1, "motivo": "Registro duplicado"}, admin, annul=True)
    annulled = attendance.correct(row["id_asistencia"], {"version": 2, "motivo": "Registro duplicado"}, admin, annul=True)
    assert annulled["estado"] == "anulada" and len(annulled["auditoria"]) == 3
    assert attendance.summary(admin)["dentro"] == 0
    assert attendance.records(SimpleNamespace(role="user", id_cliente=1)) == []


def test_supabase_mapping_preserves_general_visit(attendance, admin):
    row = enter(attendance, admin)
    remote = SupabaseGymService.__new__(SupabaseGymService)
    payload = remote._attendance_to_remote(row)
    mapped = remote._map_attendance(payload)
    assert payload["servicio"] == "gimnasio" and payload["id_matricula"] is None
    assert attendance.present(mapped)["tipo"] == "general"
    assert mapped["auditoria"][0]["request_id"] == row["auditoria"][0]["request_id"]


@pytest.fixture
def api(attendance, admin):
    app = FastAPI()
    app.include_router(attendance_routes.router)
    app.dependency_overrides[attendance_routes.service] = lambda: attendance
    app.dependency_overrides[get_current_user] = lambda: admin
    return TestClient(app), app


def test_general_api_validates_payload_and_preserves_schedule_endpoint(api):
    client, _ = api
    assert client.post("/asistencia/general/entrada", json={"dni": "11111111"}).status_code == 422
    assert client.post("/asistencia/general/entrada", json={"dni": "invalid", "request_id": str(uuid4())}).status_code == 422
    assert client.post("/asistencia/entrada", json={"dni": "11111111"}).status_code == 400
    response = client.post("/asistencia/general/entrada", json={"dni": "11111111", "request_id": str(uuid4())})
    assert response.status_code == 200 and response.json()["tipo"] == "general"
    assert client.get("/asistencia/historial?tipo=general").json()["total"] == 1
    assert client.get("/asistencia/historial?tipo=horario").json()["total"] == 0


@pytest.mark.parametrize("role", ["user", "trainer", "staff"])
def test_only_admin_can_register_general_visit(api, role):
    client, app = api
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role=role, id_cliente=1)
    response = client.post("/asistencia/general/entrada", json={"dni": "11111111", "request_id": str(uuid4())})
    assert response.status_code == 403


def test_client_week_contains_only_own_general_visits(api, attendance, admin):
    enter(attendance, admin)
    enter(attendance, admin, "22222222")
    client, app = api
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role="user", id_cliente=1)
    result = client.get("/asistencia/mi-semana?inicio=2026-10-07").json()
    assert result["visitas"] == 1 and len(result["generales"]) == 1
    assert result["generales"][0]["cliente_dni"] == "11111111"
    assert "auditoria" not in result["generales"][0]
