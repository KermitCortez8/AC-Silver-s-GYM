from __future__ import annotations

from types import SimpleNamespace

import pytest

from config import Settings
import services.stripe_service as stripe_service


def _checkout(monkeypatch) -> tuple[dict, dict]:
    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        # stripe-python devuelve un StripeObject con atributos, no un dict.
        return SimpleNamespace(
            id="cs_test_123",
            url="https://checkout.stripe.com/c/pay/cs_test_123",
        )

    monkeypatch.setattr(stripe_service.stripe.checkout.Session, "create", fake_create)
    settings = Settings(
        stripe_secret_key="sk_test_example",
        stripe_webhook_secret="whsec_example",
        frontend_public_url="https://gym.example",
    )
    service = stripe_service.StripeService(settings)
    result = service.create_membership_checkout({
        "cliente": {"id_cliente": 12, "nombre": "Cliente", "correo": "cliente@example.com"},
        "membresia": {"id_membresia": 34, "monto_pago": "79.90"},
        "plan": {
            "id_pm": 1,
            "nombre_plan": "MENSUAL",
            # Simula que el administrador cambió el precio después de crear la
            # membresía: Checkout debe respetar el importe que quedó guardado.
            "precio": "99.90",
            "descripcion": "Acceso por treinta días",
        },
    })
    return result, captured


def test_checkout_creates_hosted_stripe_session(monkeypatch) -> None:
    result, checkout = _checkout(monkeypatch)

    assert result == {
        "configured": True,
        "session_id": "cs_test_123",
        "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_123",
        "amount": 79.9,
        "currency": "PEN",
    }
    assert checkout["mode"] == "payment"
    assert checkout["payment_method_types"] == ["card"]
    assert checkout["client_reference_id"] == "membership:12"
    assert checkout["customer_email"] == "cliente@example.com"
    assert checkout["line_items"][0]["price_data"]["currency"] == "pen"
    assert checkout["line_items"][0]["price_data"]["unit_amount"] == 7990
    assert checkout["metadata"] == {
        "purpose": "membership",
        "client_id": "12",
        "membership_id": "34",
    }
    assert checkout["success_url"] == (
        "https://gym.example/registro/pago/12?result=success&session_id={CHECKOUT_SESSION_ID}"
    )
    assert checkout["cancel_url"] == "https://gym.example/registro/pago/12?result=failure"
    assert checkout["idempotency_key"] == "membership-checkout-34"


def test_checkout_reports_missing_stripe_configuration() -> None:
    service = stripe_service.StripeService(Settings())

    assert service.create_membership_checkout({}) == {
        "configured": False,
        "message": "Stripe no está configurado",
    }


def test_checkout_rejects_live_key_in_test_mode() -> None:
    service = stripe_service.StripeService(Settings(
        stripe_secret_key="sk_live_example",
        stripe_mode="test",
    ))

    with pytest.raises(RuntimeError, match="STRIPE_MODE=test"):
        service.create_membership_checkout({})


def test_checkout_requires_webhook_before_accepting_payments() -> None:
    service = stripe_service.StripeService(Settings(
        stripe_secret_key="sk_test_example",
        stripe_mode="test",
    ))

    with pytest.raises(RuntimeError, match="STRIPE_WEBHOOK_SECRET"):
        service.create_membership_checkout({})


def test_webhook_validation_uses_raw_payload_and_signing_secret(monkeypatch) -> None:
    captured: dict = {}

    def fake_construct_event(payload, signature, secret):
        captured.update(payload=payload, signature=signature, secret=secret)
        return {"id": "evt_test", "type": "checkout.session.completed"}

    monkeypatch.setattr(stripe_service.stripe.Webhook, "construct_event", fake_construct_event)
    service = stripe_service.StripeService(Settings(stripe_webhook_secret="whsec_example"))

    event = service.construct_webhook_event(b'{"id":"evt_test"}', "t=1,v1=signature")

    assert event["id"] == "evt_test"
    assert captured == {
        "payload": b'{"id":"evt_test"}',
        "signature": "t=1,v1=signature",
        "secret": "whsec_example",
    }
