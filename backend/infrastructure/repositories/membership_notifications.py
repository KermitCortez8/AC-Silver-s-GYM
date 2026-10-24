"""Cola persistente de avisos en Supabase."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from infrastructure.config import Settings
from infrastructure.supabase_client import SupabaseRestClient

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
        rows = self.db.update_matching(
            TABLE,
            filters={"event_key": f"eq.{job['event_key']}", "claim_token": f"eq.{job['claim_token']}", "status": "eq.processing"},
            body={**body, "locked_until": None, "claim_token": None},
        )
        if not rows:
            raise RuntimeError("No se pudo registrar el resultado del correo")
