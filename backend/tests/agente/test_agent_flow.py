"""Casos de aceptación de la consulta pública; no usan red ni base real."""

import pytest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from application.services.agent_budget import AgentBudget, RateLimitExceeded
from application.services.agent_service import AgentService, ConversationTopics
from domain.services.agent_policy import contains_sensitive, requests_private_action
from infrastructure.services.groq_agent_provider import GroqAgentProvider, ProviderUnavailable


class Catalog:
    def __init__(self):
        self.price = 80
        self.calls = []

    def planes_membresia(self):
        self.calls.append("planes")
        return [{"nombre_plan": "Mensual", "precio": self.price, "duracion": "30 días"}]

    def horarios_servicio(self, *, solo_activos):
        assert solo_activos is True
        self.calls.append("horarios")
        return [{"servicio": "Spinning", "dia": "Lunes", "hora_inicio": "08:00", "hora_fin": "09:00"}]


class Provider:
    def __init__(self, tool="consultar_planes"):
        self.tool = tool
        self.calls = []

    def select_tool(self, message, last_topic=None):
        self.calls.append((message, last_topic))
        return (self.tool, "{}") if self.tool else None


def make_service(tool="consultar_planes"):
    catalog, provider = Catalog(), Provider(tool)
    return AgentService(catalog, provider, ConversationTopics()), catalog, provider


def test_plan_price_changes_with_catalog():
    service, catalog, _provider = make_service()
    first = service.respond("¿Cuánto cuesta el plan mensual?")
    catalog.price = 90
    second = service.respond("¿Cuánto cuesta el plan mensual?", first["id_conversacion"])
    assert "S/ 80" in first["texto"]
    assert "S/ 90" in second["texto"]
    assert catalog.calls == ["planes", "planes"]


def test_public_schedule_from_service():
    service, catalog, _provider = make_service("consultar_horarios_publicos")
    result = service.respond("¿Cuándo hay spinning?")
    assert "Spinning: Lunes 08:00–09:00" in result["texto"]
    assert catalog.calls == ["horarios"]


def test_empty_catalog_does_not_invent_a_price():
    service, catalog, _provider = make_service()
    catalog.planes_membresia = lambda: []
    result = service.respond("¿Cuánto cuesta el plan?")
    assert result["estado"] == "sin_datos"
    assert "S/" not in result["texto"]


def test_provider_failure_does_not_consult_catalog():
    service, catalog, provider = make_service()
    provider.select_tool = lambda _message, _topic: (_ for _ in ()).throw(ProviderUnavailable())
    with pytest.raises(ProviderUnavailable):
        service.respond("¿Cuánto cuesta el plan?")
    assert catalog.calls == []


@pytest.mark.parametrize("message", [
    "Mi clave es Secreta123", "Paga con 4557 1234 5678 9012", "Escríbeme a persona@example.com",
])
def test_sensitive_input_never_reaches_provider_or_catalog(message):
    service, catalog, provider = make_service()
    result = service.respond(message)
    assert result["estado"] == "bloqueado"
    assert provider.calls == []
    assert catalog.calls == []
    assert contains_sensitive(message)


def test_private_action_is_not_executed():
    service, catalog, provider = make_service()
    result = service.respond("Inscríbeme a spinning")
    assert result["estado"] == "fuera_de_alcance"
    assert not provider.calls and not catalog.calls


def test_price_question_with_word_pago_is_public():
    assert not requests_private_action("¿Cuánto pago por el plan mensual?")
    service, catalog, provider = make_service()
    assert service.respond("¿Cuánto pago por el plan mensual?")["estado"] == "respondida"
    assert catalog.calls == ["planes"] and len(provider.calls) == 1


def test_budget_reservation_is_atomic_and_has_no_user_data():
    budget = AgentBudget(per_minute=3, per_day=3)

    def try_reserve(_):
        try:
            budget.reserve()
            return True
        except RateLimitExceeded:
            return False

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(try_reserve, range(10)))
    assert sum(results) == 3
    assert budget._daily_count == 3
    assert not hasattr(budget, "visitor_ids")


def test_budget_blocks_provider_when_exhausted():
    service, catalog, provider = make_service()
    service._budget = AgentBudget(per_minute=1, per_day=1)
    service.respond("¿Cuánto cuesta el plan?")
    with pytest.raises(RateLimitExceeded):
        service.respond("¿Cuánto cuesta el plan?")
    assert len(provider.calls) == 1 and catalog.calls == ["planes"]


def test_model_cannot_choose_another_tool():
    service, catalog, _provider = make_service("activar_membresia")
    with pytest.raises(ValueError, match="no permitida"):
        service.respond("¿Cuánto cuesta el plan?")
    assert catalog.calls == []


def test_conversation_topics_are_isolated():
    service, _catalog, provider = make_service()
    first = service.respond("¿Cuánto cuesta el plan?")
    service.respond("¿Y el precio?", first["id_conversacion"])
    service.respond("¿Cuánto cuesta el plan?")
    assert provider.calls[0][1] is None
    assert provider.calls[1][1] == "consultar_planes"
    assert provider.calls[2][1] is None


def test_expired_conversation_does_not_restore_topic():
    service, _catalog, provider = make_service()
    first = service.respond("¿Cuánto cuesta el plan?")
    store = service._conversations
    with store._lock:
        store._items[first["id_conversacion"]] = ("consultar_planes", datetime.now(timezone.utc) - timedelta(seconds=1))
    second = service.respond("¿Y el precio?", first["id_conversacion"])
    assert second["id_conversacion"] != first["id_conversacion"]
    assert provider.calls[-1][1] is None


def test_missing_provider_key_does_not_call_external_service():
    with pytest.raises(ProviderUnavailable):
        GroqAgentProvider("").select_tool("planes")


def test_groq_adapter_requests_only_local_read_tools(monkeypatch):
    requests = []

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"tool_calls": [
                {"function": {"name": "consultar_planes", "arguments": "{ }"}}
            ]}}]}

    def fake_post(url, *, json, headers, timeout):
        requests.append((url, json, headers, timeout))
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)
    provider = GroqAgentProvider("synthetic-key")
    assert provider.select_tool("¿Cuánto cuesta el plan?") == (
        "consultar_planes", "{ }"
    )
    url, payload, headers, timeout = requests[0]
    assert url == GroqAgentProvider.URL
    assert timeout == 15
    assert {tool["function"]["name"] for tool in payload["tools"]} == {
        "consultar_planes", "consultar_horarios_publicos",
    }
    assert headers["Authorization"] == "Bearer synthetic-key"
    assert "synthetic-key" not in str(payload)
