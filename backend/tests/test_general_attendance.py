from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from presentation.dependencies import get_current_user
from presentation.routes import attendance_routes
from application.services.attendance_service import AttendanceConflict, AttendanceService, LIMA
from infrastructure.services.local_gym_service import LocalGymService
from infrastructure.services.supabase_gym_service import SupabaseGymService


@pytest.fixture
def attendance(monkeypatch):
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
    # Las consultas de membresías deben seguir también los cambios de service.clock.
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso',
                        lambda: service.now().date().isoformat())
    service.advance = lambda: current.__setitem__(0, current[0] + timedelta(hours=1))
    return service


@pytest.fixture
def admin():
    return SimpleNamespace(role="admin", id="admin", id_usuario="SGUSU001", name="Recepción", id_cliente=None)


def test_membership_queries_follow_the_attendance_clock(attendance):
    assert attendance.gym.get_cliente(1)["estado"] == "ACTIVO"
    assert attendance.membership(1, attendance.now().date().isoformat())

    attendance.clock = lambda: datetime(2026, 11, 1, 10, 30, tzinfo=LIMA)
    assert attendance.gym.get_cliente(1)["estado"] == "VENCIDA"
    assert attendance.membership(1, attendance.now().date().isoformat()) is None
    # La lectura proyecta el vencimiento sin cambiar el registro guardado.
    assert attendance.gym.state["clientes"][0]["estado"] == "ACTIVO"


def enter(service, actor, dni="11111111"):
    return service.enter_general(dni, str(uuid4()), actor)


def enroll(service):
    service.gym.state["matriculas_horario"] = [{"id_matricula": 1, "id_cliente": 1,
                                               "id_horario_servicio": 1, "estado": "ACTIVA", "fecha_clase": "2026-10-07"}]
    service.gym.state["horarios_servicio"] = [{"id_horario_servicio": 1, "dia": "miercoles",
                                             "hora_inicio": "10:00", "hora_fin": "14:00",
                                             "servicio": "fitness", "activo": True}]


@pytest.mark.parametrize("hour", ["14:00:00", "14:00:01", "23:59:59"])
def test_expired_class_rejects_entry_and_explains_why(attendance, admin, hour):
    enroll(attendance)
    attendance.clock = lambda: datetime.fromisoformat(f"2026-10-07T{hour}-05:00")
    before = deepcopy(attendance.gym.state)
    with pytest.raises(ValueError, match="La hora de esta clase ya pasó"):
        attendance.enter({"id_matricula": 1}, admin)
    schedule = attendance.lookup("11111111")["horarios"][0]
    assert schedule["puede_entrar"] is False
    assert schedule["asistencia"] is None
    assert "La hora de esta clase ya pasó" in schedule["motivo"]
    assert attendance.gym.state == before


@pytest.mark.parametrize("hour", ["10:00:00", "13:59:59"])
def test_class_accepts_entry_within_schedule(attendance, admin, hour):
    enroll(attendance)
    attendance.clock = lambda: datetime.fromisoformat(f"2026-10-07T{hour}-05:00")
    assert attendance.lookup("11111111")["horarios"][0]["puede_entrar"]
    assert attendance.enter({"id_matricula": 1}, admin)["hora_entrada"] == hour


def test_class_before_start_is_not_reported_as_expired(attendance, admin):
    enroll(attendance)
    attendance.clock = lambda: datetime(2026, 10, 7, 9, 59, 59, tzinfo=LIMA)
    schedule = attendance.lookup("11111111")["horarios"][0]
    assert not schedule["puede_entrar"]
    assert "La entrada se habilita de 10:00 a 14:00" in schedule["motivo"]
    with pytest.raises(ValueError, match="La entrada se habilita"):
        attendance.enter({"id_matricula": 1}, admin)
    assert attendance.gym.state["asistencia"] == []


def test_schedule_retry_and_exit_still_work_after_class_end(attendance, admin):
    enroll(attendance)
    row = attendance.enter({"id_matricula": 1}, admin)
    attendance.clock = lambda: datetime(2026, 10, 7, 14, 30, tzinfo=LIMA)
    assert attendance.enter({"id_matricula": 1}, admin)["id_asistencia"] == row["id_asistencia"]
    assert len(attendance.gym.state["asistencia"]) == 1
    assert attendance.exit(row["id_asistencia"], admin)["hora_salida"] == "14:30:00"


def test_class_uses_lima_server_time_instead_of_submitted_time(attendance, admin):
    enroll(attendance)
    # 19:00 UTC corresponde al cierre de las 14:00 en Perú.
    attendance.clock = lambda: datetime.fromisoformat("2026-10-07T19:00:00+00:00")
    with pytest.raises(ValueError, match="La hora de esta clase ya pasó"):
        attendance.enter({"id_matricula": 1, "fecha": "2026-10-07", "hora_entrada": "10:30:00"}, admin)
    assert attendance.gym.state["asistencia"] == []


def test_class_expiring_between_lookup_and_entry_is_rejected(attendance, admin):
    enroll(attendance)
    assert attendance.lookup("11111111")["horarios"][0]["puede_entrar"]
    attendance.clock = lambda: datetime(2026, 10, 7, 14, tzinfo=LIMA)
    with pytest.raises(ValueError, match="La hora de esta clase ya pasó"):
        attendance.enter({"id_matricula": 1}, admin)
    assert attendance.gym.state["asistencia"] == []


