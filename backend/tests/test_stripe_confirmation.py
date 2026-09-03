from __future__ import annotations

from types import SimpleNamespace

import pytest

import routes.clients_routes as clients_routes
from models.gym import RegistroPublicoClienteInput
from services.clients_service import ClientsService
from services.local_gym_service import LocalGymService


class FakeClientsService:
    def __init__(self, amount_matches: bool = True) -> None:
        self.amount_matches = amount_matches
        self.confirmations: list[tuple[int, dict]] = []

    def confirm_public_payment(self, id_cliente: int, payload: dict) -> dict:
        if (
            not self.amount_matches
            or id_cliente != 12
            or payload.get("id_membresia") != 34
            or payload.get("monto_pago") != 79.0
        ):
            raise ValueError("La membresía o el importe del pago no coincide con el registro")
        self.confirmations.append((id_cliente, payload))
        return {"membresia": {"estado": "EN_TRAMITE"}}


def _install_gateway(monkeypatch, checkout: dict) -> None:
    class FakeGateway:
        def __init__(self, _settings) -> None:
            pass

        def get_checkout_session(self, _session_id: str) -> dict:
            return checkout

    monkeypatch.setattr(clients_routes, "StripeService", FakeGateway)


def _paid_checkout(**overrides) -> dict:
    checkout = {
        "id": "cs_test_123",
        "status": "complete",
        "payment_status": "paid",
        "mode": "payment",
        "client_reference_id": "membership:12",
        "metadata": {"purpose": "membership", "client_id": "12", "membership_id": "34"},
        "currency": "pen",
        "amount_total": 7900,
    }
    checkout.update(overrides)
    return checkout


def test_confirm_verified_checkout_persists_paid_session(monkeypatch) -> None:
    _install_gateway(monkeypatch, _paid_checkout())
    clients = FakeClientsService()

    result = clients_routes._confirm_verified_checkout("cs_test_123", clients, SimpleNamespace())

    assert result["confirmed"] is True
    assert result["id_cliente"] == 12
    assert result["payment_status"] == "paid"
    assert clients.confirmations == [(
        12,
        {
            "id_membresia": 34,
            "monto_pago": 79.0,
            "metodo_pago": "stripe",
            "referencia_pago": "cs_test_123",
        },
    )]


def test_confirm_verified_checkout_does_not_persist_unpaid_session(monkeypatch) -> None:
    _install_gateway(monkeypatch, _paid_checkout(status="open", payment_status="unpaid"))
    clients = FakeClientsService()

    result = clients_routes._confirm_verified_checkout("cs_test_123", clients, SimpleNamespace())

    assert result == {"confirmed": False, "payment_status": "unpaid"}
    assert clients.confirmations == []


def test_confirm_verified_checkout_rejects_wrong_amount(monkeypatch) -> None:
    _install_gateway(monkeypatch, _paid_checkout(amount_total=8000))
    clients = FakeClientsService()

    with pytest.raises(ValueError, match="importe"):
        clients_routes._confirm_verified_checkout("cs_test_123", clients, SimpleNamespace())

    assert clients.confirmations == []


def test_confirm_verified_checkout_rejects_unrelated_metadata(monkeypatch) -> None:
    _install_gateway(monkeypatch, _paid_checkout(metadata={"purpose": "order", "client_id": "12"}))
    clients = FakeClientsService()

    with pytest.raises(ValueError, match="metadatos"):
        clients_routes._confirm_verified_checkout("cs_test_123", clients, SimpleNamespace())

    assert clients.confirmations == []


def test_confirm_verified_checkout_rejects_another_membership(monkeypatch) -> None:
    _install_gateway(monkeypatch, _paid_checkout(metadata={
        "purpose": "membership",
        "client_id": "12",
        "membership_id": "99",
    }))
    clients = FakeClientsService()

    with pytest.raises(ValueError, match="membresía"):
        clients_routes._confirm_verified_checkout("cs_test_123", clients, SimpleNamespace())

    assert clients.confirmations == []


def test_confirm_verified_checkout_rejects_live_session_in_test_mode(monkeypatch) -> None:
    _install_gateway(monkeypatch, _paid_checkout(livemode=True))
    clients = FakeClientsService()

    with pytest.raises(ValueError, match="modo configurado"):
        clients_routes._confirm_verified_checkout(
            "cs_live_123",
            clients,
            SimpleNamespace(stripe_mode="test"),
        )

    assert clients.confirmations == []


