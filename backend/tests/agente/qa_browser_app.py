"""Servidor aislado para recorrer UI → API → servicio con datos controlados.

Se inicia solo desde Playwright. No lee .env ni registra pagos, correo o BD.
"""

from types import SimpleNamespace

from fastapi import FastAPI

from presentation.dependencies import get_gym_service
from presentation.routes import agent_routes


class ControlledGym:
    def planes_membresia(self):
        return [{"nombre_plan": "Plan QA", "precio": 91, "duracion": "31 días"}]

    def horarios_servicio(self, solo_activos=False):
        assert solo_activos is True
        return [{"servicio": "Baile", "dia": "Lunes", "hora_inicio": "07:00", "hora_fin": "08:00"}]


class ControlledProvider:
    def __init__(self, _key):
        pass

    def select_tool(self, message, _last_topic=None):
        if "plan" in message.casefold():
            return "consultar_planes", "{}"
        return None


agent_routes.get_settings = lambda: SimpleNamespace(groq_api_key="local-qa")
agent_routes.GroqAgentProvider = ControlledProvider

app = FastAPI(title="Agente QA aislado")
app.include_router(agent_routes.router, prefix="/api")
app.dependency_overrides[get_gym_service] = ControlledGym