def test_transaction_revalidates_class_expiration(attendance, admin):
    enroll(attendance)
    row = attendance.enter({"id_matricula": 1}, admin)
    row.pop("id_asistencia")
    attendance.gym.state["asistencia"].clear()
    attendance.clock = lambda: datetime(2026, 10, 7, 14, tzinfo=LIMA)
    with pytest.raises(ValueError, match="La hora de esta clase ya pasó"):
        attendance.save(row, None, "entrada", admin)
    assert attendance.gym.state["asistencia"] == []


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


@pytest.mark.parametrize("path,payload", [
    ("/asistencia/entrada", {"id_matricula": 1}),
    ("/asistencia/checkin", {"id_cliente": 1}),
    ("/asistencia/checkin-dni", {"dni": "11111111"}),
])
def test_expired_class_api_returns_error_without_saving(api, attendance, path, payload):
    enroll(attendance)
    attendance.clock = lambda: datetime(2026, 10, 7, 14, tzinfo=LIMA)
    client, _ = api
    response = client.post(path, json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "La hora de esta clase ya pasó. No se puede registrar la asistencia."
    assert attendance.gym.state["asistencia"] == []


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


def test_general_tres_horas_exactas_admiten_salida_real(attendance, admin):
    row = enter(attendance, admin)
    assert row['limite_salida'] == '2026-10-07T13:30:00-05:00'
    attendance.clock = lambda: datetime(2026, 10, 7, 13, 30, tzinfo=LIMA)
    assert attendance.summary(admin)['dentro'] == 1
    saved = attendance.exit(row['id_asistencia'], admin)
    assert saved['estado'] == 'completada' and not saved['cierre_automatico']


def test_general_se_cierra_incompleta_y_libera_aforo_al_superar_tres_horas(attendance, admin):
    request = str(uuid4())
    row = attendance.enter_general('11111111', request, admin)
    attendance.clock = lambda: datetime(2026, 10, 7, 13, 30, 1, tzinfo=LIMA)
    summary = attendance.summary(admin)
    assert summary['dentro'] == 0 and summary['salidas'] == 1
    assert summary['pendientes'] == []
    closed = attendance.records(admin, estado='incompleta')[0]
    assert closed['hora_salida'] == '13:30:00' and closed['fecha_salida'] == '2026-10-07'
    assert closed['cierre_automatico'] and closed['estado_asistencia'] == 'incompleta'
    assert closed['version'] == 2 and closed['auditoria'][-1]['accion'] == 'cierre_automatico'
    assert attendance.records(admin, estado='completada') == []
    assert attendance.exit(row['id_asistencia'], admin)['hora_salida'] == '13:30:00'
    assert attendance.enter_general('11111111', request, admin)['id_asistencia'] == row['id_asistencia']
    lookup = attendance.lookup('11111111')['general']
    assert lookup['asistencia_abierta'] is None and lookup['ultima_visita']['cierre_automatico']
    assert lookup['puede_entrar']
    assert enter(attendance, admin)['id_asistencia'] != row['id_asistencia']


def test_cierre_general_cruza_medianoche_y_conserva_privacidad(attendance, admin):
    attendance.clock = lambda: datetime(2026, 10, 7, 22, 15, tzinfo=LIMA)
    enter(attendance, admin)
    attendance.clock = lambda: datetime(2026, 10, 8, 1, 15, 1, tzinfo=LIMA)
    user = SimpleNamespace(role='user', id_cliente=1)
    rows = attendance.records(user)
    assert rows[0]['fecha_salida'] == '2026-10-08' and rows[0]['hora_salida'] == '01:15:00'
    assert rows[0]['cierre_automatico'] and rows[0]['estado'] == 'incompleta'
    assert 'auditoria' not in rows[0]
    assert attendance.records(SimpleNamespace(role='user', id_cliente=2)) == []


def test_cierre_general_admite_correccion_documentada_de_salida_real(attendance, admin):
    row = enter(attendance, admin)
    attendance.clock = lambda: datetime(2026, 10, 7, 14, 0, tzinfo=LIMA)
    closed = attendance.exit(row['id_asistencia'], admin)
    corrected = attendance.correct(row['id_asistencia'], {
        'version': closed['version'], 'motivo': 'La salida real fue verificada.',
        'fecha': row['fecha'], 'hora_entrada': row['hora_entrada'],
        'hora_salida': '12:00:00', 'fecha_salida': row['fecha'],
    }, admin)
    assert corrected['estado'] == 'completada' and not corrected['cierre_automatico']
    assert any(e['accion'] == 'cierre_automatico' for e in corrected['auditoria'])


def test_reconciliacion_observa_cierre_del_cron_aunque_ya_no_haya_vencidas():
    from infrastructure.repositories.gym_repository import SupabaseGymRepository
    repository = object.__new__(SupabaseGymRepository)
    class Database:
        def rpc(self, name, body):
            assert name == 'marcar_asistencias_incompletas' and body == {}
            return 0
    repository.supabase = Database()
    repository.cache.resource_refreshed_at.update(asistencia=10.0, clientes=10.0)
    assert repository.reconcile_attendance(datetime(2026, 10, 7, 13, 30, 1, tzinfo=LIMA)) == 0
    assert 'asistencia' not in repository.cache.resource_refreshed_at
    assert repository.cache.resource_refreshed_at['clientes'] == 10.0
