"""Cola persistente de avisos en Supabase."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from infrastructure.config import Settings
from infrastructure.supabase_client import SupabaseRestClient

TABLE = "schedule_email_notifications"


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