def test_payment_amount_uses_price_saved_on_membership() -> None:
    class FakeGym:
        state = {
            "membresia": [{
                "id_membresia": 34,
                "id_cliente": 12,
                "id_pm": 1,
                "monto_pago": 79.0,
            }],
        }

        def ensure_fresh(self) -> None:
            pass

        def _latest_membership_for_cliente(self, _state, id_cliente: int) -> dict | None:
            return self.state["membresia"][0] if id_cliente == 12 else None

        def get_plan_membresia(self, _id_pm: int) -> dict:
            return {"precio": 199.0}

    service = ClientsService(FakeGym())

    assert service.payment_amount_matches(12, 79.0, id_membresia=34) is True
    assert service.payment_amount_matches(12, 199.0, id_membresia=34) is False


def test_duplicate_confirmation_does_not_revert_active_membership() -> None:
    gym = LocalGymService()
    gym.state["clientes"] = [{"id_cliente": 12, "estado": "PENDIENTE_PAGO"}]
    gym.state["membresia"] = [{
        "id_membresia": 34,
        "id_cliente": 12,
        "id_pm": 1,
        "monto_pago": 79.0,
        "estado": "PENDIENTE_PAGO",
        "estado_pago": "PENDIENTE",
        "referencia_pago": "",
    }]
    payment = {
        "id_membresia": 34,
        "monto_pago": 79.0,
        "metodo_pago": "stripe",
        "referencia_pago": "cs_test_123",
    }

    gym.confirmar_pago_cliente_publico(12, payment)
    gym.activar_membresia_cliente(12)
    gym.confirmar_pago_cliente_publico(12, payment)

    assert gym.state["clientes"][0]["estado"] == "ACTIVO"
    assert gym.state["membresia"][0]["estado"] == "Activa"
    assert gym.state["membresia"][0]["estado_pago"] == "PAGADO"


def test_duplicate_confirmation_repairs_pending_client_after_partial_write() -> None:
    gym = LocalGymService()
    gym.state["clientes"] = [{"id_cliente": 12, "estado": "PENDIENTE_PAGO"}]
    gym.state["membresia"] = [{
        "id_membresia": 34,
        "id_cliente": 12,
        "id_pm": 1,
        "monto_pago": 79.0,
        "estado": "EN_TRAMITE",
        "estado_pago": "PAGADO",
        "metodo_pago": "stripe",
        "referencia_pago": "cs_test_123",
    }]

    gym.confirmar_pago_cliente_publico(12, {
        "id_membresia": 34,
        "monto_pago": 79.0,
        "metodo_pago": "stripe",
        "referencia_pago": "cs_test_123",
    })

    assert gym.state["clientes"][0]["estado"] == "EN_TRAMITE"


def test_membership_cannot_be_activated_before_payment() -> None:
    gym = LocalGymService()
    gym.state["clientes"] = [{"id_cliente": 12, "estado": "PENDIENTE_PAGO"}]
    gym.state["membresia"] = [{
        "id_membresia": 34,
        "id_cliente": 12,
        "id_pm": 1,
        "estado": "PENDIENTE_PAGO",
        "estado_pago": "PENDIENTE",
    }]

    with pytest.raises(ValueError, match="sin pago confirmado"):
        gym.activar_membresia_cliente(12)

    assert gym.state["clientes"][0]["estado"] == "PENDIENTE_PAGO"


def test_activating_an_active_membership_does_not_extend_its_dates() -> None:
    gym = LocalGymService()
    gym.state["clientes"] = [{"id_cliente": 12, "estado": "PENDIENTE_PAGO"}]
    gym.state["membresia"] = [{
        "id_membresia": 34,
        "id_cliente": 12,
        "id_pm": 1,
        "fecha_inicio": "2026-01-01",
        "fecha_fin": "2026-01-31",
        "estado": "Activa",
        "estado_pago": "PAGADO",
    }]

    gym.activar_membresia_cliente(12)

    assert gym.state["clientes"][0]["estado"] == "ACTIVO"
    assert gym.state["membresia"][0]["fecha_inicio"] == "2026-01-01"
    assert gym.state["membresia"][0]["fecha_fin"] == "2026-01-31"


def test_public_registration_ignores_payment_fields_from_browser() -> None:
    payload = RegistroPublicoClienteInput.model_validate({
        "nombre": "Cliente",
        "correo": "cliente@example.com",
        "dni": "12345678",
        "password": "secreto",
        "metodo_pago": "atacante",
        "referencia_pago": "referencia-repetida",
    }).model_dump()

    assert "metodo_pago" not in payload
    assert "referencia_pago" not in payload
