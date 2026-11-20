import pytest

from tests.clientes.integracion.test_admin_client_payment import PAYLOAD, api


@pytest.mark.parametrize("checkout", [False, True])
def test_admin_registers_one_day_class_from_catalog(api, checkout):
    client, gym, _, _, calls = api
    plan = gym.upsert_plan_membresia({
        "nombre_plan": "CLASE", "duracion": "1 día", "precio": 12,
    })

    response = client.post("/clientes/registro-admin", json={
        **PAYLOAD, "plan": "CLASE", "pagar_con_stripe": checkout,
    })

    assert response.status_code == 201
    result = response.json()
    assert result["cliente"]["plan"] == "CLASE"
    assert result["membresia"]["id_pm"] == plan["id_pm"]
    assert result["membresia"]["monto_pago"] == 12
    assert result["membresia"]["estado_pago"] == "PENDIENTE"
    assert len(calls) == int(checkout)
    if checkout:
        assert calls[0]["line_items"][0]["price_data"]["unit_amount"] == 1200


@pytest.mark.parametrize("exists", [False, True])
def test_admin_rejects_unavailable_class_before_writing(api, exists):
    client, gym, _, _, calls = api
    if exists:
        gym.upsert_plan_membresia({
            "nombre_plan": "CLASE", "duracion": "1 día", "precio": 12, "activo": False,
        })

    response = client.post("/clientes/registro-admin", json={
        **PAYLOAD, "plan": "CLASE", "pagar_con_stripe": True,
    })

    assert response.status_code == 400
    assert gym.state["clientes"] == gym.state["membresia"] == calls == []
