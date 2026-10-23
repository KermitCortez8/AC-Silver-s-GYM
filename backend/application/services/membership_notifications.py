"""Cola persistente de correos, con reintentos y deduplicación por membresía/evento."""
from __future__ import annotations

import asyncio
import logging


from application.services.email_templates import membership_email
from application.ports.integrations import EmailSender, MembershipNotificationQueue

logger = logging.getLogger(__name__)


class MembershipNotificationService:
    def __init__(self, settings, *, repository: MembershipNotificationQueue, sender: EmailSender) -> None:
        self.settings = settings
        self.repository = repository
        self.sender = sender

    @property
    def configured(self) -> bool:
        return bool(self.settings.has_email_credentials and self.settings.has_supabase_credentials)

    def notify(self, event: str, saved: dict, plan: dict) -> dict:
        if not self.configured:
            return {"status": "not_configured", "message": "El servicio de correo todavía no está configurado."}
        try:
            membership_id = int(saved["membresia"]["id_membresia"])
            event_key = f"membership/{membership_id}/{event}"
            payload = membership_email(self.settings, event, saved, plan)
            job = self.repository.enqueue(event_key, membership_id, event, payload)
            if job["status"] == "sent":
                return {"status": "sent", "message": "El correo ya fue enviado."}
            return self.process_one(event_key) or {"status": "queued", "message": "El correo está pendiente de envío."}
        except (RuntimeError, OSError, ValueError, KeyError) as error:
            # El pago o la activación ya se guardaron. Un fallo del correo no los revierte.
            logger.warning("No se pudo preparar el correo de membresía (%s). Revisa Resend y la migración 004.", type(error).__name__)
            return {"status": "error", "message": "No se pudo preparar el correo. Revisa la configuración y reintenta el envío."}

    def process_one(self, event_key: str | None = None) -> dict | None:
        if not self.configured:
            return None
        job = self.repository.claim(event_key)
        if not job:
            return None
        try:
            # Se conserva el contenido de la compra; el remitente es la cuenta Resend configurada.
            delivery_id = self.sender.send(job["payload"], job["event_key"])
        except (RuntimeError, OSError) as error:
            self.repository.finish(job, error=str(error))
            logger.warning("Correo %s pendiente; se reintentará automáticamente.", job["event_key"])
            return {"status": "queued", "message": "El correo se reintentará automáticamente."}
        self.repository.finish(job, delivery_id=delivery_id)
        return {"status": "sent", "message": "Correo enviado."}


def notify_membership(service: MembershipNotificationService, clients_service, saved: dict, event: str) -> dict:
    settings = service.settings
    if not getattr(settings, "has_email_credentials", False):
        return {"status": "not_configured", "message": "El servicio de correo todavía no está configurado."}
    if not service.configured:
        return {"status": "not_configured", "message": "El servicio de correo todavía no está configurado."}
    try:
        plan = clients_service.gym.get_plan_membresia(int(saved["membresia"]["id_pm"])) or {}
        return service.notify(event, saved, plan)
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        logger.warning("No se pudieron preparar los datos del correo (%s).", type(error).__name__)
        return {"status": "error", "message": "No se pudo preparar el correo. Reintenta el envío."}


async def process_pending_emails(service: MembershipNotificationService) -> None:
    if not service.configured:
        logger.info("Notificaciones de membresía deshabilitadas: configura RESEND_API_KEY y EMAIL_FROM.")
        return
    while True:
        try:
            result = await asyncio.to_thread(service.process_one)
        except (RuntimeError, OSError, ValueError):
            logger.warning("No se pudo procesar la cola de correos. Revisa Supabase y 004_membership_email_notifications.sql.")
            result = None
        await asyncio.sleep(1 if result else 30)
