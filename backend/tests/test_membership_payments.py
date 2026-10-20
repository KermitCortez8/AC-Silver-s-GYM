import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from config import Settings, get_settings
from dependencies import get_clients_service, get_current_user, get_gym_service
from models.auth import UserProfile
from routes.clients_routes import router
from services.clients_service import ClientsService
from services.local_gym_service import LocalGymService
import routes.clients_routes as clients_routes


@pytest.fixture
def api():
    gym = LocalGymService()
    service = ClientsService(gym)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_clients_service] = lambda: service
    app.dependency_overrides[get_gym_service] = lambda: gym
    app.dependency_overrides[get_settings] = lambda: Settings()
    app.dependency_overrides[get_current_user] = lambda: UserProfile(
        id="ADMIN1", name="Admin", email="admin@example.com", role="admin",
    )
    return TestClient(app), app, gym, service


def register(service):
    return service.register_public_client({
        "nombre": "Cliente Stripe", "correo": "stripe@example.com",
        "dni": "12345678", "password": "secreto123", "plan": "MENSUAL",
    })


def test_verified_stripe_registration_appears_once_in_payment_history(api, monkeypatch):
    client, _, gym, service = api
    result = register(service)
    client_id = result["cliente"]["id_cliente"]
    membership_id = result["membresia"]["id_membresia"]
    pending = client.get("/pagos/membresias").json()
    assert len(pending) == 1
    assert pending[0]["estado_pago"] == "PENDIENTE"
    assert pending[0]["fecha_pago"] == ""

    class Gateway:
        def __init__(self, settings):
            pass

        def get_checkout_session(self, session_id):
            return {
                "id": session_id, "livemode": False, "status": "complete",
                "payment_status": "paid", "mode": "payment", "currency": "pen",
                "amount_total": 7900, "client_reference_id": f"membership:{client_id}",
                "metadata": {"purpose": "membership", "client_id": str(client_id),
                             "membership_id": str(membership_id)},
            }

    monkeypatch.setattr(clients_routes, "StripeService", Gateway)
    monkeypatch.setattr(clients_routes, "notify_membership", lambda *args: {})
    for _ in range(2):
        response = client.post("/pagos/stripe/confirmar-retorno?session_id=cs_verified")
        assert response.status_code == 200
        assert response.json()["confirmed"] is True
    rows = client.get("/pagos/membresias").json()
    assert len(rows) == 1
    assert rows[0]["nombre"] == "Cliente Stripe"
    assert rows[0]["plan"] == "MENSUAL"
    assert rows[0]["monto_pago"] == 79
    assert rows[0]["metodo_pago"] == "stripe"
    assert rows[0]["referencia_pago"] == "cs_verified"
    assert rows[0]["estado_pago"] == "PAGADO"
    assert rows[0]["fecha_pago"]
    assert "password_hash" not in rows[0]
    assert "google_sub" not in rows[0]
    assert gym.state["membresia"][0]["estado"] == "EN_TRAMITE"


def test_history_keeps_older_payments_and_saved_discounted_amount(api):
    client, _, gym, service = api
    result = register(service)
    membership = result["membresia"]
    membership.update(monto_pago=69, estado_pago="PAGADO", metodo_pago="stripe",
                      referencia_pago="cs_old", fecha_pago="2026-09-01", estado="VENCIDA")
    gym.state["membresia"].append({
        "id_membresia": 2, "id_cliente": result["cliente"]["id_cliente"], "id_pm": 2,
        "monto_pago": 199, "estado_pago": "PENDIENTE", "metodo_pago": "stripe",
    })
    gym.state["planes_membresia"][0]["precio"] = 99
    rows = client.get("/pagos/membresias").json()
    assert [row["id_membresia"] for row in rows] == [2, 1]
    assert rows[0]["plan"] == "3 MESES"
    assert rows[0]["estado_pago"] == "PENDIENTE"
    assert rows[1]["monto_pago"] == 69
    assert rows[1]["referencia_pago"] == "cs_old"
    assert rows[1]["estado_pago"] == "PAGADO"


def test_manual_payments_are_identified_and_not_relabelled_as_stripe(api):
    client, _, _, service = api
    result = register(service)
    service.confirm_manual_payment(result["cliente"]["id_cliente"])
    row = client.get("/pagos/membresias").json()[0]
    assert row["metodo_pago"] == "efectivo"
    assert row["referencia_pago"].startswith("manual:")
    assert row["estado_pago"] == "PAGADO"


@pytest.mark.parametrize("role,expected", [("admin", 200), ("staff", 200), ("user", 403), ("trainer", 403)])
def test_payment_history_requires_staff_access(api, role, expected):
    client, app, _, _ = api
    app.dependency_overrides[get_current_user] = lambda: UserProfile(
        id="USER1", name="User", email="user@example.com", role=role,
    )
    assert client.get("/pagos/membresias").status_code == expected


def test_payment_history_requires_authentication(api):
    client, app, _, _ = api
    def unauthenticated():
        raise HTTPException(status_code=401, detail="Falta token")

    app.dependency_overrides[get_current_user] = unauthenticated
    assert client.get("/pagos/membresias").status_code == 401
