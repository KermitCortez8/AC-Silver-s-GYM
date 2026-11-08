# Módulo: infrastructure.chatbot_config
# Parámetros operativos y variables de entorno del Chatbot (RNF-CB07).
from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from pydantic import BaseModel, Field


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value:
            os.environ.setdefault(key, value)


class ChatbotSettings(BaseModel):
    # Claves de proveedores (nunca versionadas)
    groq_api_key: str = Field(default="", repr=False, exclude=True)
    resend_api_key: str = Field(default="", repr=False, exclude=True)

    # Correo de alertas de presupuesto (Resend)
    alert_email_to: str = "admin@silvergym.pe"
    alert_email_from: str = "notificaciones@silvergym.pe"

    # Seguridad de IP (HMAC-SHA256, Ley 29733)
    ip_hmac_secret: str = Field(default="chatbot_super_secret_hmac_key_2026", repr=False, exclude=True)

    # Límites de longitud y frecuencia de mensajes (HU-CB14, RN-10)
    max_mensaje_chars: int = 500
    rate_limit_cliente_min: int = 10
    rate_limit_cliente_dia: int = 100
    rate_limit_visitante_min: int = 5
    rate_limit_visitante_dia: int = 20

    # Presupuesto de tokens LLM (HU-CB15, RN-11)
    presupuesto_tpd: int = 180000
    tope_tokens_cliente: int = 8000
    tope_tokens_visitante: int = 3000

    # Tiempos de espera y expiración (HU-CB16, RNF-CB07)
    groq_timeout_seconds: float = 15.0
    groq_max_retries: int = 1
    inactividad_min: int = 30
    expiracion_pendiente_min: int = 5

    # Reglas de negocio operativas (RN-09, HU-CB05, HU-CB10)
    plazo_cancelacion_horas: int = 2
    aviso_membresia_dias: int = 7
    contact_whatsapp: str = "+51 912 794 583"
    llm_model: str = "openai/gpt-oss-120b"

    @property
    def has_groq_credentials(self) -> bool:
        return bool(self.groq_api_key.strip())

    @property
    def has_resend_credentials(self) -> bool:
        return bool(self.resend_api_key.strip())


@lru_cache
def get_chatbot_settings() -> ChatbotSettings:
    backend_dir = Path(__file__).resolve().parents[1]
    _load_env_file(backend_dir / ".env")
    _load_env_file(backend_dir.parent / ".env")

    return ChatbotSettings(
        groq_api_key=(os.getenv("GROQ_API_KEY") or "").strip(),
        resend_api_key=(os.getenv("RESEND_API_KEY") or "").strip(),
        alert_email_to=(os.getenv("CHATBOT_ALERT_EMAIL_TO") or "admin@silvergym.pe").strip(),
        alert_email_from=(os.getenv("CHATBOT_ALERT_EMAIL_FROM") or "notificaciones@silvergym.pe").strip(),
        ip_hmac_secret=(os.getenv("CHATBOT_IP_HMAC_SECRET") or "chatbot_super_secret_hmac_key_2026").strip(),
        max_mensaje_chars=int(os.getenv("CHATBOT_MAX_MENSAJE_CHARS") or "500"),
        rate_limit_cliente_min=int(os.getenv("CHATBOT_RATE_LIMIT_CLIENTE_MIN") or "10"),
        rate_limit_cliente_dia=int(os.getenv("CHATBOT_RATE_LIMIT_CLIENTE_DIA") or "100"),
        rate_limit_visitante_min=int(os.getenv("CHATBOT_RATE_LIMIT_VISITANTE_MIN") or "5"),
        rate_limit_visitante_dia=int(os.getenv("CHATBOT_RATE_LIMIT_VISITANTE_DIA") or "20"),
        presupuesto_tpd=int(os.getenv("CHATBOT_PRESUPUESTO_TPD") or "180000"),
        tope_tokens_cliente=int(os.getenv("CHATBOT_TOPE_TOKENS_CLIENTE") or "8000"),
        tope_tokens_visitante=int(os.getenv("CHATBOT_TOPE_TOKENS_VISITANTE") or "3000"),
        groq_timeout_seconds=float(os.getenv("CHATBOT_GROQ_TIMEOUT_SECONDS") or "15.0"),
        groq_max_retries=int(os.getenv("CHATBOT_GROQ_MAX_RETRIES") or "1"),
        inactividad_min=int(os.getenv("CHATBOT_INACTIVIDAD_MIN") or "30"),
        expiracion_pendiente_min=int(os.getenv("CHATBOT_EXPIRACION_PENDIENTE_MIN") or "5"),
        plazo_cancelacion_horas=int(os.getenv("CHATBOT_PLAZO_CANCELACION_HORAS") or "2"),
        aviso_membresia_dias=int(os.getenv("CHATBOT_AVISO_MEMBRESIA_DIAS") or "7"),
        contact_whatsapp=(os.getenv("CHATBOT_CONTACT_WHATSAPP") or "+51 912 794 583").strip(),
        llm_model=(os.getenv("CHATBOT_LLM_MODEL") or "openai/gpt-oss-120b").strip(),
    )
