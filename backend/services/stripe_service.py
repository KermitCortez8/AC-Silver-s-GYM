# Módulo: stripe_service.
# Crea sesiones alojadas de Stripe Checkout para las membresías.
# Recupera sesiones y valida la firma de los webhooks de Stripe.
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from typing import Any
import logging
import time
import stripe

from config import Settings

logger = logging.getLogger(__name__)
# Stripe exige que la sesión dure como mínimo 30 minutos; se usan 31 para no quedar al límite por diferencias de reloj.
STORE_CHECKOUT_MINUTES = 31

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

        checkout_params = dict(
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
        )
        # Stripe exige los mismos parámetros al reutilizar una clave. El hash
        # mantiene los reintentos estables y distingue cambios de URL o importe.
        fingerprint = hashlib.sha256(json.dumps(
            checkout_params, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        try:
            session = stripe.checkout.Session.create(
                api_key=self.settings.stripe_secret_key,
                idempotency_key=f"membership-checkout-v2-{membership_id or client_id}-{fingerprint}",
                **checkout_params,
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

    def create_store_checkout(
        self,
        pedido: dict[str, Any],
        *,
        customer_email: str = "",
        user_id: str = "",
    ) -> dict[str, Any]:
        """Crea la sesión de Stripe Checkout de un pedido de tienda. Los importes salen del pedido, no del navegador."""
        if not self.configured:
            return {"configured": False, "message": "Stripe no está configurado"}
        self.validate_configuration()

        id_pedido = int(pedido.get("id_pedido", 0) or 0)
        if not id_pedido:
            raise ValueError("No se pudo determinar el pedido")

        line_items: list[dict[str, Any]] = []
        items_total = 0
        for item in pedido.get("items") or []:
            unit_amount = self._amount_in_cents(item.get("precio_unitario"))
            quantity = max(1, int(item.get("cantidad") or 1))
            items_total += unit_amount * quantity
            line_items.append({
                "price_data": {
                    "currency": "pen",
                    "unit_amount": unit_amount,
                    "product_data": {"name": str(item.get("nombre_producto") or "Producto")[:250]},
                },
                "quantity": quantity,
            })
        if not line_items:
            raise ValueError("El pedido no tiene productos")

        # El IGV va como una línea aparte para que el total cobrado sea exactamente el total del pedido.
        igv_cents = int((Decimal(str(pedido.get("igv") or 0)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if igv_cents > 0:
            items_total += igv_cents
            line_items.append({
                "price_data": {
                    "currency": "pen",
                    "unit_amount": igv_cents,
                    "product_data": {"name": "IGV (18%)"},
                },
                "quantity": 1,
            })
        if items_total != self._amount_in_cents(pedido.get("total")):
            raise ValueError("Los importes del pedido no coinciden con el cobro de Stripe")

        return_url = f"{self.settings.frontend_public_url}/user/store/payment"
        metadata = {
            "purpose": "store",
            "pedido_id": str(id_pedido),
            "client_id": str(pedido.get("id_cliente") or ""),
            "user_id": str(user_id or ""),
        }
        checkout_params: dict[str, Any] = dict(
            mode="payment",
            payment_method_types=["card"],
            client_reference_id=f"store:{id_pedido}",
            line_items=line_items,
            metadata=metadata,
            payment_intent_data={"metadata": metadata},
            success_url=f"{return_url}?result=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{return_url}?result=cancel&pedido={id_pedido}",
            locale="es",
            submit_type="pay",
        )
        email = str(customer_email or "").strip()
        if email:
            checkout_params["customer_email"] = email
        fingerprint = hashlib.sha256(json.dumps(
            checkout_params, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        # La expiración depende de la hora: se agrega después de calcular la huella de la clave de idempotencia.
        checkout_params["expires_at"] = int(time.time()) + STORE_CHECKOUT_MINUTES * 60
        try:
            session = stripe.checkout.Session.create(
                api_key=self.settings.stripe_secret_key,
                idempotency_key=f"store-checkout-v1-{id_pedido}-{fingerprint}",
                **checkout_params,
            )
        except Exception as error:
            logger.warning("Stripe rechazó el checkout del pedido %s: %s", id_pedido, error)
            raise RuntimeError("Stripe rechazó la creación del checkout") from error

        session_id = str(_value(session, "id", "") or "")
        checkout_url = str(_value(session, "url", "") or "")
        if not session_id or not checkout_url:
            raise RuntimeError("Stripe no devolvió una sesión de pago válida")
        return {
            "configured": True,
            "session_id": session_id,
            "checkout_url": checkout_url,
            "amount": items_total / 100,
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

    def expire_checkout_session(self, session_id: str) -> Any:
        """Cierra una sesión abierta para que nadie pueda pagarla. Devuelve la sesión con su estado real."""
        session = self.get_checkout_session(session_id)
        if str(_value(session, "status", "") or "").lower() != "open":
            return session
        try:
            return stripe.checkout.Session.expire(session_id, api_key=self.settings.stripe_secret_key)
        except Exception:
            # Puede haberse completado justo antes de expirar: se consulta de nuevo para decidir con el estado real.
            return self.get_checkout_session(session_id)

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
