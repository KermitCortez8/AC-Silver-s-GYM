"""TC-144/158/169/173: oráculos de notificación con cola y HTTPS simulados."""
from copy import deepcopy
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from application.services.clients_service import ClientsService
from application.services.membership_notifications import MembershipNotificationService
from infrastructure.config import Settings
from infrastructure.services import email_service
from infrastructure.services.email_service import ResendEmailService, membership_email
from infrastructure.services.local_gym_service import LocalGymService


class MemoryQueue:
    """Doble declarado del puerto; no afirma comprobar concurrencia SQL."""
    def __init__(self):
        self.jobs = {}

    def enqueue(self, event_key, membership_id, event, payload):
        return self.jobs.setdefault(event_key, {"event_key": event_key, "payload": deepcopy(payload), "status": "pending"})

    def claim(self, event_key):
        job = self.jobs.get(event_key)
        return job if job and job["status"] != "sent" else None

    def finish(self, job, **result):
        job.update(result, status="sent" if result.get("delivery_id") else "pending")


def config():
    return Settings(resend_api_key="re_synthetic_qa", supabase_url="https://example.invalid",
                    supabase_key="synthetic-not-a-real-key", frontend_public_url="https://gym.example")


def paid_membership():
    gym = LocalGymService()
    clients = ClientsService(gym)
    saved = clients.register_admin_client({"nombre": "Correo QA", "correo": "qa@example.com", "dni": "55555555",
                                          "telefono": "999999999", "password": "qa-sintetica", "plan": "MENSUAL"})
    paid = clients.confirm_public_payment(saved["cliente"]["id_cliente"], {
        "id_membresia": saved["membresia"]["id_membresia"], "monto_pago": saved["membresia"]["monto_pago"],
        "metodo_pago": "efectivo", "referencia_pago": "QA-pago-no-real"})
    return gym, paid, gym.get_plan_membresia(paid["membresia"]["id_pm"])


def test_tc158_plantilla_local_exige_pago_y_no_contacta_proveedor(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("La construcción de una plantilla no debe enviar HTTP")
    monkeypatch.setattr(email_service, "urlopen", forbidden)
    saved = {"cliente": {"id_cliente": 1, "correo": "qa@example.com", "nombre": "QA", "estado": "ACTIVO"},
             "membresia": {"estado_pago": "PAGADO", "estado": "ACTIVO", "monto_pago": 79}}
    payload = membership_email(config(), "activation", saved, {"nombre_plan": "Mensual"})
    assert payload["to"] == ["qa@example.com"]
    assert payload["subject"] and "https://gym.example/login" in payload["html"]
    saved["membresia"]["estado_pago"] = "PENDIENTE"
    with pytest.raises(ValueError, match="pago confirmado"):
        membership_email(config(), "payment", saved, {})


@pytest.mark.parametrize("problem", ["timeout", "sin-id", "http-400", "http-401", "http-429", "http-500"])
def test_tc144_tc169_tc173_fallo_reintento_y_deduplicacion_con_pago_conservado(monkeypatch, caplog, problem):
    gym, saved, plan = paid_membership()
    original = deepcopy(gym.state)
    queue = MemoryQueue()
    settings = config()
    service = MembershipNotificationService(settings, repository=queue, sender=ResendEmailService(settings))
    calls = []
    failing = [True]

    def send(request, **_kwargs):
        calls.append(request)
        if failing[0]:
            if problem == "timeout":
                raise URLError("marcador-privado-qa")
            if problem == "sin-id":
                return BytesIO(b'{}')
            raise HTTPError(request.full_url, int(problem.split("-")[1]), "error", {},
                            BytesIO(b'{"message":"marcador-privado-qa re_synthetic_qa"}'))
        return BytesIO(b'{"id":"delivery-qa-1"}')

    monkeypatch.setattr(email_service, "urlopen", send)
    result = service.notify("payment", saved, plan)
    assert result["status"] == "queued"
    [job] = queue.jobs.values()
    assert job["status"] == "pending" and not job.get("delivery_id")
    assert "marcador-privado-qa" not in str(result) + str(job.get("error")) + caplog.text
    assert "re_synthetic_qa" not in str(result) + str(job.get("error")) + caplog.text
    assert gym.state == original
    failing[0] = False
    assert service.notify("payment", saved, plan)["status"] == "sent"
    assert job["delivery_id"] == "delivery-qa-1"
    assert calls[0].get_header("Idempotency-key")
    assert calls[0].get_header("Idempotency-key") == calls[1].get_header("Idempotency-key")
    assert service.notify("payment", saved, plan)["status"] == "sent"
    assert len(calls) == 2 and len(queue.jobs) == 1
    assert gym.state == original
