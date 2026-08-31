# Módulo: mercado_pago_service.
# Crea preferencias de Checkout Pro para las membresías.
# Valida la firma del webhook antes de consultar un pago.
# Mantiene las credenciales de Mercado Pago dentro del backend.
from __future__ import annotations

from typing import Any

import mercadopago
from mercadopago.webhook import InvalidWebhookSignatureError, WebhookSignatureValidator

from config import Settings


class MercadoPagoService:
    # Inicializa la clase.
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.sdk = mercadopago.SDK(settings.mercado_pago_access_token) if settings.mercado_pago_access_token else None

    @property
    # Procesa esta operación.
    def configured(self) -> bool:
        return self.sdk is not None

    # Crea el registro correspondiente.
    def create_membership_checkout(self, result: dict[str, Any]) -> dict[str, Any]:
        if not self.sdk:
            return {"configured": False, "message": "Mercado Pago no está configurado"}

        client = result.get("cliente") or {}
        plan = result.get("plan") or {}
        client_id = int(client.get("id_cliente", 0) or 0)
        amount = float(plan.get("precio", 0) or 0)
        if not client_id or amount <= 0:
            raise ValueError("No se pudo determinar el cliente o importe de la membresía")

        return_url = f"{self.settings.frontend_public_url}/registro/pago/{client_id}"
        preference = {
            "items": [{
                "id": f"membresia-{plan.get('id_pm', 'gym')}",
                "title": f"Membresía {plan.get('nombre_plan', 'Silver Gym')}",
                "description": str(plan.get("descripcion") or "Membresía de Silver Gym"),
                "quantity": 1,
                "currency_id": "PEN",
                "unit_price": amount,
            }],
            "payer": {
                "name": str(client.get("nombre") or ""),
                "email": str(client.get("correo") or ""),
            },
            "external_reference": f"membership:{client_id}",
            "back_urls": {
                "success": f"{return_url}?result=success",
                "pending": f"{return_url}?result=pending",
                "failure": f"{return_url}?result=failure",
            },
            "auto_return": "approved",
            "statement_descriptor": "SILVER GYM",
        }
        if self.settings.backend_public_url:
            preference["notification_url"] = f"{self.settings.backend_public_url}/api/pagos/mercado-pago/webhook"

        response = self.sdk.preference().create(preference)
        if int(response.get("status", 500)) not in {200, 201}:
            raise RuntimeError("Mercado Pago rechazó la creación del checkout")
        data = response.get("response") or {}
        checkout_url = data.get("sandbox_init_point") if str(self.settings.mercado_pago_access_token).startswith("TEST-") else data.get("init_point")
        if not checkout_url:
            raise RuntimeError("Mercado Pago no devolvió una URL de pago")
        return {
            "configured": True,
            "preference_id": data.get("id"),
            "checkout_url": checkout_url,
            "amount": amount,
            "currency": "PEN",
        }

    # Valida los datos recibidos.
    def validate_webhook(self, signature: str, request_id: str, data_id: str) -> None:
        if not self.settings.mercado_pago_webhook_secret:
            raise RuntimeError("Falta configurar MERCADO_PAGO_WEBHOOK_SECRET")
        try:
            WebhookSignatureValidator.validate(
                signature,
                request_id,
                data_id,
                self.settings.mercado_pago_webhook_secret,
            )
        except InvalidWebhookSignatureError as error:
            raise ValueError("Firma de webhook inválida") from error

    # Obtiene los datos necesarios.
    def get_payment(self, payment_id: str) -> dict[str, Any]:
        if not self.sdk:
            raise RuntimeError("Mercado Pago no está configurado")
        response = self.sdk.payment().get(payment_id)
        if int(response.get("status", 500)) != 200:
            raise RuntimeError("No se pudo verificar el pago en Mercado Pago")
        return response.get("response") or {}
