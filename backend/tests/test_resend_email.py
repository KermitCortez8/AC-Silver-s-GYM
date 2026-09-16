from copy import deepcopy
from io import BytesIO
import json
from urllib.error import HTTPError, URLError

import pytest

from config import Settings, get_settings
from services import email_service
from services.email_service import ResendEmailService, membership_email
from services.membership_notifications import MembershipNotificationService
from services.schedule_notifications import ScheduleNotificationService, schedule_email


@pytest.fixture
def settings():
    return Settings(
        resend_api_key="re_test_private", email_from="onboarding@resend.dev",
        supabase_url="https://gym.supabase.co", supabase_key="test-db-key",
        frontend_public_url="https://gym.vercel.app",
    )


@pytest.fixture
def payload():
    return {
        "from": "Old Sender <old@gmail.com>", "to": ["client@example.com"],
        "subject": "Membresía", "text": "Activa", "html": "<p>Activa</p>",
    }


def test_https_sender_preserves_recipient_and_updates_queued_sender(monkeypatch, settings, payload):
    calls = []

    def send(request, timeout):
        calls.append(request)
        assert timeout == 15
        return BytesIO(b'{"id":"email-123"}')

    monkeypatch.setattr(email_service, "urlopen", send)
    original = deepcopy(payload)
    sender = ResendEmailService(settings)
    assert sender.send(payload, "enrollment/12") == "email-123"
    sender.send(payload, "enrollment/12")
    sender.send(payload, "enrollment/13")
    settings.supabase_url = "https://other.supabase.co"
    sender.send(payload, "enrollment/12")
    assert payload == original
    request = calls[0]
    assert request.full_url == "https://api.resend.com/emails"
    assert request.method == "POST"
    assert request.get_header("Authorization") == "Bearer re_test_private"
    assert json.loads(request.data) == {**payload, "from": "Silver Gym Surco <onboarding@resend.dev>"}
    keys = [r.get_header("Idempotency-key") for r in calls]
    assert keys[0] == keys[1]
    assert len(set(keys)) == 3


@pytest.mark.parametrize("status", [401, 403, 409, 422, 429, 500])
def test_provider_errors_are_safe_for_queue_and_logs(monkeypatch, settings, payload, status):
    def reject(*args, **kwargs):
        raise HTTPError("https://api.resend.com/emails", status, "error", {},
                        BytesIO(b'{"message":"re_test_private client@example.com"}'))

    monkeypatch.setattr(email_service, "urlopen", reject)
    with pytest.raises(RuntimeError) as failure:
        ResendEmailService(settings).send(payload, "membership/1/payment")
    assert "Resend" in str(failure.value)
    assert "re_test_private" not in str(failure.value)
    assert "client@example.com" not in str(failure.value)


@pytest.mark.parametrize("response", [b'{}', b'null', b'{"id":null}', b'not json'])
def test_no_delivery_id_is_not_reported_as_sent(monkeypatch, settings, payload, response):
    monkeypatch.setattr(email_service, "urlopen", lambda *a, **kw: BytesIO(response))
    with pytest.raises(RuntimeError):
        ResendEmailService(settings).send(payload, "membership/1/payment")


def test_timeout_keeps_membership_pending(monkeypatch, settings, payload):
    def fail(*args, **kwargs):
        raise URLError("timeout with sensitive details")

    monkeypatch.setattr(email_service, "urlopen", fail)
    outcomes = []

    class Repository:
        def claim(self, event_key):
            return {"payload": payload, "event_key": event_key}

        def finish(self, job, **outcome):
            outcomes.append(outcome)

    service = MembershipNotificationService(settings, repository=Repository())
    assert service.configured
    result = service.process_one("membership/1/payment")
    assert result["status"] == "queued"
    assert "error" in outcomes[0] and "delivery_id" not in outcomes[0]
    assert "sensitive" not in outcomes[0]["error"]


def test_success_records_provider_id_for_membership(monkeypatch, settings, payload):
    monkeypatch.setattr(email_service, "urlopen", lambda *a, **kw: BytesIO(b'{"id":"accepted-id"}'))
    outcomes = []

    class Repository:
        def claim(self, event_key):
            return {"payload": payload, "event_key": event_key}

        def finish(self, job, **outcome):
            outcomes.append(outcome)

    result = MembershipNotificationService(settings, repository=Repository()).process_one("membership/1/payment")
    assert result["status"] == "sent"
    assert outcomes == [{"delivery_id": "accepted-id"}]


def test_schedule_cancelled_before_sending_when_enrollment_changes(settings):
    outcomes = []

    class Repository:
        def claim(self, event_key):
            return {"event_key": event_key}

        def delivery_context(self, job):
            return None

        def finish(self, job, **outcome):
            outcomes.append(outcome)

    class NoSend:
        def send(self, *args):
            pytest.fail("No debe enviar un aviso cancelado")

    service = ScheduleNotificationService(settings, repository=Repository(), sender=NoSend())
    assert service.configured
    assert service.process_one("enrollment/12")["status"] == "cancelled"
    assert outcomes == [{"cancelled": True}]


def test_templates_work_without_gmail(settings):
    saved = {"cliente": {"id_cliente": 1, "correo": "client@example.com", "estado": "ACTIVO"},
             "membresia": {"estado_pago": "PAGADO", "estado": "ACTIVO", "monto_pago": 79}}
    result = membership_email(settings, "activation", saved, {"nombre_plan": "Mensual"})
    assert result["from"] == "Silver Gym Surco <onboarding@resend.dev>"
    assert "https://gym.vercel.app/login" in result["html"]
    saved["membresia"]["estado_pago"] = "PENDIENTE"
    with pytest.raises(ValueError, match="pago confirmado"):
        membership_email(settings, "payment", saved, {})
    schedule = schedule_email(settings, {
        "event_type": "enrollment", "correo": "client@example.com", "nombre": "Ana",
        "hora_inicio": "09:00", "hora_fin": "10:00", "dia": "lunes", "servicio": "fitness",
    })
    assert "https://gym.vercel.app/user/schedule" in schedule["html"]


def test_missing_key_disables_notifications_and_key_is_private(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_environment_test")
    monkeypatch.setenv("EMAIL_FROM", "onboarding@resend.dev")
    get_settings.cache_clear()
    try:
        configured = get_settings()
        assert configured.has_email_credentials
        assert "re_environment_test" not in repr(configured)
        assert "resend_api_key" not in configured.model_dump()
    finally:
        get_settings.cache_clear()
    assert not Settings().has_email_credentials
