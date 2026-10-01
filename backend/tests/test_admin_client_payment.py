from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config import Settings, get_settings
from dependencies import get_clients_service, get_current_user, get_gym_service
from models.auth import UserProfile
from routes.clients_routes import router
from services.clients_service import ClientsService
from services.local_gym_service import LocalGymService
from services.supabase_gym_service import SupabaseGymService
import services.stripe_service as stripe_service


PAYLOAD = {
    "nombre": "Cliente Admin", "correo": "admin-client@example.com",
    "dni": "12345678", "password": "secreto123", "plan": "MENSUAL",
}


@pytest.fixture
def api(monkeypatch):
    gym = LocalGymService()
    service = ClientsService(gym)
    settings = Settings(
        stripe_secret_key="sk_test_example", stripe_webhook_secret="whsec_example",
        frontend_public_url="https://gym.example",
    )
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_clients_service] = lambda: service
    app.dependency_overrides[get_gym_service] = lambda: gym
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: UserProfile(
        id="ADMIN1", name="Admin", email="admin@example.com", role="admin",
    )
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(id="cs_test_admin", url="https://checkout.stripe.com/test")

    monkeypatch.setattr(stripe_service.stripe.checkout.Session, "create", create)
    return TestClient(app), gym, service, settings, calls


def test_register_without_payment_creates_pending_admin_membership(api):
    client, gym, _, _, calls = api
    response = client.post("/clientes/registro-admin", json=PAYLOAD)
    assert response.status_code == 201
    result = response.json()
    assert result["cliente"]["origen_registro"] == "ADMIN"
    assert "password_hash" not in result["cliente"]
    assert result["membresia"]["estado_pago"] == "PENDIENTE"
    assert result["membresia"]["estado"] == "EN_TRAMITE"
    assert result["membresia"]["fecha_inicio"] == ""
    assert result["payment"] is None
    assert len(gym.state["clientes"]) == len(gym.state["membresia"]) == 1
    assert calls == []


def test_register_and_pay_returns_to_admin_and_preserves_discount(api):
    client, gym, _, _, calls = api
    promo = gym.upsert_promocion({
        "nombre": "Admin promo", "valor_descuento": 10, "tipo_descuento": "monto",
        "planes_aplicables": [1], "activo": True,
    })
    response = client.post("/clientes/registro-admin", json={
        **PAYLOAD, "pagar_con_stripe": True, "id_promocion": promo["id_promocion"],
        "estado_pago": "PAGADO", "origen_registro": "PUBLICO", "estado": "ACTIVO",
    })
    assert response.status_code == 201
    result = response.json()
    assert result["payment"]["amount"] == 69
    assert result["membresia"]["estado_pago"] == "PENDIENTE"
    assert result["cliente"]["origen_registro"] == "ADMIN"
    checkout = calls[0]
    assert checkout["success_url"] == "https://gym.example/admin/clients?stripe_result=success&session_id={CHECKOUT_SESSION_ID}"
    assert checkout["cancel_url"] == "https://gym.example/admin/clients?stripe_result=failure"
    assert checkout["metadata"]["membership_id"] == str(result["membresia"]["id_membresia"])
    assert checkout["line_items"][0]["price_data"]["unit_amount"] == 6900


def test_admin_does_not_apply_unselected_promotion(api):
    client, gym, _, _, _ = api
    gym.upsert_promocion({"nombre": "Promo", "tipo_descuento": "monto", "valor_descuento": 10, "activo": True})
    result = client.post("/clientes/registro-admin", json=PAYLOAD).json()
    assert result["membresia"]["monto_pago"] == 79
    assert result["membresia"]["id_promocion"] is None


def test_invalid_promotion_does_not_create_client(api):
    client, gym, _, _, _ = api
    response = client.post("/clientes/registro-admin", json={**PAYLOAD, "id_promocion": 999})
    assert response.status_code == 400
    assert gym.state["clientes"] == gym.state["membresia"] == []


def test_retry_checkout_uses_saved_amount_and_does_not_duplicate_registration(api):
    client, gym, _, _, calls = api
    result = client.post("/clientes/registro-admin", json=PAYLOAD).json()
    gym.state["planes_membresia"][0]["precio"] = 999
    for _ in range(2):
        response = client.post(f"/clientes/{result['cliente']['id_cliente']}/pago-stripe")
        assert response.status_code == 200
        assert response.json()["amount"] == 79
    assert len(gym.state["clientes"]) == len(gym.state["membresia"]) == 1
    assert calls[0]["idempotency_key"] == calls[1]["idempotency_key"]


@pytest.mark.parametrize("origin", ["PUBLICO", "", None])
def test_panel_rejects_public_and_unknown_origin(api, origin):
    client, gym, _, _, calls = api
    result = gym.registrar_cliente_publico(PAYLOAD)
    result["cliente"]["origen_registro"] = origin
    response = client.post(f"/clientes/{result['cliente']['id_cliente']}/pago-stripe")
    assert response.status_code == 400
    assert calls == []


