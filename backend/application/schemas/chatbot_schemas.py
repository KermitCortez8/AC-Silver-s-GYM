# Módulo: application.schemas.chatbot_schemas
# DTOs y modelos de datos del contrato de API del Chatbot.
# Fuente: contracts/control.md y spec.md.
from __future__ import annotations

from typing import Any, Literal, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


ChatState = Literal["ok", "rate_limited", "slow", "basic_mode", "session_expired", "forbidden"]
BlockKind = Literal["rate_limit", "basic_mode", "session_expired"]


class QuickReply(BaseModel):
    label: str
    action: str


class ScheduleItem(BaseModel):
    id: int
    service: str
    day: str
    start: str
    end: str
    slots_left: int


class ProductBasicItem(BaseModel):
    id: Union[int, str]
    name: str
    category: str
    image_url: Optional[str] = None
    available: bool = True


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ScheduleListBlock(BaseModel):
    type: Literal["schedule_list"] = "schedule_list"
    items: list[ScheduleItem] = Field(default_factory=list)


class ProductBasicListBlock(BaseModel):
    type: Literal["product_basic_list"] = "product_basic_list"
    items: list[ProductBasicItem] = Field(default_factory=list)


class ContactBlock(BaseModel):
    type: Literal["contact"] = "contact"
    phone: str = "+51 912 794 583"
    whatsapp_url: str = "https://wa.me/51912794583"
    attention_hours: str = "Lun a Sáb 8:00 am - 8:00 pm"


class NoticeBlock(BaseModel):
    type: Literal["notice"] = "notice"
    kind: BlockKind
    text: str
    retry_in_seconds: Optional[int] = None


Block = Union[TextBlock, ScheduleListBlock, ProductBasicListBlock, ContactBlock, NoticeBlock, dict[str, Any]]


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    action: Optional[str] = None
    confirmed: bool = False

    @field_validator("message")
    @classmethod
    def validate_message_length(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("El mensaje no puede estar vacío.")
        if len(v) > 500:
            raise ValueError("El mensaje supera el límite máximo permitido de 500 caracteres.")
        return v


class ChatResponse(BaseModel):
    conversation_id: str
    state: ChatState = "ok"
    blocks: list[Any] = Field(default_factory=list)
    quick_replies: list[QuickReply] = Field(default_factory=list)
    retry_after_seconds: Optional[int] = None
