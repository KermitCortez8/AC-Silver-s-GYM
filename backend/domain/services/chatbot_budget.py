# Módulo: domain.services.chatbot_budget
# HU-CB15: Presupuesto de uso del LLM.
# Reglas asociadas: RN-11 (Tokens campo usage de Groq, costo $0), EX-03 (Modo básico al 100%), [?-P2], [?-V2], [?-P3].
from __future__ import annotations

from datetime import date
from typing import Any, Callable, Optional
from pydantic import BaseModel

from infrastructure.repositories.chatbot_repository import MemoryChatbotRepository


class EstadoPresupuesto(BaseModel):
    modo_basico: bool
    motivo: Optional[str] = None  # 'presupuesto_global_agotado' | 'tope_usuario_agotado' | None
    tokens_usuario_hoy: int
    tokens_globales_hoy: int
    porcentaje_global: int


class ChatbotBudgetController:
    def __init__(
        self,
        repository: MemoryChatbotRepository,
        presupuesto_tpd: int = 180000,
        tope_cliente: int = 8000,
        tope_visitante: int = 3000,
        email_sender: Optional[Callable[[str, int, int], bool]] = None,
    ) -> None:
        self.repo = repository
        self.presupuesto_tpd = presupuesto_tpd
        self.tope_cliente = tope_cliente
        self.tope_visitante = tope_visitante
        self.email_sender = email_sender
        self.umbral_80_tokens = int(0.80 * presupuesto_tpd)

    def consultar_estado(
        self,
        clave: str,
        tipo_sujeto: str,
        fecha: date,
    ) -> EstadoPresupuesto:
        """
        Verifica si la conversación debe operar en modo básico (EX-03, HU-CB15 Esc. 3 y 4).
        """
        tokens_usuario = self.repo.get_tokens(clave, tipo_sujeto, fecha)
        tokens_global = self.repo.get_tokens("__sistema__", "global", fecha)

        porcentaje_global = int((tokens_global / max(1, self.presupuesto_tpd)) * 100)

        # 1. Verificar si se alcanzó el 100% del presupuesto global
        if tokens_global >= self.presupuesto_tpd:
            return EstadoPresupuesto(
                modo_basico=True,
                motivo="presupuesto_global_agotado",
                tokens_usuario_hoy=tokens_usuario,
                tokens_globales_hoy=tokens_global,
                porcentaje_global=porcentaje_global,
            )

        # 2. Verificar tope individual por usuario (HU-CB15 Esc. 4)
        tope_usuario = self.tope_cliente if tipo_sujeto == "cliente" else self.tope_visitante
        if tokens_usuario >= tope_usuario:
            return EstadoPresupuesto(
                modo_basico=True,
                motivo="tope_usuario_agotado",
                tokens_usuario_hoy=tokens_usuario,
                tokens_globales_hoy=tokens_global,
                porcentaje_global=porcentaje_global,
            )

        return EstadoPresupuesto(
            modo_basico=False,
            tokens_usuario_hoy=tokens_usuario,
            tokens_globales_hoy=tokens_global,
            porcentaje_global=porcentaje_global,
        )

    def registrar_consumo(
        self,
        clave: str,
        tipo_sujeto: str,
        fecha: date,
        tokens_respuesta: int,
    ) -> EstadoPresupuesto:
        """
        Registra los tokens devueltos por el campo 'usage' de Groq y gestiona alertas por correo.
        """
        if tokens_respuesta <= 0:
            return self.consultar_estado(clave, tipo_sujeto, fecha)

        # Acumular consumo individual
        tokens_usuario = self.repo.add_tokens(clave, tipo_sujeto, fecha, tokens_respuesta)

        # Acumular consumo global del sistema
        tokens_global = self.repo.add_tokens("__sistema__", "global", fecha, tokens_respuesta)

        porcentaje_global = int((tokens_global / max(1, self.presupuesto_tpd)) * 100)

        # Evaluar alertas deduplicadas (máximo 1 envío por tipo y por día)
        if tokens_global >= self.presupuesto_tpd:
            if not self.repo.has_alert_been_sent_today("tope_100", fecha):
                exito = self.email_sender("tope_100", tokens_global, self.presupuesto_tpd) if self.email_sender else False
                self.repo.record_alert_if_not_sent("tope_100", fecha, exito)

        elif tokens_global >= self.umbral_80_tokens:
            if not self.repo.has_alert_been_sent_today("umbral_80", fecha):
                exito = self.email_sender("umbral_80", tokens_global, self.presupuesto_tpd) if self.email_sender else False
                self.repo.record_alert_if_not_sent("umbral_80", fecha, exito)

        return self.consultar_estado(clave, tipo_sujeto, fecha)
