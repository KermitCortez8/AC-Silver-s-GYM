"""Ruta HTTP aislada, con catálogo y proveedor falsos."""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from presentation.dependencies import get_gym_service
from presentation.routes import agent_routes
from application.services.agent_budget import AgentBudget


class FakeGym:
    def planes_membresia(self):
        return [{"nombre_plan": "Mensual", "precio": 80, "duracion": "30 días"}]


class FakeProvider:
    def __init__(self, _key):
        pass

    def select_tool(self, _message, _last_topic=None):
        return "consultar_planes", "{}"


def test_public_endpoint_uses_business_catalog_without_external_calls(monkeypatch):
    monkeypatch.setattr(agent_routes, "get_settings", lambda: SimpleNamespace(groq_api_key="test"))
    monkeypatch.setattr(agent_routes, "GroqAgentProvider", FakeProvider)
    app = FastAPI()
    app.include_router(agent_routes.router, prefix="/api")
    app.dependency_overrides[get_gym_service] = FakeGym
    with TestClient(app) as client:
        result = client.post("/api/agente/mensajes", json={"mensaje": "¿Cuánto cuesta el plan mensual?"})
        invalid = client.post("/api/agente/mensajes", json={"mensaje": "x" * 151})
    assert result.status_code == 200
    assert "S/ 80" in result.json()["texto"]
    assert invalid.status_code == 422


def test_public_endpoint_returns_429_when_budget_is_exhausted(monkeypatch):
    monkeypatch.setattr(agent_routes, "get_settings", lambda: SimpleNamespace(groq_api_key="test"))
    monkeypatch.setattr(agent_routes, "GroqAgentProvider", FakeProvider)
    monkeypatch.setattr(agent_routes, "_budget", AgentBudget(per_minute=1, per_day=1))
    app = FastAPI()
    app.include_router(agent_routes.router, prefix="/api")
    app.dependency_overrides[get_gym_service] = FakeGym
    with TestClient(app) as client:
        first = client.post("/api/agente/mensajes", json={"mensaje": "¿Cuánto cuesta el plan?"})
        second = client.post("/api/agente/mensajes", json={"mensaje": "¿Cuánto cuesta el plan?"})
    assert first.status_code == 200
    assert second.status_code == 429
