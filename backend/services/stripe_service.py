# Módulo: stripe_service.
# Crea sesiones alojadas de Stripe Checkout para las membresías.
# Recupera sesiones y valida la firma de los webhooks de Stripe.
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

import stripe

from config import Settings


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


class StripeService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.stripe_secret_key)

    def validate_configuration(self) -> None:
        key = self.settings.stripe_secret_key
        mode = self.settings.stripe_mode
        if not key:
            raise RuntimeError("Stripe no está configurado")
        if mode not in {"test", "live"}:
            raise RuntimeError("STRIPE_MODE debe ser test o live")
        expected_prefix = "sk_test_" if mode == "test" else "sk_live_"
        if not key.startswith(expected_prefix):
            raise RuntimeError(
                f"STRIPE_SECRET_KEY no corresponde a STRIPE_MODE={mode}"
            )
        if not self.settings.stripe_webhook_secret.startswith("whsec_"):
            raise RuntimeError("Falta configurar un STRIPE_WEBHOOK_SECRET válido")

    @staticmethod
    def _amount_in_cents(value: Any) -> int:
        try:
            amount = Decimal(str(value or "0"))
        except InvalidOperation as error:
            raise ValueError("El precio de la membresía no es válido") from error
        cents = int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if cents <= 0:
            raise ValueError("El precio de la membresía debe ser mayor que cero")
        return cents

    def create_membership_checkout(self, result: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            return {"configured": False, "message": "Stripe no está configurado"}
        self.validate_configuration()

        client = result.get("cliente") or {}
        membership = result.get("membresia") or {}
        plan = result.get("plan") or {}
        client_id = int(client.get("id_cliente", 0) or 0)
        membership_id = int(membership.get("id_membresia", 0) or 0)
        if not client_id:
            raise ValueError("No se pudo determinar el cliente de la membresía")

        amount_in_cents = self._amount_in_cents(membership.get("monto_pago") or plan.get("precio"))
        return_url = f"{self.settings.frontend_public_url}/registro/pago/{client_id}"
        metadata = {
            "purpose": "membership",
            "client_id": str(client_id),
            "membership_id": str(membership_id),
        }
        product_data: dict[str, str] = {
            "name": f"Membresía {plan.get('nombre_plan', 'Silver Gym')}",
        }
        description = str(plan.get("descripcion") or "").strip()
        if description:
            product_data["description"] = description

        try:
            session = stripe.checkout.Session.create(
                api_key=self.settings.stripe_secret_key,
                mode="payment",
                payment_method_types=["card"],
                client_reference_id=f"membership:{client_id}",
                customer_email=str(client.get("correo") or "").strip(),
                line_items=[{
                    "price_data": {
                        "currency": "pen",
                        "unit_amount": amount_in_cents,
                        "product_data": product_data,
                    },
                    "quantity": 1,
                }],
                metadata=metadata,
                payment_intent_data={"metadata": metadata},
                success_url=f"{return_url}?result=success&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{return_url}?result=failure",
                locale="es",
                submit_type="pay",
                idempotency_key=f"membership-checkout-{membership_id or client_id}",
            )
        except Exception as error:
            raise RuntimeError("Stripe rechazó la creación del checkout") from error

        session_id = str(_value(session, "id", "") or "")
        checkout_url = str(_value(session, "url", "") or "")
        if not session_id or not checkout_url:
            raise RuntimeError("Stripe no devolvió una sesión de pago válida")
        return {
            "configured": True,
            "session_id": session_id,
            "checkout_url": checkout_url,
            "amount": amount_in_cents / 100,
            "currency": "PEN",
        }

    def get_checkout_session(self, session_id: str) -> Any:
        self.validate_configuration()
        try:
            return stripe.checkout.Session.retrieve(
                session_id,
                api_key=self.settings.stripe_secret_key,
            )
        except Exception as error:
            raise RuntimeError("No se pudo verificar la sesión de pago en Stripe") from error

    def construct_webhook_event(self, payload: bytes, signature: str) -> Any:
        if not self.settings.stripe_webhook_secret:
            raise RuntimeError("Falta configurar STRIPE_WEBHOOK_SECRET")
        if not signature:
            raise ValueError("Falta la firma del webhook de Stripe")
        try:
            return stripe.Webhook.construct_event(
                payload,
                signature,
                self.settings.stripe_webhook_secret,
            )
        except Exception as error:
            raise ValueError("Firma de webhook de Stripe inválida") from error
