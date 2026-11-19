"""Contratos de catálogo y cupos a través de la API real con datos QA."""
from copy import deepcopy

import pytest

from tests.soporte.testiny_api import documented_api  # noqa: F401


URL = "/api/gym/horarios-servicio"
SCHEDULE = dict(servicio="fitness", id_rutina=7, codigo_dia="LUN", dia="lunes",
                hora_inicio="10:00", hora_fin="11:00", cupos=4, activo=True)


@pytest.fixture
def schedules(documented_api):
    api = documented_api
    api.gym.state["horarios_servicio"] = []
    api.gym.state["catalogo_rutina"] = [
        {"id_rutina": 7, "servicio": "fitness", "nombre_rutina": "Circuito QA"},
        {"id_rutina": 8, "servicio": "baile", "nombre_rutina": "Baile QA"},
    ]
    return api


def save(api, **changes):
    response = api.client.post(URL, json={**SCHEDULE, **changes})
    assert response.status_code == 200, response.text
    return response.json()


def test_tc056_modificar_horario_conserva_sesiones_y_cupos(schedules, monkeypatch):
    monkeypatch.setattr("domain.services.gym_domain_service._today_iso", lambda: "2026-10-05")
    saved = save(schedules)
    identity = saved["id_horario_servicio"]
    sessions = ("2026-10-05", "2026-10-12")
    for day in sessions:
        schedules.gym.matricular_cliente_horario({"id_cliente": 1, "id_horario_servicio": identity, "fecha_clase": day})
    original = deepcopy(schedules.gym.state["matriculas_horario"])

    save(schedules, id_horario_servicio=identity, hora_inicio="11:00", hora_fin="12:00")
    [edited] = schedules.client.get(URL).json()
    assert (edited["hora_inicio"], edited["hora_fin"]) == ("11:00", "12:00")
    assert edited["ocupacion_por_fecha"] == dict.fromkeys(sessions, 1)
    assert edited["cupos_disponibles"] == 3

    reduced = save(schedules, id_horario_servicio=identity, hora_inicio="11:00", hora_fin="12:00", cupos=1)
    assert reduced["cupos"] == 1
    [full] = schedules.client.get(URL).json()
    assert full["ocupacion_por_fecha"] == dict.fromkeys(sessions, 1)
    assert full["cupos_disponibles"] == 0

    refused = schedules.client.post(URL, json={**full, "dia": "martes", "codigo_dia": "MAR"})
    assert refused.status_code == 400 and "matrículas pendientes" in refused.text
    assert schedules.client.get(URL).json() == [full]
    assert schedules.gym.state["matriculas_horario"] == original


@pytest.mark.parametrize("begin,end,status,message", [
    ("", "11:00", 400, "Hora invalida"), ("10:00", "", 400, "Hora invalida"),
    ("10:00", "10:30", 400, "1 o 2 horas"), ("10:00", "11:30", 400, "1 o 2 horas"),
    ("10:00", "09:00", 422, "La hora de fin debe ser posterior"),
])
def test_tc058_rechaza_horas_y_permite_corregir(schedules, begin, end, status, message):
    response = schedules.client.post(URL, json={**SCHEDULE, "hora_inicio": begin, "hora_fin": end})
    assert response.status_code == status and message in response.text
    assert schedules.client.get(URL).json() == []

    save(schedules, hora_inicio="10:00:00", hora_fin="11:00:00")
    save(schedules, hora_inicio="18:00:00", hora_fin="20:00:00")
    rows = schedules.client.get(URL).json()
    assert {(row["hora_inicio"], row["hora_fin"]) for row in rows} == {("10:00", "11:00"), ("18:00", "20:00")}


@pytest.mark.parametrize("value", [0, -1, 2.5, "texto"])
def test_tc059_no_guarda_cupos_invalidos_y_acepta_enteros(schedules, value):
    saved = save(schedules)
    identity = saved["id_horario_servicio"]
    before = schedules.client.get(URL).json()
    response = schedules.client.post(URL, json={**SCHEDULE, "id_horario_servicio": identity, "cupos": value})
    assert response.status_code == 422
    assert "cupos" in response.text
    assert schedules.client.get(URL).json() == before

    save(schedules, id_horario_servicio=identity, cupos=3)
    [updated] = schedules.client.get(URL).json()
    assert (updated["cupos"], updated["cupos_usados"], updated["cupos_disponibles"]) == (3, 0, 3)


