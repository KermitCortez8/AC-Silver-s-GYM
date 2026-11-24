import pytest

from domain.services.schedule_sessions import SALAS_HORARIO
from tests.soporte.testiny_api import documented_api  # noqa: F401


URL = "/api/gym/horarios-servicio"


@pytest.fixture
def clase(documented_api):
    api = documented_api
    api.gym.state["horarios_servicio"] = []
    rutina = api.gym.upsert_rutina({"nombre_rutina": "Circuito", "servicio": "fitness"})
    return {
        "servicio": "fitness", "id_rutina": rutina["id_rutina"], "dia": "lunes",
        "hora_inicio": "10:00", "hora_fin": "11:00", "cupos": 8, "activo": True,
    }


@pytest.mark.parametrize("sala", [None, "", "Sala inexistente", "Sala 1", "Sala de fuerza"])
def test_sala_requerida_del_catalogo_fijo(documented_api, clase, sala):
    response = documented_api.client.post(URL, json={**clase, "sala": sala})
    assert response.status_code == 400
    assert "sala" in response.json()["detail"].lower()
    assert documented_api.client.get(URL).json() == []


def test_sala_consultable_y_editable_para_horarios_con_matriculas(documented_api, clase):
    api = documented_api
    creado = api.client.post(URL, json={**clase, "sala": SALAS_HORARIO[0]})
    assert creado.status_code == 200
    horario_id = creado.json()["id_horario_servicio"]
    api.gym.matricular_cliente_horario({
        "id_cliente": 1, "id_horario_servicio": horario_id, "fecha_clase": "2099-10-05",
    })
    cambio = api.client.post(URL, json={**clase, "id_horario_servicio": horario_id, "sala": SALAS_HORARIO[1]})
    assert cambio.status_code == 200
    assert cambio.json()["sala"] == SALAS_HORARIO[1]

    usado = api.client.get(URL).json()[0]
    assert usado["ocupacion_por_fecha"] == {"2099-10-05": 1}
    assert api.client.get("/api/gym/horarios-publicos").json()[0]["sala"] == SALAS_HORARIO[1]
    api.login("user")
    assert api.client.get("/api/gym/matriculas").json()[0]["sala"] == SALAS_HORARIO[1]


@pytest.mark.parametrize("sala_anterior", [None, "Sala 1"])
def test_asignacion_posterior_de_una_clase_previa(documented_api, clase, sala_anterior):
    api = documented_api
    api.gym.state["horarios_servicio"] = [{**clase, "id_horario_servicio": 5, "sala": sala_anterior}]
    assert api.client.get(URL).json()[0]["sala"] == sala_anterior

    if sala_anterior:
        conservado = api.client.post(URL, json={**clase, "id_horario_servicio": 5, "cupos": 9})
        assert conservado.status_code == 200
        assert conservado.json()["sala"] == sala_anterior

    editado = api.client.post(URL, json={**clase, "id_horario_servicio": 5, "sala": SALAS_HORARIO[0]})
    assert editado.status_code == 200
    preservado = api.client.post(URL, json={**clase, "id_horario_servicio": 5, "cupos": 9})
    assert preservado.status_code == 200
    assert preservado.json()["sala"] == SALAS_HORARIO[0]
