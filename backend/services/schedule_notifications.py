"""Avisos de matrícula y recordatorios de clases con Gmail y una cola privada."""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from html import escape
import logging
from urllib.parse import urlsplit
from uuid import uuid4
from zoneinfo import ZoneInfo

from config import Settings
from services.email_service import GmailEmailService, _email, _gmail_sender
from services.supabase_gym_service import SupabaseRestClient

logger = logging.getLogger(__name__)
LIMA = ZoneInfo("America/Lima")
TABLE = "schedule_email_notifications"
DAYS = {"lunes": "Lunes", "martes": "Martes", "miercoles": "Miércoles", "jueves": "Jueves",
        "viernes": "Viernes", "sabado": "Sábado", "domingo": "Domingo"}
SERVICES = {"fitness": "Fitness", "musculacion": "Musculación", "cardio": "Cardio", "baile": "Baile"}


def schedule_email(settings: Settings, data: dict) -> dict:
    event = data["event_type"]
    if event not in {"enrollment", "reminder"}:
        raise ValueError("Tipo de aviso de horario inválido")
    recipient = _email(str(data.get("correo") or ""))
    _, sender = _gmail_sender(settings)
    base = settings.frontend_public_url.rstrip("/")
    if urlsplit(base).scheme not in {"http", "https"} or not urlsplit(base).netloc:
        raise ValueError("Configura FRONTEND_PUBLIC_URL para el enlace al horario")
    start = time.fromisoformat(data["hora_inicio"]).strftime("%H:%M")
    end = time.fromisoformat(data["hora_fin"]).strftime("%H:%M")
    service = SERVICES[data["servicio"]]
    day = DAYS[data["dia"]]
    name = str(data.get("nombre") or "Cliente")
    details = [("Clase", service), ("Día", day), ("Horario", f"{start} – {end}"), ("Zona horaria", "Perú (America/Lima)")]
    if event == "enrollment":
        title = "El administrador te inscribió en una clase"
        description = "Se agregó una clase a tu horario. Revisa los datos de tu matrícula:"
        details.append(("Frecuencia", f"Cada {day.lower()}, mientras tu matrícula y membresía estén vigentes"))
        subject = f"Inscripción confirmada: {service} · Silver Gym Surco"
    else:
        occurrence = datetime.fromisoformat(data["class_start"]).astimezone(LIMA)
        details.insert(2, ("Fecha", occurrence.strftime("%d/%m/%Y")))
        title = "Te esperamos en tu próxima clase"
        # No afirma «falta una hora»: un reintento de SMTP puede llegar más tarde.
        description = "Te recordamos tu clase programada. Revisa la hora de inicio y prepárate para entrenar."
        subject = f"Recordatorio: {service} a las {start} · Silver Gym Surco"
    url = f"{base}/user/schedule"
    rows = "".join(
        f'<tr><td style="padding:10px;border-bottom:1px solid #eee;color:#555">{escape(label)}</td>'
        f'<td style="padding:10px;border-bottom:1px solid #eee">{escape(value)}</td></tr>'
        for label, value in details
    )
    html = (
        '<!doctype html><html lang="es"><body style="margin:0;background:#f5f5f5;font-family:Arial,sans-serif;color:#171717">'
        '<main style="max-width:620px;margin:24px auto;padding:32px;background:#fff;border-radius:16px">'
        '<p style="color:#dc2626;font-weight:bold">Silver Gym Surco</p>'
        f'<h1 style="font-size:26px">{escape(title)}</h1><p>Hola, {escape(name)}.</p>'
        f'<p style="line-height:1.6">{escape(description)}</p><table style="width:100%;border-collapse:collapse">{rows}</table>'
        f'<p style="margin:28px 0"><a href="{escape(url, quote=True)}" style="background:#dc2626;color:#fff;padding:14px 24px;'
        'border-radius:8px;text-decoration:none">Ver mi horario</a></p>'
        '<p style="font-size:12px;color:#666">Si necesitas cambiar tu clase, comunícate con administración.</p></main></body></html>'
    )
    text = f"Silver Gym Surco\n{title}\n\nHola, {name}.\n{description}\n\n"
    text += "\n".join(f"{label}: {value}" for label, value in details)
    text += f"\n\nVer mi horario: {url}"
    return {"from": sender, "to": [recipient], "subject": subject, "html": html, "text": text}


class ScheduleNotificationRepository:
    def __init__(self, settings: Settings):
        self.db = SupabaseRestClient(settings.supabase_url, settings.supabase_key)

    def enqueue_due(self):
        return self.db.rpc("enqueue_due_schedule_reminders", {})

    def claim(self, event_key=None):
        rows = self.db.rpc("claim_schedule_email", {"p_claim_token": str(uuid4()), "p_event_key": event_key})
        return rows[0] if rows else None

    def delivery_context(self, job):
        return self.db.rpc("schedule_email_delivery_context", {
            "p_event_key": job["event_key"], "p_claim_token": job["claim_token"],
        })

    def finish(self, job, *, delivery_id="", error="", cancelled=False):
        now = datetime.now(timezone.utc)
        if cancelled:
            values = {"status": "cancelled", "last_error": "La matrícula, el horario o la fecha ya no corresponden."}
        elif delivery_id:
            values = {"status": "sent", "delivery_id": delivery_id, "sent_at": now.isoformat(), "last_error": None}
        else:
            delay = min(900, 30 * 2 ** min(int(job.get("attempts") or 1) - 1, 5))
            values = {"status": "pending", "last_error": error, "available_at": (now + timedelta(seconds=delay)).isoformat()}
        rows = self.db._request("PATCH", TABLE, query={
            "event_key": f"eq.{job['event_key']}", "claim_token": f"eq.{job['claim_token']}", "status": "eq.processing",
        }, body={**values, "claim_token": None, "locked_until": None}, return_representation=True)
        if not rows:
            raise RuntimeError("No se pudo guardar el resultado del aviso de horario")


class ScheduleNotificationService:
    def __init__(self, settings: Settings, repository=None, sender=None):
        self.settings = settings
        self.repository = repository or ScheduleNotificationRepository(settings)
        self.sender = sender or GmailEmailService(settings)

    @property
    def configured(self):
        return self.settings.has_gmail_credentials and self.settings.has_supabase_credentials

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


def notify_schedule_enrollment(settings: Settings, enrollment_id: int):
    service = ScheduleNotificationService(settings)
    if not service.configured:
        return {"status": "queued", "message": "La confirmación quedó en cola para su envío desde Supabase."}
    try:
        return service.process_one(f"enrollment/{enrollment_id}") or {
            "status": "queued", "message": "La confirmación por correo quedó programada.",
        }
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        # La matrícula y la cola ya se confirmaron en una única transacción.
        logger.warning("Aviso de matrícula pendiente (%s). Revisa Gmail, Supabase y la migración 006.", type(error).__name__)
        return {"status": "queued", "message": "El correo está pendiente; se reintentará automáticamente."}
