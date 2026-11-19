"""Ruta HTTP aislada, con catálogo y proveedor falsos."""

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from infrastructure.services.groq_agent_provider import GroqAgentProvider
from presentation.dependencies import get_agent_provider, get_gym_service
from presentation.routes import agent_routes
from application.services.agent_budget import AgentBudget
from app.agent_readonly_app import app as readonly_app


def test_local_demo_exposes_only_public_catalog_reads_and_agent():
    with TestClient(readonly_app) as client:
        paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {
        "/api/agente/mensajes", "/api/gym/horarios-publicos",
        "/api/planes-membresia", "/api/promociones/vigentes-publico",
    }
    assert all(set(operations) == ({"post"} if path.endswith("/mensajes") else {"get"})
               for path, operations in paths.items())


class FakeGym:
    def planes_membresia(self):
        return [{"nombre_plan": "Mensual", "precio": 80, "duracion": "30 días"}]

    def horarios_servicio(self, *, solo_activos):
        assert solo_activos
        return [{
            "servicio": "Fitness", "dia": "Lunes",
            "hora_inicio": "08:00", "hora_fin": "09:00",
        }]


class FakeProvider:
    def __init__(self, _key):
        pass

    def select_tool(self, _message, _last_topic=None):
        return "consultar_planes", "{}"


def test_public_endpoint_uses_business_catalog_without_external_calls():
    app = FastAPI()
    app.include_router(agent_routes.router, prefix="/api")
    app.dependency_overrides[get_gym_service] = FakeGym
    app.dependency_overrides[get_agent_provider] = lambda: FakeProvider("test")
    with TestClient(app) as client:
        result = client.post("/api/agente/mensajes", json={"mensaje": "¿Cuánto cuesta el plan mensual?"})
        boundary = client.post("/api/agente/mensajes", json={"mensaje": "x" * 500})
        invalid = client.post("/api/agente/mensajes", json={"mensaje": "x" * 501})
    assert result.status_code == 200
    assert "S/ 80" in result.json()["texto"]
    assert boundary.status_code == 200
    assert invalid.status_code == 422


@pytest.mark.parametrize("mensaje", [
    "Quiero saber horarios",
    "¿Cuáles son los horarios?",
    "¿Qué horarios tienen?",
    "Horarios, por favor.",
])
def test_public_schedule_requests_work_without_provider_key(mensaje):
    app = FastAPI()
    app.include_router(agent_routes.router, prefix="/api")
    app.dependency_overrides[get_gym_service] = FakeGym
    app.dependency_overrides[get_agent_provider] = lambda: GroqAgentProvider("")

    with TestClient(app) as client:
        result = client.post("/api/agente/mensajes", json={"mensaje": mensaje})

    assert result.status_code == 200
    assert result.json()["estado"] == "respondida"
    assert "Fitness:\n• Lunes 08:00–09:00" in result.json()["texto"]


@pytest.mark.parametrize("provider_times_out", [False, True], ids=["groq", "catalogo-de-respaldo"])
def test_public_schedule_prefers_configured_provider_and_recovers_from_timeout(monkeypatch, provider_times_out):
    monkeypatch.setattr(agent_routes, "_budget", AgentBudget())
    calls = []

    def select_with_key(url, *, headers, json, timeout):
        assert url == GroqAgentProvider.URL
        assert headers["Authorization"] == "Bearer clave-sintetica"
        calls.append(json["messages"][-1]["content"])
        assert timeout == 15
        if provider_times_out:
            raise httpx.ReadTimeout("Tiempo de espera agotado")
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"tool_calls": [
                {"function": {"name": "consultar_horarios_publicos", "arguments": "{}"}},
            ]}}]},
        )

    monkeypatch.setattr("httpx.post", select_with_key)
    app = FastAPI()
    app.include_router(agent_routes.router, prefix="/api")
    app.dependency_overrides[get_gym_service] = FakeGym
    app.dependency_overrides[get_agent_provider] = lambda: GroqAgentProvider("clave-sintetica")

    with TestClient(app) as client:
        result = client.post("/api/agente/mensajes", json={"mensaje": "Quiero saber horarios"})

    assert len(calls) == 1 and "Quiero saber horarios" in calls[0]
    assert result.status_code == 200
    assert "Fitness:\n• Lunes 08:00–09:00" in result.json()["texto"]


def test_public_endpoint_returns_429_when_budget_is_exhausted(monkeypatch):
    monkeypatch.setattr(agent_routes, "_budget", AgentBudget(per_minute=1, per_day=1))
    app = FastAPI()
    app.include_router(agent_routes.router, prefix="/api")
    app.dependency_overrides[get_gym_service] = FakeGym
    app.dependency_overrides[get_agent_provider] = lambda: FakeProvider("test")
    with TestClient(app) as client:
        first = client.post("/api/agente/mensajes", json={"mensaje": "¿Cuánto cuesta el plan?"})
        second = client.post("/api/agente/mensajes", json={"mensaje": "Quisiera saber algo"})
    assert first.status_code == 200
    assert second.status_code == 429
