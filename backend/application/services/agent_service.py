"""Orquesta herramientas públicas sin permitir acciones del modelo en el negocio."""

from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4

from domain.services.agent_policy import (
    contains_sensitive, requests_private_action, validate_message, validate_tool,
)


class ConversationTopics:
    """Solo retiene el tema público reciente; no conserva mensajes personales."""

    def __init__(self):
        self._items = {}
        self._lock = Lock()

    def get(self, identifier: str | None) -> tuple[str, str | None]:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._items = {key: value for key, value in self._items.items() if value[1] > now}
            if identifier in self._items:
                return identifier, self._items[identifier][0]
            return str(uuid4()), None

    def put(self, identifier: str, topic: str) -> None:
        with self._lock:
            self._items[identifier] = (topic, datetime.now(timezone.utc) + timedelta(minutes=30))


class AgentService:
    def __init__(self, gym, provider, conversations: ConversationTopics, budget=None):
        self._gym = gym
        self._provider = provider
        self._conversations = conversations
        self._budget = budget

    def respond(self, message: str, conversation_id: str | None = None) -> dict:
        text = validate_message(message)
        identifier, last_topic = self._conversations.get(conversation_id)
        base = {"id_conversacion": identifier, "enlaces": []}
        if contains_sensitive(text):
            return {**base, "estado": "bloqueado", "texto": "Por tu seguridad, no compartas datos personales, claves ni datos de pago por el chat."}
        if requests_private_action(text):
            return {**base, "estado": "fuera_de_alcance", "texto": "Esa gestión requiere usar los formularios y controles de la plataforma.",
                    "enlaces": [{"texto": "Ir al acceso", "ruta": "/login"}]}
        if self._budget:
            self._budget.reserve()
        selection = self._provider.select_tool(text, last_topic)
        if not selection:
            return {**base, "estado": "fuera_de_alcance", "texto": "Puedo ayudarte con planes de membresía y horarios de clases."}
        tool = validate_tool(*selection)
        if tool == "consultar_planes":
            plans = self._gym.planes_membresia()
            lines = []
            for plan in plans[:10]:
                name = str(plan.get("nombre_plan") or plan.get("nombre") or "").strip()
                price = plan.get("precio")
                duration = str(plan.get("duracion") or "").strip()
                if name and price is not None:
                    lines.append(f"{name}: S/ {price}" + (f" · {duration}" if duration else ""))
            reply = "Planes disponibles: " + "; ".join(lines) if lines else "No puedo confirmar los planes en este momento."
            route, label = "/registro", "Ver registro"
        else:
            schedules = self._gym.horarios_servicio(solo_activos=True)
            lines = []
            for row in schedules[:10]:
                service = str(row.get("servicio") or "").strip()
                day = str(row.get("dia") or "").strip()
                start = str(row.get("hora_inicio") or "").strip()
                end = str(row.get("hora_fin") or "").strip()
                if service and day and start and end:
                    lines.append(f"{service}: {day} {start}–{end}")
            reply = "Clases publicadas: " + "; ".join(lines) if lines else "No puedo confirmar los horarios en este momento."
            route, label = "/", "Ver inicio"
        self._conversations.put(identifier, tool)
        return {**base, "estado": "respondida" if lines else "sin_datos", "texto": reply,
                "enlaces": [{"texto": label, "ruta": route}]}
