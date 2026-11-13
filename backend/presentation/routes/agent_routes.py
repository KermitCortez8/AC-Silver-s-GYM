"""Consulta pública y de solo lectura del agente del gimnasio."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from application.services.agent_budget import AgentBudget, RateLimitExceeded
from application.services.agent_service import AgentService, ConversationTopics
from application.services.gym_service import GymService
from infrastructure.config import get_settings
from infrastructure.services.groq_agent_provider import GroqAgentProvider, ProviderUnavailable
from presentation.dependencies import get_gym_service


router = APIRouter(prefix="/agente", tags=["agente"])
_conversations = ConversationTopics()
_budget = AgentBudget()


class AgentRequest(BaseModel):
    mensaje: str = Field(min_length=1, max_length=150)
    id_conversacion: str | None = Field(default=None, max_length=64)


@router.post("/mensajes")
def message(payload: AgentRequest, gym: GymService = Depends(get_gym_service)):
    service = AgentService(gym, GroqAgentProvider(get_settings().groq_api_key), _conversations, _budget)
    try:
        return service.respond(payload.mensaje, payload.id_conversacion)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RateLimitExceeded as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except ProviderUnavailable as error:
        raise HTTPException(status_code=503, detail="El asistente no está disponible. Consulta los planes y horarios en la página.") from error
    except (OSError, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="No se pudo consultar el catálogo. Inténtalo de nuevo más tarde.") from error
