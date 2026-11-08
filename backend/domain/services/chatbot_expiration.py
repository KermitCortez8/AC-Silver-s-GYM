# Módulo: domain.services.chatbot_expiration
# HU-CB16: Tiempos de espera y expiración.
# Reglas asociadas: EX-02 (Timeout 15 s + 1 reintento), EX-14 (Inactividad 30 min), EX-15 (Pendientes 5 min sin reserva previa).
from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any, Callable, Optional
from pydantic import BaseModel

from infrastructure.repositories.chatbot_repository import MemoryChatbotRepository


class ResultadoExpiracion(BaseModel):
    valida: bool
    expirada: bool
    motivo: Optional[str] = None


class ChatbotExpirationController:
    def __init__(
        self,
        repository: MemoryChatbotRepository,
        inactividad_min: int = 30,
        expiracion_pendiente_min: int = 5,
        groq_timeout_seconds: float = 15.0,
        groq_max_retries: int = 1,
    ) -> None:
        self.repo = repository
        self.inactividad_segundos = inactividad_min * 60
        self.expiracion_pendiente_segundos = expiracion_pendiente_min * 60
        self.groq_timeout_seconds = groq_timeout_seconds
        self.groq_max_retries = groq_max_retries

    def verificar_inactividad(
        self,
        conversacion_id: str,
        ahora: Optional[datetime] = None,
    ) -> ResultadoExpiracion:
        """
        Verifica si la conversación ha estado inactiva por más de 30 minutos (EX-14).
        Si expiró, marca como 'expirada_inactividad'.
        """
        conv = self.repo.get_conversation(conversacion_id)
        if not conv:
            return ResultadoExpiracion(valida=False, expirada=True, motivo="conversacion_no_existe")

        if conv.get("estado") in ("cerrada", "expirada_inactividad"):
            return ResultadoExpiracion(valida=False, expirada=True, motivo=f"conversacion_{conv['estado']}")

        ultimo_mensaje = conv.get("ultimo_mensaje_en")
        if not ultimo_mensaje:
            return ResultadoExpiracion(valida=True, expirada=False)

        now = ahora or datetime.now(timezone.utc)
        diferencia = (now - ultimo_mensaje).total_seconds()

        if diferencia > self.inactividad_segundos:
            self.repo.close_conversation(conversacion_id, estado="expirada_inactividad")
            return ResultadoExpiracion(
                valida=False,
                expirada=True,
                motivo="expirada_inactividad_30min",
            )

        return ResultadoExpiracion(valida=True, expirada=False)

    def verificar_accion_pendiente(
        self,
        conversacion_id: str,
        ahora: Optional[datetime] = None,
    ) -> ResultadoExpiracion:
        """
        Verifica si una acción pendiente de confirmación sigue vigente (< 5 min) (EX-15).
        Si pasaron más de 5 min, la acción expira y se anula (sin reserva previa).
        """
        conv = self.repo.get_conversation(conversacion_id)
        if not conv or not conv.get("accion_pendiente"):
            return ResultadoExpiracion(valida=False, expirada=False, motivo="sin_accion_pendiente")

        desde = conv.get("accion_pendiente_desde")
        if not desde:
            return ResultadoExpiracion(valida=True, expirada=False)

        now = ahora or datetime.now(timezone.utc)
        diferencia = (now - desde).total_seconds()

        if diferencia > self.expiracion_pendiente_segundos:
            self.repo.clear_pending_action(conversacion_id)
            return ResultadoExpiracion(
                valida=False,
                expirada=True,
                motivo="accion_pendiente_expirada_5min",
            )

        return ResultadoExpiracion(valida=True, expirada=False)

    def ejecutar_llamada_llm_con_reintento(
        self,
        llm_caller: Callable[[], Any],
    ) -> tuple[Optional[Any], bool]:
        """
        Ejecuta la llamada al LLM con timeout y 1 reintento interno backend (RNF-CB01, EX-02).
        Retorna (respuesta, exito).
        """
        intentos = 0
        max_intentos = 1 + self.groq_max_retries

        while intentos < max_intentos:
            intentos += 1
            try:
                # El llamador real implementa timeout=self.groq_timeout_seconds
                resultado = llm_caller()
                return resultado, True
            except (TimeoutError, Exception):
                if intentos >= max_intentos:
                    return None, False
                # Pequeña pausa antes del reintento
                time.sleep(0.1)

        return None, False
