from copy import deepcopy

import pytest

from domain.services.schedule_sessions import SALAS_HORARIO
from tests.soporte.testiny_api import documented_api  # noqa: F401


URL = "/api/gym/horarios-servicio/configuracion"
DEFAULTS = {"hora_inicio": "06:00", "duracion_minutos": 60, "cupos": 10}
PARAMETERS = {"hora_inicio": "08:30", "duracion_minutos": 120, "cupos": 16}
GYM_SETTINGS = "/api/gym/configuracion"


def test_parametros_compartidos_conservan_horarios_y_aforo(documented_api):
    api = documented_api
    horarios = deepcopy(api.gym.state["horarios_servicio"])
    assert api.client.get(URL).json() == DEFAULTS
    capacidad = {"capacidad_total": 40, "capacidad_por_hora": 12}
    assert api.client.post(GYM_SETTINGS, json=capacidad).json() == capacidad

    assert api.client.put(URL, json=PARAMETERS).json() == PARAMETERS
    api.login("staff")
    assert api.client.get(URL).json() == PARAMETERS
    assert api.client.get(GYM_SETTINGS).json() == capacidad

    capacidad["capacidad_total"] = 50
    assert api.client.post(GYM_SETTINGS, json=capacidad).json() == capacidad
    assert api.client.get(URL).json() == PARAMETERS
    assert api.gym.state["horarios_servicio"] == horarios


@pytest.mark.parametrize("invalid", [
    {"hora_inicio": "22:00"},
    {"hora_inicio": "21:00"},
    {"hora_inicio": "05:59"},
    {"hora_inicio": "8:30"},
    {"duracion_minutos": 90},
    {"cupos": 0},
    {"cupos": True},
])
def test_parametros_invalidos_no_reemplazan_la_configuracion(documented_api, invalid):
    client = documented_api.client
    assert client.put(URL, json=PARAMETERS).status_code == 200
    assert client.put(URL, json={**PARAMETERS, **invalid}).status_code == 422
    assert client.get(URL).json() == PARAMETERS


@pytest.mark.parametrize("role", ["user", "trainer"])
def test_parametros_solo_para_personal_autorizado(documented_api, role):
    api = documented_api
    api.login(role)
    assert api.client.get(URL).status_code == 403
    assert api.client.put(URL, json=PARAMETERS).status_code == 403


@pytest.mark.parametrize("dia,inicio,fin,esperado", [
    ("lunes", "06:00", "07:00", 200),
    ("viernes", "20:00", "22:00", 200),
    ("viernes", "21:01", "22:01", 400),
    ("sábado", "06:59", "07:59", 400),
    ("sábado", "07:00", "09:00", 200),
    ("domingo", "17:00", "18:00", 200),
    ("domingo", "17:01", "18:01", 400),
])
def test_horario_completo_dentro_de_atencion(documented_api, dia, inicio, fin, esperado):
    api = documented_api
    rutina = api.gym.upsert_rutina({"nombre_rutina": "Circuito", "servicio": "fitness"})
    antes = deepcopy(api.gym.state["horarios_servicio"])
    response = api.client.post("/api/gym/horarios-servicio", json={
        "servicio": "fitness", "id_rutina": rutina["id_rutina"], "dia": dia,
        "hora_inicio": inicio, "hora_fin": fin, "cupos": 8, "activo": True, "sala": SALAS_HORARIO[0],
    })
    assert response.status_code == esperado
    if esperado == 400:
        assert api.gym.state["horarios_servicio"] == antes


def test_horario_retirado_se_conserva_sin_aparecer_en_el_catalogo(documented_api):
    api = documented_api
    rutina = api.gym.upsert_rutina({"nombre_rutina": "Circuito", "servicio": "fitness"})
    clase = {"servicio": "fitness", "id_rutina": rutina["id_rutina"], "dia": "sábado", "cupos": 8}
    retirado = {**clase, "id_horario_servicio": 31, "hora_inicio": "07:00", "hora_fin": "19:00", "activo": False}
    vigente = {**clase, "id_horario_servicio": 32, "hora_inicio": "7 a. m.", "hora_fin": "8 am", "activo": True}
    api.gym.state["horarios_servicio"] = [retirado.copy(), vigente.copy()]
    [visible] = api.client.get("/api/gym/horarios-servicio").json()
    assert (visible["id_horario_servicio"], visible["dia"], visible["hora_inicio"], visible["hora_fin"]) == (32, "sabado", "07:00", "08:00")
    assert api.client.post("/api/gym/horarios-servicio", json={
        **clase, "hora_inicio": "16:00", "hora_fin": "17:00", "sala": SALAS_HORARIO[0],
    }).status_code == 200
    assert api.gym.get_horario_servicio(31)["hora_fin"] == "19:00"
