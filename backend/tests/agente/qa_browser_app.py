"""Servidor aislado para recorrer UI → API → servicio con datos controlados.

Se inicia solo desde Playwright. No lee .env ni registra pagos, correo o BD.
"""

from types import SimpleNamespace

from fastapi import FastAPI

from application.services.agent_budget import AgentBudget
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
        plain = message.casefold()
        if "plan" in plain:
            return "consultar_planes", "{}"
        if "ejercicio" in plain:
            return "consultar_informacion_publica", '{"tema":"actividades"}'
        if "cupo" in plain:
            return "consultar_informacion_publica", '{"tema":"cupos"}'
        if "one piece" in plain:
            return "fuera_de_tema", "{}"
        return None


agent_routes.get_settings = lambda: SimpleNamespace(groq_api_key="local-qa")
agent_routes.GroqAgentProvider = ControlledProvider
# La cuota de producto se prueba en pytest; aquí se aíslan recorridos entre navegadores.
agent_routes._budget = AgentBudget(per_minute=1000, per_day=10000)

app = FastAPI(title="Agente QA aislado")
app.include_router(agent_routes.router, prefix="/api")
app.dependency_overrides[get_gym_service] = ControlledGym
