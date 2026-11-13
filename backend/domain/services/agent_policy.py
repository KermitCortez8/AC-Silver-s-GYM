"""Reglas deterministas para la primera versión pública del agente."""

import json
import re

from domain.services.public_gym_knowledge import PUBLIC_TOPICS

ALLOWED_TOOLS = frozenset({
    "consultar_planes", "consultar_horarios_publicos",
    "consultar_informacion_publica",
})

_SENSITIVE = (
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b(?:contrase(?:ñ|n)a|password|clave|pin|cvv)\b", re.I),
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


def validate_message(message: str) -> str:
    text = message.strip()
    if not text or len(text) > 150:
        raise ValueError("Escribe una consulta de 1 a 150 caracteres.")
    return text


def contains_sensitive(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SENSITIVE)


def requests_private_action(text: str) -> bool:
    return bool(_PRIVATE.search(text))


def asks_for_public_schedules(text: str) -> bool:
    """Reconoce preguntas explícitas por horarios de entrenamiento del gimnasio."""
    return bool(
        re.search(r"\bhorarios?\b", text, re.I)
        and re.search(
            r"\b(?:ejercici\w*|clases?|entren\w*|gimnas\w*|gym|"
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
    if parsed:
        raise ValueError("El agente solicitó una acción no permitida.")
    return name, None
