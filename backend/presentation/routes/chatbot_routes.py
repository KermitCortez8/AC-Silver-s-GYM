# Módulo: presentation.routes.chatbot_routes
# Endpoint HTTP POST /api/chatbot/message y router del Chatbot.
# Fuente: contracts/control.md y spec.md.
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse

from application.schemas.chatbot_schemas import ChatRequest, ChatResponse
from application.services.chatbot_orchestrator import ChatbotOrchestrator
from domain.services.chatbot_budget import ChatbotBudgetController
from domain.services.chatbot_expiration import ChatbotExpirationController
from domain.services.chatbot_rate_limiter import ChatbotRateLimiter
from infrastructure.chatbot_config import get_chatbot_settings
from infrastructure.notifications.resend_notifier import enviar_alerta_presupuesto_resend
from infrastructure.repositories.chatbot_repository import MemoryChatbotRepository
from infrastructure.services.groq_service import GroqService

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

# Instancia singleton compartida en memoria para el módulo chatbot
_settings = get_chatbot_settings()
_repo = MemoryChatbotRepository()


def _resend_adapter(tipo: str, tokens: int, total: int) -> bool:
    return enviar_alerta_presupuesto_resend(
        tipo_alerta=tipo,
        tokens_consumidos=tokens,
        presupuesto_total=total,
        to_email=_settings.alert_email_to,
        from_email=_settings.alert_email_from,
        api_key=_settings.resend_api_key,
    )


_budget_controller = ChatbotBudgetController(
    repository=_repo,
    presupuesto_tpd=_settings.presupuesto_tpd,
    tope_cliente=_settings.tope_tokens_cliente,
    tope_visitante=_settings.tope_tokens_visitante,
    email_sender=_resend_adapter,
)

_rate_limiter = ChatbotRateLimiter(
    repository=_repo,
    limite_cliente_min=_settings.rate_limit_cliente_min,
    limite_cliente_dia=_settings.rate_limit_cliente_dia,
    limite_visitante_min=_settings.rate_limit_visitante_min,
    limite_visitante_dia=_settings.rate_limit_visitante_dia,
)

_expiration_controller = ChatbotExpirationController(
    repository=_repo,
    inactividad_min=_settings.inactividad_min,
    expiracion_pendiente_min=_settings.expiracion_pendiente_min,
    groq_timeout_seconds=_settings.groq_timeout_seconds,
    groq_max_retries=_settings.groq_max_retries,
)

_groq_service = GroqService(
    api_key=_settings.groq_api_key,
    model=_settings.llm_model,
    timeout_seconds=_settings.groq_timeout_seconds,
)


def _llm_caller(msg: str, hist: list) -> tuple[str, int]:
    return _groq_service.generar_respuesta(msg, hist)


_orchestrator = ChatbotOrchestrator(
    settings=_settings,
    repository=_repo,
    budget_controller=_budget_controller,
    rate_limiter=_rate_limiter,
    expiration_controller=_expiration_controller,
    llm_caller=_llm_caller if _settings.has_groq_credentials else None,
)


def get_chatbot_orchestrator() -> ChatbotOrchestrator:
    return _orchestrator


@router.post("/message", response_model=ChatResponse)
async def send_chatbot_message(
    chat_request: ChatRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
) -> JSONResponse:
    """
    Endpoint principal del Chatbot para visitantes y clientes autenticados.
    Aplica el pipeline de 9 etapas de control de seguridad, privacidad y límites.
    """
    # Extracción de IP de proxy de confianza o cliente directo
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"

    response = _orchestrator.procesar_mensaje(
        request=chat_request,
        authorization_header=authorization,
        ip_real=client_ip,
    )

    # Status code mapping
    status_code = status.HTTP_200_OK
    if response.state == "rate_limited":
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif response.state == "forbidden":
        status_code = status.HTTP_403_FORBIDDEN

    headers = {}
    if response.retry_after_seconds:
        headers["Retry-After"] = str(response.retry_after_seconds)

    return JSONResponse(
        content=response.model_dump(),
        status_code=status_code,
        headers=headers,
    )
