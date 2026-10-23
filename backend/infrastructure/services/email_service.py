"""Plantillas y envío de correos mediante la API HTTPS de Resend."""
from __future__ import annotations

from hashlib import sha256
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from infrastructure.config import Settings


# Reexportaciones conservadas para consumidores de las plantillas anteriores.
from application.services.email_templates import _email, email_sender, membership_email


class ResendEmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, payload: dict, event_key: str) -> str:
        if not self.settings.has_email_credentials:
            raise RuntimeError("Configura RESEND_API_KEY y EMAIL_FROM para enviar correos.")
        try:
            _, sender = email_sender(self.settings)
            recipients = payload.get("to")
            if not isinstance(recipients, list) or len(recipients) != 1:
                raise ValueError("La notificación debe tener un único destinatario")
            # Actualiza también el remitente de mensajes encolados antes de migrar de Gmail.
            body = {
                "from": sender,
                "to": [_email(str(recipients[0]))],
                "subject": str(payload["subject"]),
                "html": str(payload["html"]),
                "text": str(payload["text"]),
            }
            # Misma clave en Python y Supabase: un proyecto y evento identifican el envío.
            digest = sha256(f"{self.settings.supabase_url.rstrip('/')}|{event_key}".encode()).hexdigest()
            request = Request(
                "https://api.resend.com/emails",
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.settings.resend_api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "AC-Silvers-GYM/1.1",
                    "Idempotency-Key": f"gym-{digest}",
                },
                method="POST",
            )
            with urlopen(request, timeout=15) as response:
                result = json.load(response)
            delivery_id = result.get("id") if isinstance(result, dict) else None
            if not isinstance(delivery_id, str) or not delivery_id.strip():
                raise RuntimeError("Resend no confirmó el envío; se reintentará.")
            return delivery_id
        except HTTPError as error:
            # Nunca persistir el cuerpo del proveedor: puede contener direcciones o credenciales.
            messages = {
                401: "Resend rechazó la clave. Revisa RESEND_API_KEY.",
                403: "Resend rechazó el envío. Revisa el remitente y el destinatario permitido para pruebas.",
                409: "Resend detectó un conflicto de envío. Conserva el contenido y remitente del evento al reintentar.",
                422: "Resend rechazó los datos. Revisa EMAIL_FROM y el correo del cliente.",
                429: "Se alcanzó el límite de Resend; el correo queda pendiente de reintento.",
            }
            raise RuntimeError(messages.get(error.code, "Resend no está disponible; se reintentará.")) from error
        except OSError as error:
            raise RuntimeError("No se pudo confirmar el envío con Resend; se reintentará.") from error
        except (ValueError, KeyError) as error:
            raise RuntimeError("Revisa la configuración de Resend y los datos del correo.") from error
