"""Orquesta herramientas públicas sin permitir acciones del modelo en el negocio."""

from datetime import datetime, timedelta, timezone
import re
from threading import Lock
import unicodedata
from uuid import uuid4

from domain.services.agent_policy import (
    asks_for_public_schedules, contains_sensitive, requests_private_action,
    validate_message, validate_tool,
)
from domain.services.public_gym_knowledge import PUBLIC_TOPICS


def _plain(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", value.casefold())
        if unicodedata.category(char) != "Mn"
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
        if asks_for_public_schedules(text) or (
            last_topic == "consultar_informacion_publica:actividades"
            and re.search(r"\bhorarios?\b", text, re.I)
        ):
            selection = ("consultar_horarios_publicos", "{}")
        else:
            if self._budget:
                self._budget.reserve()
            selection = self._provider.select_tool(text, last_topic)
        if not selection:
            return {**base, "estado": "fuera_de_alcance", "texto": "Puedo orientarte sobre los servicios y la información pública del gimnasio. No tengo datos confirmados para esa pregunta."}
        tool, topic = validate_tool(*selection)
        if tool == "consultar_planes":
            plans = self._gym.planes_membresia()
            lines = []
            for plan in plans:
                name = str(plan.get("nombre_plan") or plan.get("nombre") or "").strip()
                price = plan.get("precio")
                duration = str(plan.get("duracion") or "").strip()
                if name and price is not None:
                    lines.append(f"{name}: S/ {price}" + (f" · {duration}" if duration else ""))
            reply = (
                "Planes disponibles:\n" + "\n".join(f"• {line}" for line in lines)
                if lines else "No puedo confirmar los planes en este momento."
            )
            route, label = "/registro", "Ver registro"
        elif tool == "consultar_horarios_publicos":
            schedules = self._gym.horarios_servicio(solo_activos=True)
            groups = {}
            for row in schedules:
                service = str(row.get("servicio") or "").strip()
                day = str(row.get("dia") or "").strip()
                start = str(row.get("hora_inicio") or "").strip()
                end = str(row.get("hora_fin") or "").strip()
                if service and day and start and end:
                    groups.setdefault(service.casefold(), []).append((day, start, end))
            day_order = {
                "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2,
                "jueves": 3, "viernes": 4, "sabado": 5, "sábado": 5,
                "domingo": 6,
            }
            labels = {
                "fitness": "Fitness", "musculacion": "Musculación",
                "musculación": "Musculación", "cardio": "Cardio",
                "baile": "Baile",
            }
            days = {"miercoles": "Miércoles", "sabado": "Sábado"}
            question = _plain(text)
            requested = [
                service for service in (*groups, "spinning", "yoga")
                if re.search(rf"\b{re.escape(_plain(service))}\b", question)
            ]
            if requested:
                groups = {service: groups[service] for service in requested if service in groups}
            lines = []
            for service in sorted(groups):
                lines.append(f"{labels.get(service, service.title())}:")
                slots = sorted(
                    groups[service],
                    key=lambda slot: (day_order.get(slot[0].casefold(), 7), slot[1]),
                )
                for day, start, end in slots:
                    lines.append(f"• {days.get(day.casefold(), day.title())} {start}–{end}")
            reply = (
                "Horarios publicados por actividad:\n" + "\n".join(lines)
                if lines else (
                    "No encontré horarios públicos activos para esa actividad."
                    if requested else "No puedo confirmar los horarios en este momento."
                )
            )
            route, label = "/", "Ver inicio"
        else:
            fact = PUBLIC_TOPICS[topic]
            reply = fact["texto"]
            label, route = fact["enlace"]
            lines = [reply]
        self._conversations.put(identifier, f"{tool}:{topic}" if topic else tool)
        return {**base, "estado": "respondida" if lines else "sin_datos", "texto": reply,
                "enlaces": [{"texto": label, "ruta": route}]}
