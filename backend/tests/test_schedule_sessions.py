"""Regresión: se repite la programación, nunca la reserva de un cliente."""
from copy import deepcopy
from datetime import date, datetime, timedelta

import pytest
from pydantic import ValidationError

from domain.models.gym import MatriculaHorarioInput
from domain.services.schedule_sessions import enrollment_session, next_session
from infrastructure.repositories.mappers.schedules import _map_schedule_enrollment, _schedule_enrollment_to_remote
from tests.test_general_attendance import attendance, admin, api, enroll
from tests.test_schedule_enrollment import _schedule_service


def test_mismo_cliente_puede_reservar_dos_semanas_sin_compartir_cupos_ni_cancelacion():
    gym = _schedule_service()
    first = next_session(gym.state["horarios_servicio"][0], date.today())
    second = (date.fromisoformat(first) + timedelta(days=7)).isoformat()
    a = gym.matricular_cliente_horario(dict(id_cliente=1, id_horario_servicio=10, fecha_clase=first))
    with pytest.raises(ValueError, match="ya esta matriculado"):
        gym.matricular_cliente_horario(dict(id_cliente=1, id_horario_servicio=10, fecha_clase=first))
    with pytest.raises(ValueError, match="sin cupos"):
        gym.matricular_cliente_horario(dict(id_cliente=2, id_horario_servicio=10, fecha_clase=first))
    b = gym.matricular_cliente_horario(dict(id_cliente=1, id_horario_servicio=10, fecha_clase=second))
    assert a["id_matricula"] != b["id_matricula"]
    assert gym.horarios_servicio()[0]["ocupacion_por_fecha"] == {first: 1, second: 1}
    gym.cancelar_matricula_horario(a["id_matricula"], id_cliente=1)
    assert gym.horarios_servicio()[0]["ocupacion_por_fecha"] == {second: 1}
    assert gym.matriculas_horario(id_cliente=1, solo_activas=True)[0]["fecha_clase"] == second


def test_otra_semana_no_hereda_reserva_y_permite_otro_cliente():
    gym = _schedule_service()
    first = next_session(gym.state["horarios_servicio"][0], date.today())
    second = (date.fromisoformat(first) + timedelta(days=7)).isoformat()
    gym.matricular_cliente_horario(dict(id_cliente=1, id_horario_servicio=10, fecha_clase=first))
    gym.matricular_cliente_horario(dict(id_cliente=2, id_horario_servicio=10, fecha_clase=second))
    assert len(gym.matriculas_horario(solo_activas=True)) == 2


@pytest.mark.parametrize("value", ["2026-02-30", "fecha", "2020-01-06"])
def test_rechaza_fechas_invalidas_o_pasadas_sin_crear_matricula(value):
    gym = _schedule_service()
    with pytest.raises(ValueError):
        gym.matricular_cliente_horario(dict(id_cliente=1, id_horario_servicio=10, fecha_clase=value))
    assert gym.state["matriculas_horario"] == []


def test_rechaza_dia_incorrecto_y_membresia_que_no_cubre_la_sesion():
    gym = _schedule_service()
    monday = date.fromisoformat(next_session(gym.state["horarios_servicio"][0], date.today()))
    for selected, message in [((monday + timedelta(days=1)).isoformat(), "día del horario"),
                              ((monday + timedelta(days=70)).isoformat(), "membresía no cubre")]:
        with pytest.raises(ValueError, match=message):
            gym.matricular_cliente_horario(dict(id_cliente=1, id_horario_servicio=10, fecha_clase=selected))
    with pytest.raises(ValidationError):
        MatriculaHorarioInput(id_cliente=1, id_horario_servicio=10, fecha_clase="2026-02-30")


def test_fecha_no_se_pierde_al_normalizar_mapear_o_recargar():
    row = dict(id_matricula=1, id_cliente=1, id_horario_servicio=10, fecha_matricula="2026-09-01",
               fecha_clase="2026-09-14", estado="ACTIVA")
    assert _map_schedule_enrollment(_schedule_enrollment_to_remote(row))["fecha_clase"] == "2026-09-14"
    schedule = {"dia": "lunes"}
    assert enrollment_session({"fecha_matricula": "2026-09-01"}, schedule) == "2026-09-07"
    assert enrollment_session({}, schedule) == ""
    assert enrollment_session({"fecha_clase": "2026-02-30", "fecha_matricula": "2026-09-01"}, schedule) == ""


def test_asistencia_no_arrastra_clientes_ni_registros_a_la_siguiente_semana(attendance, admin):
    enroll(attendance)
    row = attendance.enter({"id_matricula": 1}, admin)
    attendance.exit(row["id_asistencia"], admin)
    assert attendance.roster(1, "2026-10-07")["clientes"][0]["asistencia"]["id_asistencia"] == row["id_asistencia"]
    assert attendance.roster(1, "2026-10-14")["clientes"] == []
    attendance.clock = lambda: datetime.fromisoformat("2026-10-14T10:30:00-05:00")
    before = deepcopy(attendance.gym.state["asistencia"])
    with pytest.raises(ValueError, match="fecha de esta clase"):
        attendance.enter({"id_matricula": 1}, admin)
    assert attendance.gym.state["asistencia"] == before
    attendance.gym.state["matriculas_horario"].append({"id_matricula": 2, "id_cliente": 2,
        "id_horario_servicio": 1, "estado": "ACTIVA", "fecha_clase": "2026-10-14"})
    roster = attendance.roster(1, "2026-10-14")
    assert [r["cliente"]["id_cliente"] for r in roster["clientes"]] == [2]
    assert roster["clientes"][0]["asistencia"] is None
    assert roster["clientes"][0]["puede_entrar"]


def test_http_asistencia_consulta_fecha_y_valida_parametro(api, attendance):
    enroll(attendance)
    client, _ = api
    assert len(client.get('/asistencia/horarios/1/clientes?fecha=2026-10-07').json()["clientes"]) == 1
    assert client.get('/asistencia/horarios/1/clientes?fecha=2026-10-14').json()["clientes"] == []
    assert client.get('/asistencia/horarios/1/clientes?fecha=2026-02-30').status_code == 422
