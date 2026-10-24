"""Avisos de matrícula y recordatorios de clases con Resend y una cola privada."""
from __future__ import annotations

import logging


from application.services.email_templates import schedule_email
from application.ports.integrations import EmailSender, ScheduleNotificationQueue

logger = logging.getLogger(__name__)


class ScheduleNotificationService:
    def __init__(self, settings, *, repository: ScheduleNotificationQueue, sender: EmailSender):
        self.settings = settings
        self.repository = repository
        self.sender = sender

    @property
    def configured(self):
        return self.settings.has_email_credentials and self.settings.has_supabase_credentials

    def process_one(self, event_key=None):
        if not self.configured:
            return None
        job = self.repository.claim(event_key)
        if not job:
            return None
        data = self.repository.delivery_context(job)
        if not data:
            self.repository.finish(job, cancelled=True)
            return {"status": "cancelled", "message": "El aviso se omitió porque la matrícula o el horario cambiaron."}
        try:
            payload = schedule_email(self.settings, data)
            delivery_id = self.sender.send(payload, job["event_key"])
        except (ValueError, KeyError) as error:
            self.repository.finish(job, error="Revisa el correo del cliente y los datos de su horario.")
            logger.warning("Datos incompletos en el aviso de horario (%s).", type(error).__name__)
            return {"status": "queued", "message": "El correo está pendiente. Revisa el correo del cliente y su horario."}
        except (RuntimeError, OSError) as error:
            self.repository.finish(job, error=str(error))
            return {"status": "queued", "message": "El correo está pendiente; se reintentará automáticamente."}
        self.repository.finish(job, delivery_id=delivery_id)
        return {"status": "sent", "message": "Se envió la confirmación al correo del cliente."}


def notify_schedule_enrollment(service: ScheduleNotificationService, enrollment_id: int):
    if not service.configured:
        return {"status": "queued", "message": "La confirmación quedó en cola para su envío desde Supabase."}
    try:
        return service.process_one(f"enrollment/{enrollment_id}") or {
            "status": "queued", "message": "La confirmación por correo quedó programada.",
        }
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        # La matrícula y la cola ya se confirmaron en una única transacción.
        logger.warning("Aviso de matrícula pendiente (%s). Revisa Resend, Supabase y la migración 006.", type(error).__name__)
        return {"status": "queued", "message": "El correo está pendiente; se reintentará automáticamente."}