def test_panel_rejects_paid_membership(api):
    client, _, service, _, calls = api
    result = service.register_admin_client(PAYLOAD)
    service.confirm_manual_payment(result["cliente"]["id_cliente"])
    response = client.post(f"/clientes/{result['cliente']['id_cliente']}/pago-stripe")
    assert response.status_code == 400
    assert calls == []


def test_verified_admin_payment_allows_activation_and_blocks_another_checkout(api, monkeypatch):
    client, _, service, _, calls = api
    result = service.register_admin_client(PAYLOAD)
    client_id = result["cliente"]["id_cliente"]
    membership_id = result["membresia"]["id_membresia"]
    monkeypatch.setattr(stripe_service.stripe.checkout.Session, "retrieve", lambda *args, **kwargs: {
        "id": "cs_test_paid", "livemode": False, "status": "complete", "payment_status": "paid",
        "mode": "payment", "currency": "pen", "amount_total": 7900,
        "client_reference_id": f"membership:{client_id}",
        "metadata": {"purpose": "membership", "client_id": str(client_id), "membership_id": str(membership_id)},
    })
    response = client.post("/pagos/stripe/confirmar-retorno?session_id=cs_test_paid")
    assert response.status_code == 200
    assert response.json()["confirmed"] is True
    assert client.post(f"/clientes/{client_id}/activar-membresia").status_code == 200
    assert client.post(f"/clientes/{client_id}/pago-stripe").status_code == 400
    assert calls == []


def test_stripe_failure_keeps_registration_available_for_retry(api, monkeypatch):
    client, gym, _, _, _ = api

    def fail(**kwargs):
        raise RuntimeError("Stripe unavailable")

    monkeypatch.setattr(stripe_service.stripe.checkout.Session, "create", fail)
    response = client.post("/clientes/registro-admin", json={**PAYLOAD, "pagar_con_stripe": True})
    assert response.status_code == 201
    assert response.json()["payment"]["message"]
    assert len(gym.state["clientes"]) == len(gym.state["membresia"]) == 1
    assert gym.state["membresia"][0]["estado_pago"] == "PENDIENTE"


def test_missing_stripe_configuration_fails_before_registration(api):
    client, gym, _, settings, _ = api
    settings.stripe_secret_key = ""
    response = client.post("/clientes/registro-admin", json={**PAYLOAD, "pagar_con_stripe": True})
    assert response.status_code == 503
    assert gym.state["clientes"] == []
    assert client.post("/clientes/registro-admin", json=PAYLOAD).status_code == 201


@pytest.mark.parametrize("path", ["/clientes/registro-admin", "/clientes/1/pago-stripe"])
def test_panel_requires_authentication(api, path):
    client, _, _, _, calls = api
    del client.app.dependency_overrides[get_current_user]
    assert client.post(path, json=PAYLOAD).status_code == 401
    assert calls == []


@pytest.mark.parametrize("role", ["user", "trainer"])
def test_panel_rejects_non_admin_roles(api, role):
    client, gym, _, _, calls = api
    client.app.dependency_overrides[get_current_user] = lambda: UserProfile(
        id="USER1", name="User", email="user@example.com", role=role,
    )
    assert client.post("/clientes/registro-admin", json=PAYLOAD).status_code == 403
    assert client.post("/clientes/1/pago-stripe").status_code == 403
    assert gym.state["clientes"] == calls == []


def test_editing_client_preserves_origin_and_identity(api):
    _, gym, service, _, _ = api
    result = service.register_admin_client(PAYLOAD)
    saved = service.upsert_client({**PAYLOAD, "id_usuario": result["cliente"]["id_usuario"], "estado": "PENDIENTE_PAGO"})
    assert saved["id_cliente"] == result["cliente"]["id_cliente"]
    assert saved["origen_registro"] == "ADMIN"
    assert len(gym.state["clientes"]) == 1
    normalized = gym._normalize(gym.state)
    assert normalized["clientes"][0]["origen_registro"] == "ADMIN"


def test_admin_schema_is_required_instead_of_silently_dropping_origin():
    class FakeSupabase:
        def validate_columns(self, table, columns):
            raise RuntimeError("PGRST204: missing column")

    gym = object.__new__(SupabaseGymService)
    gym.remote_columns = {"CLIENTES": {"id_cliente", "Nombres"}}
    gym.supabase = FakeSupabase()
    with pytest.raises(RuntimeError, match="009_admin_client_stripe.sql"):
        gym.validate_admin_registration_schema()
    assert "origen_registro" not in gym._filter_remote_columns("CLIENTES", {"id_cliente": 1, "origen_registro": "PUBLICO"})


def test_zero_price_is_not_replaced_with_plan_price(api):
    _, _, service, settings, calls = api
    result = service.register_admin_client(PAYLOAD)
    result["membresia"]["monto_pago"] = 0
    with pytest.raises(ValueError, match="mayor que cero"):
        stripe_service.StripeService(settings).create_membership_checkout(result, admin=True)
    assert calls == []
