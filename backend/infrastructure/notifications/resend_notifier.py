# Módulo: infrastructure.notifications.resend_notifier
# HU-CB15: Notificación por correo vía Resend ante umbrales del 80% y 100% ([?-P2 DECIDIDO]).
from __future__ import annotations

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


def enviar_alerta_presupuesto_resend(
    tipo_alerta: str,
    tokens_consumidos: int,
    presupuesto_total: int,
    to_email: str,
    from_email: str,
    api_key: str,
) -> bool:
    """
    Envía notificación de alerta por correo vía Resend.
    Garantía de resiliencia: Si Resend falla, el chat NO se interrumpe y retorna False.
    """
    if not api_key:
        logger.warning("RESEND_API_KEY no configurada. Alerta de presupuesto omitida.")
        return False

    porcentaje = int((tokens_consumidos / max(1, presupuesto_total)) * 100)
    asunto = f"⚠️ [Chatbot] Alerta de Consumo: {porcentaje}% del Presupuesto Diario ({tipo_alerta})"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #D83A00; margin-top: 0;">Silver Gym Surco — Alerta de Presupuesto</h2>
        <p>Se ha detectado que el consumo diario de tokens del Chatbot alcanzó el <strong>{porcentaje}%</strong> del presupuesto interno.</p>
        <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #D83A00; margin: 15px 0;">
            <p style="margin: 0;"><strong>Tipo de Alerta:</strong> {tipo_alerta}</p>
            <p style="margin: 5px 0 0 0;"><strong>Tokens Consumidos:</strong> {tokens_consumidos:,} / {presupuesto_total:,}</p>
        </div>
        <p style="color: #666; font-size: 13px;">Nota: Al llegar al 100%, el Chatbot conmuta automáticamente a modo básico para proteger los límites de la capa gratuita de Groq.</p>
    </div>
    """

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": asunto,
        "html": html_content,
        "text": f"Alerta Chatbot Silver Gym: {porcentaje}% alcanzado ({tokens_consumidos}/{presupuesto_total} tokens).",
    }

    req = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SilverGym-Chatbot-Alerts/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status in (200, 201)
    except (HTTPError, URLError, TimeoutError, Exception) as err:
        logger.error("Error al enviar alerta por correo vía Resend: %s", str(err))
        return False
