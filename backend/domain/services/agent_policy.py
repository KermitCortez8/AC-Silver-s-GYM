"""Reglas deterministas para la primera versión pública del agente."""

import json
import re
import unicodedata

from domain.services.public_gym_knowledge import PUBLIC_TOPICS

ALLOWED_TOOLS = frozenset({
    "consultar_planes", "consultar_horarios_publicos",
    "consultar_informacion_publica", "conversar", "fuera_de_tema",
})

_SENSITIVE = (
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b(?:contrase(?:ñ|n)a|password|clave|pin|cvv)\s*(?:es|:|=)\s*\S+", re.I),
    re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    re.compile(r"\b\d{8,9}\b"),
    re.compile(r"\b(?:dni|tel[eé]fono)\s*[:#]?\s*\d{8,9}\b", re.I),
)
_PRIVATE = re.compile(
    r"\b(?:matricul|inscr[ií]b|inscripci[oó]n|cancel|cobr|"
    r"activ(?:ar|aci[oó]n|ame|a\s+(?:mi|la|una)\s+cuenta)|"
    r"mi membres[ií]a|mis datos|"
    r"otro cliente|tercero|pedido|compr[aoe])\w*\b|"
    r"\b(?:paga|pagar|p[aá]game|realizar un pago|hacer un pago)\b", re.I,
)

SOCIAL_REPLIES = {
    "hola": "¡Hola! Soy Silver. ¿Qué tal? Puedo ayudarte con planes, clases, horarios y dudas sobre el gimnasio.",
    "bienestar": "Todo bien, gracias por preguntar. ¿Y tú? Si quieres, puedo ayudarte con planes, clases u horarios del gimnasio.",
    "seguimiento": "¡Todo bien por aquí, gracias! ¿Te ayudo con algún plan, clase u horario?",
    "identidad": "Soy Silver, el asistente de Silver Gym. Puedo orientarte sobre información pública del gimnasio. ¿Qué te gustaría saber?",
    "ayuda": "Puedo ayudarte a consultar planes, horarios de clases, tipos de entrenamiento y otras dudas públicas del gimnasio. ¿Por dónde empezamos?",
    "bien": "¡Me alegra! Si te surge alguna duda sobre el gimnasio, aquí estoy.",
    "gracias": "¡De nada! Si tienes otra pregunta sobre el gimnasio, aquí estoy.",
    "despedida": "¡Hasta luego! Que tengas un buen día.",
    "confirmacion": "¡Claro! Si tienes otra pregunta sobre el gimnasio, dime.",
}
_SOCIAL_MESSAGES = {
    "hola": "hola", "holi": "hola", "buenas": "hola", "buenos dias": "hola",
    "buenas tardes": "hola", "buenas noches": "hola", "saludos": "hola",
    "que tal": "bienestar", "que tal todo": "bienestar",
    "como estas": "bienestar", "como te va": "bienestar",
    "como va todo": "bienestar",
    "todo bien": "bienestar", "y tu": "seguimiento",
    "quien eres": "identidad", "como te llamas": "identidad",
    "que haces": "ayuda", "que puedes hacer": "ayuda",
    "en que me ayudas": "ayuda", "en que me puedes ayudar": "ayuda",
    "bien gracias": "bien", "todo bien gracias": "bien",
    "muy bien gracias": "bien", "estoy bien gracias": "bien",
    "bien y tu": "bien", "todo bien y tu": "bien",
    "gracias": "gracias", "muchas gracias": "gracias", "mil gracias": "gracias",
    "ok gracias": "gracias", "vale gracias": "gracias", "genial gracias": "gracias",
    "adios": "despedida", "chau": "despedida", "chao": "despedida",
    "hasta luego": "despedida", "nos vemos": "despedida", "bye": "despedida",
    "ok": "confirmacion", "vale": "confirmacion", "listo": "confirmacion",
}


def validate_message(message: str) -> str:
    text = message.strip()
    if not text or len(text) > 150:
        raise ValueError("Escribe una consulta de 1 a 150 caracteres.")
    return text


def contains_sensitive(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SENSITIVE)


def requests_private_action(text: str) -> bool:
    return bool(_PRIVATE.search(text))


def asks_for_account_recovery(text: str) -> bool:
    """Distingue ayuda para volver a entrar de una petición de ejecutar el cambio."""
    return bool(
        re.search(r"\b(?:recuper\w*|restablec\w*|olvid\w*|perd\w*)\b", text, re.I)
        and re.search(
            r"\b(?:cuenta|acceso|contrase(?:ñ|n)a|clave|password|login|sesi[oó]n)\b",
            text, re.I,
        )
    )


def social_reply(text: str) -> str | None:
    """Responde cortesías breves sin enviar contenido al proveedor externo."""
    plain = "".join(
        char for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )
    normalized = " ".join(re.sub(r"[^a-z\s]", " ", plain).split())
    normalized = re.sub(r"^(?:silver|chat) | (?:silver|chat)$", "", normalized)
    category = _SOCIAL_MESSAGES.get(normalized)
    greeting = r"(?:hola|holi|buenas|buenos dias|buenas tardes|buenas noches)"
    if category is None and re.fullmatch(
        rf"(?:{greeting}(?: silver| chat)? )?"
        r"(?:como estas|que tal(?: todo)?|como te va|como va todo|todo bien)"
        r"(?: tu| silver| chat)?",
        normalized,
    ):
        category = "bienestar"
    if category is None and re.fullmatch(rf"{greeting}(?: silver| chat)?", normalized):
        category = "hola"
    if category is None and re.fullmatch(
        r"(?:muchas|mil)? ?gracias por (?:la|el|tu) "
        r"(?:informacion|info|ayuda|respuesta|dato|datos)", normalized,
    ):
        category = "gracias"
    if category is None and re.fullmatch(r"(?:muchas|mil)? ?gracias(?: silver| chat)?", normalized):
        category = "gracias"
    return SOCIAL_REPLIES.get(category)


def asks_for_public_schedules(text: str) -> bool:
    """Reconoce preguntas explícitas por horarios de entrenamiento del gimnasio."""
    return bool(
        re.search(r"\bhorarios?\b", text, re.I)
        and re.search(
            r"\b(?:ejercici\w*|clases?|actividades?|entren\w*|gimnas\w*|gym|"
            r"fitness|muscul\w*|cardio|baile|spinning|yoga)\b",
            text, re.I,
        )
    )


def validate_tool(name: str, arguments: str) -> tuple[str, str | None]:
    try:
        parsed = json.loads(arguments or "{}")
    except (TypeError, ValueError) as error:
        raise ValueError("El agente solicitó una acción no permitida.") from error
    if name not in ALLOWED_TOOLS or not isinstance(parsed, dict):
        raise ValueError("El agente solicitó una acción no permitida.")
    if name == "consultar_informacion_publica":
        topic = parsed.get("tema")
        if (set(parsed) != {"tema"} or not isinstance(topic, str)
                or topic not in PUBLIC_TOPICS):
            raise ValueError("El agente solicitó una acción no permitida.")
        return name, topic
    if name == "conversar":
        category = parsed.get("intencion")
        if (set(parsed) != {"intencion"} or not isinstance(category, str)
                or category not in SOCIAL_REPLIES):
            raise ValueError("El agente solicitó una acción no permitida.")
        return name, category
    if parsed:
        raise ValueError("El agente solicitó una acción no permitida.")
    return name, None
