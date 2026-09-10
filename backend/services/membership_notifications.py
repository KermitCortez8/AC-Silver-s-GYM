"""Cola persistente de correos, con reintentos y deduplicación por membresía/evento."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from uuid import uuid4

from config import Settings
from services.email_service import GmailEmailService, membership_email
from services.supabase_gym_service import SupabaseRestClient

logger = logging.getLogger(__name__)
TABLE = "membership_email_notifications"


class NotificationRepository:
    def __init__(self, settings: Settings) -> None:
        self.db = SupabaseRestClient(settings.supabase_url, settings.supabase_key)

    def enqueue(self, event_key: str, membership_id: int, event: str, payload: dict) -> dict:
        rows = self.db.rpc("enqueue_membership_email", {
            "p_event_key": event_key, "p_id_membresia": membership_id,
            "p_event_type": event, "p_payload": payload,
        })
        if not rows:
            raise RuntimeError("No se pudo guardar la notificación")
        return rows[0]

    def claim(self, event_key: str | None = None) -> dict | None:
        rows = self.db.rpc("claim_membership_email", {"p_claim_token": str(uuid4()), "p_event_key": event_key})
        return rows[0] if rows else None

    def finish(self, job: dict, *, delivery_id: str = "", error: str = "") -> None:
        now = datetime.now(timezone.utc)
        if delivery_id:
            # Se conserva el nombre de columna para instalaciones que ya aplicaron la migración 004.
            body = {"status": "sent", "resend_id": delivery_id, "sent_at": now.isoformat(), "last_error": None}
        else:
            delay = min(3600, 30 * 2 ** min(int(job.get("attempts") or 1) - 1, 7))
            body = {"status": "pending", "available_at": (now + timedelta(seconds=delay)).isoformat(), "last_error": error}
        rows = self.db._request(
            "PATCH", TABLE,
            query={"event_key": f"eq.{job['event_key']}", "claim_token": f"eq.{job['claim_token']}", "status": "eq.processing"},
            body={**body, "locked_until": None, "claim_token": None}, return_representation=True,
        )
        if not rows:
            raise RuntimeError("No se pudo registrar el resultado del correo")


class MembershipNotificationService:
    def __init__(self, settings: Settings, repository=None, sender=None) -> None:
        self.settings = settings
        self.repository = repository or NotificationRepository(settings)
        self.sender = sender or GmailEmailService(settings)

    @property
    def configured(self) -> bool:
        return bool(self.settings.has_gmail_credentials and self.settings.has_supabase_credentials)

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
            logger.warning("No se pudo preparar el correo de membresía (%s). Revisa Gmail y la migración 004.", type(error).__name__)
            return {"status": "error", "message": "No se pudo preparar el correo. Revisa la configuración y reintenta el envío."}

    def process_one(self, event_key: str | None = None) -> dict | None:
        if not self.configured:
            return None
        job = self.repository.claim(event_key)
        if not job:
            return None
        try:
            # Se conserva el contenido de la compra; el remitente es la cuenta Gmail configurada.
            delivery_id = self.sender.send(job["payload"], job["event_key"])
        except (RuntimeError, OSError) as error:
            self.repository.finish(job, error=str(error))
            logger.warning("Correo %s pendiente; se reintentará automáticamente.", job["event_key"])
            return {"status": "queued", "message": "El correo se reintentará automáticamente."}
        self.repository.finish(job, delivery_id=delivery_id)
        return {"status": "sent", "message": "Correo enviado."}


def notify_membership(settings: Settings, clients_service, saved: dict, event: str) -> dict:
    if not getattr(settings, "has_gmail_credentials", False):
        return {"status": "not_configured", "message": "El servicio de correo todavía no está configurado."}
    service = MembershipNotificationService(settings)
    if not service.configured:
        return {"status": "not_configured", "message": "El servicio de correo todavía no está configurado."}
    try:
        plan = clients_service.gym.get_plan_membresia(int(saved["membresia"]["id_pm"])) or {}
        return service.notify(event, saved, plan)
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        logger.warning("No se pudieron preparar los datos del correo (%s).", type(error).__name__)
        return {"status": "error", "message": "No se pudo preparar el correo. Reintenta el envío."}


async def process_pending_emails(settings: Settings) -> None:
    service = MembershipNotificationService(settings)
    if not service.configured:
        logger.info("Notificaciones de membresía deshabilitadas: configura GMAIL_EMAIL y GMAIL_APP_PASSWORD.")
        return
    while True:
        try:
            result = await asyncio.to_thread(service.process_one)
        except (RuntimeError, OSError, ValueError):
            logger.warning("No se pudo procesar la cola de correos. Revisa Supabase y 004_membership_email_notifications.sql.")
            result = None
        await asyncio.sleep(1 if result else 30)