@pytest.mark.parametrize("changes,status,message", [
    ({"id_rutina": 0}, 422, "identificador debe ser un entero positivo"),
    ({"id_rutina": 8}, 400, "no corresponde"),
    ({"dia": "", "codigo_dia": ""}, 400, "dia valido"),
    ({"dia": "inválido"}, 400, "dia valido"),
])
def test_tc060_valida_rutina_y_dia_y_permite_coincidencias(schedules, changes, status, message):
    response = schedules.client.post(URL, json={**SCHEDULE, **changes})
    assert response.status_code == status and message in response.text
    assert schedules.client.get(URL).json() == []
    first = save(schedules)
    second = save(schedules)
    assert first["id_horario_servicio"] != second["id_horario_servicio"]
    assert len(schedules.client.get(URL).json()) == 2


@pytest.mark.parametrize("start,end", [("10:00", "11:00"), ("18:00", "20:00")])
def test_tc054_horario_guardado_es_consultable_y_tiene_cupos_consistentes(schedules, start, end):
    saved = save(schedules, hora_inicio=start, hora_fin=end)
    [loaded] = schedules.client.get(URL).json()
    assert loaded["id_horario_servicio"] == saved["id_horario_servicio"]
    assert (loaded["servicio"], loaded["id_rutina"], loaded["rutina_nombre"]) == ("fitness", 7, "Circuito QA")
    assert (loaded["codigo_dia"], loaded["hora_inicio"], loaded["hora_fin"], loaded["activo"]) == ("LUN", start, end, True)
    assert (loaded["cupos"], loaded["cupos_usados"], loaded["cupos_disponibles"]) == (4, 0, 4)
    assert schedules.client.get("/api/gym/horarios-publicos").json()[0]["hora_inicio"] == start


def test_tc057_borrar_horario_libre_y_pausar_el_reservado(schedules, monkeypatch):
    monkeypatch.setattr("domain.services.gym_domain_service._today_iso", lambda: "2026-10-05")
    free = save(schedules)
    occupied = save(schedules, hora_inicio="11:00", hora_fin="12:00")
    reserved = occupied["id_horario_servicio"]
    schedules.gym.matricular_cliente_horario({"id_cliente": 1, "id_horario_servicio": reserved, "fecha_clase": "2026-10-05"})
    enrollments = deepcopy(schedules.gym.state["matriculas_horario"])
    assert schedules.client.delete(f"{URL}/{free['id_horario_servicio']}").status_code == 204
    assert [row["id_horario_servicio"] for row in schedules.client.get(URL).json()] == [reserved]
    denied = schedules.client.delete(f"{URL}/{reserved}")
    assert denied.status_code == 404 and "matriculas activas" in denied.text
    assert schedules.gym.state["matriculas_horario"] == enrollments
    save(schedules, **{**occupied, "activo": False})
    assert schedules.client.get(URL).json()[0]["activo"] is False
    assert schedules.client.get("/api/gym/horarios-publicos").json() == []
    assert schedules.gym.state["matriculas_horario"] == enrollments


def test_tc062_cupo_lleno_rechaza_una_fecha_y_deja_reservar_otra(schedules, monkeypatch):
    monkeypatch.setattr("domain.services.gym_domain_service._today_iso", lambda: "2026-10-05")
    study = save(schedules, cupos=1)
    identity = study["id_horario_servicio"]
    url = "/api/gym/matriculas"
    monday = {"id_horario_servicio": identity, "fecha_clase": "2026-10-05"}
    assert schedules.client.post(url, json={**monday, "id_cliente": 1}).status_code == 200
    before = deepcopy(schedules.gym.state["matriculas_horario"])
    denied = schedules.client.post(url, json={**monday, "id_cliente": 2})
    assert denied.status_code in (400, 409) and "cupo" in denied.text.lower()
    assert schedules.gym.state["matriculas_horario"] == before
    next_monday = schedules.client.post(url, json={**monday, "id_cliente": 2, "fecha_clase": "2026-10-12"})
    assert next_monday.status_code == 200 and next_monday.json()["estado"] == "ACTIVA"
    assert schedules.client.get(URL).json()[0]["ocupacion_por_fecha"] == {"2026-10-05": 1, "2026-10-12": 1}
