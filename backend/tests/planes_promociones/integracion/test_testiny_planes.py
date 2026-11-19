"""Protección de contratos ya firmados mediante la API real de planes."""
from copy import deepcopy

import pytest

from application.services.clients_service import ClientsService
from tests.soporte.testiny_api import documented_api  # noqa: F401


PLANS = "/api/planes-membresia"


def save_plan(api, **changes):
    response = api.client.post(PLANS, json={
        "nombre_plan": "Plan QA", "precio": 100, "duracion": "30 días", "descripcion": "Entrenamiento QA",
        "activo": True, **changes,
    })
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("duration,days", [("15 días", 15), ("2 meses", 60), ("1 año", 365)])
def test_tc035_duracion_guardada_y_precio_cero_en_catalogo(documented_api, duration, days):
    api = documented_api
    plan = save_plan(api, duracion=duration, precio=0)
    assert plan in api.client.get(PLANS).json()
    assert plan["precio"] == 0 and plan["activo"] and plan["descripcion"] == "Entrenamiento QA"
    assert api.gym.components.memberships._duration_days(plan) == days


def test_tc036_tc037_editar_catalogo_no_recalcula_importe_previo(documented_api):
    api = documented_api
    plan = save_plan(api)
    identity = plan["id_pm"]
    api.gym.state["membresia"][0].update(id_pm=identity, monto_pago=72)
    original = deepcopy(api.client.get("/api/clientes/1/membresias").json())
    assert plan in api.client.get(PLANS).json() and original[0]["monto_pago"] == 72
    updated = api.client.put(f"{PLANS}/{identity}", json={
        **plan, "nombre_plan": "Plan extendido", "precio": 120, "descripcion": "Descripción editada",
    })
    assert updated.status_code == 200 and updated.json() in api.client.get(PLANS).json()
    assert updated.json()["precio"] == 120
    assert api.client.get("/api/clientes/1/membresias").json() == original
    promo = api.gym.upsert_promocion({"nombre": "Descuento QA", "tipo_descuento": "monto",
        "valor_descuento": 10, "planes_aplicables": [identity], "activo": True})
    new = ClientsService(api.gym).register_admin_client({
        "nombre": "Nuevo Cliente QA", "correo": "nuevo@gmail.com", "dni": "33333333",
        "telefono": "999999999", "password": "qa-synthetic-password", "plan": updated.json()["nombre_plan"],
        "id_promocion": promo["id_promocion"],
    })
    assert new["membresia"]["monto_pago"] == 110
    assert api.client.get("/api/clientes/1/membresias").json() == original


def test_tc038_eliminar_plan_no_utilizado_preserva_otros(documented_api):
    api = documented_api
    plan = save_plan(api)
    before = [item for item in api.client.get(PLANS).json() if item["id_pm"] != plan["id_pm"]]
    assert api.client.delete(f"{PLANS}/{plan['id_pm']}").status_code == 204
    assert api.client.get(PLANS).json() == before


@pytest.mark.parametrize("state,end", [("ACTIVO", "2099-12-31"), ("VENCIDA", "2021-01-01")])
def test_tc040_un_plan_vinculado_se_puede_desactivar_pero_no_borrar(documented_api, state, end):
    api = documented_api
    plans = "/api/planes-membresia"
    saved = api.client.post(plans, json={"nombre_plan": "Plan QA", "precio": 100, "duracion": "30 días"})
    assert saved.status_code == 200, saved.text
    plan = saved.json()
    identity = plan["id_pm"]
    api.gym.state["membresia"][0].update(id_pm=identity, estado=state, fecha_fin=end, monto_pago=72)
    before = deepcopy(api.client.get("/api/clientes/1/membresias").json())
    response = api.client.delete(f"{plans}/{identity}")
    assert response.status_code == 400 and "usado por membresías" in response.text
    assert api.gym.get_plan_membresia(identity) == plan
    assert api.client.get("/api/clientes/1/membresias").json() == before
    assert before[0]["monto_pago"] == 72

    updated = api.client.put(f"{plans}/{identity}", json={**plan, "activo": False})
    assert updated.status_code == 200 and not updated.json()["activo"]
    error = api.client.post("/api/membresias", json={"id_cliente": 2, "id_pm": identity,
                            "fecha_inicio": "2026-11-19", "fecha_fin": "2026-12-19"})
    assert error.status_code == 400 and "disponible" in error.text
    assert api.client.get("/api/clientes/1/membresias").json() == before
