# Módulo: infrastructure.repositories.chatbot_repository
# Repositorio de base de datos para las 6 tablas del Chatbot:
#   1. chatbot_conversaciones
#   2. chatbot_mensajes
#   3. chatbot_rate_limit_contadores
#   4. chatbot_uso_tokens
#   5. chatbot_eventos_seguridad
#   6. chatbot_alertas_enviadas
# Soporta concurrencia atómica e implementación en memoria para tests.
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional
import uuid


class MemoryChatbotRepository:
    """Implementación en memoria atómica para tests unitarios y desarrollo rápido."""

    def __init__(self) -> None:
        self.conversaciones: dict[str, dict[str, Any]] = {}
        self.mensajes: list[dict[str, Any]] = []
        # Clave: (clave, tipo_sujeto, ventana_tipo, ventana_inicio_str) -> contador
        self.rate_limit_contadores: dict[tuple[str, str, str, str], int] = {}
        # Clave: (clave, tipo_sujeto, fecha_str) -> tokens
        self.uso_tokens: dict[tuple[str, str, str], int] = {}
        self.eventos_seguridad: list[dict[str, Any]] = []
        # Clave: (tipo_alerta, fecha_str) -> bool
        self.alertas_enviadas: dict[tuple[str, str], bool] = {}

    def get_conversation(self, conversation_id: str) -> Optional[dict[str, Any]]:
        return self.conversaciones.get(conversation_id)

    def create_conversation(
        self,
        conversation_id: Optional[str] = None,
        cliente_id: Optional[int] = None,
        tipo_sujeto: str = "visitante",
        sesion_navegador_id: Optional[str] = None,
        ip_hmac: Optional[str] = None,
    ) -> dict[str, Any]:
        cid = conversation_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        record = {
            "id": cid,
            "cliente_id": cliente_id,
            "tipo_sujeto": tipo_sujeto,
            "sesion_navegador_id": sesion_navegador_id,
            "ip_hmac": ip_hmac,
            "estado": "activa",
            "ultimo_mensaje_en": now,
            "accion_pendiente": None,
            "accion_pendiente_desde": None,
            "creado_en": now,
            "cerrado_en": None,
        }
        self.conversaciones[cid] = record
        return record

    def touch_conversation(self, conversation_id: str) -> None:
        if conversation_id in self.conversaciones:
            self.conversaciones[conversation_id]["ultimo_mensaje_en"] = datetime.now(timezone.utc)

    def set_pending_action(self, conversation_id: str, accion_pendiente: dict[str, Any]) -> None:
        if conversation_id in self.conversaciones:
            self.conversaciones[conversation_id]["accion_pendiente"] = accion_pendiente
            self.conversaciones[conversation_id]["accion_pendiente_desde"] = datetime.now(timezone.utc)

    def clear_pending_action(self, conversation_id: str) -> None:
        if conversation_id in self.conversaciones:
            self.conversaciones[conversation_id]["accion_pendiente"] = None
            self.conversaciones[conversation_id]["accion_pendiente_desde"] = None

    def close_conversation(self, conversation_id: str, estado: str = "cerrada") -> None:
        if conversation_id in self.conversaciones:
            self.conversaciones[conversation_id]["estado"] = estado
            self.conversaciones[conversation_id]["cerrado_en"] = datetime.now(timezone.utc)

    def add_message(
        self,
        conversacion_id: str,
        rol: str,
        contenido: str,
        tokens_consumidos: Optional[int] = None,
        accion_detectada: Optional[str] = None,
    ) -> dict[str, Any]:
        record = {
            "id": str(uuid.uuid4()),
            "conversacion_id": conversacion_id,
            "rol": rol,
            "contenido": contenido,
            "tokens_consumidos": tokens_consumidos,
            "accion_detectada": accion_detectada,
            "creado_en": datetime.now(timezone.utc),
        }
        self.mensajes.append(record)
        return record

    def get_messages(self, conversacion_id: str) -> list[dict[str, Any]]:
        return [m for m in self.mensajes if m["conversacion_id"] == conversacion_id]

    def increment_rate_limit(
        self,
        clave: str,
        tipo_sujeto: str,
        ventana_tipo: str,
        ventana_inicio: datetime,
    ) -> int:
        key = (clave, tipo_sujeto, ventana_tipo, ventana_inicio.isoformat())
        count = self.rate_limit_contadores.get(key, 0) + 1
        self.rate_limit_contadores[key] = count
        return count

    def get_rate_limit(
        self,
        clave: str,
        tipo_sujeto: str,
        ventana_tipo: str,
        ventana_inicio: datetime,
    ) -> int:
        key = (clave, tipo_sujeto, ventana_tipo, ventana_inicio.isoformat())
        return self.rate_limit_contadores.get(key, 0)

    def add_tokens(self, clave: str, tipo_sujeto: str, fecha: date, tokens: int) -> int:
        key = (clave, tipo_sujeto, fecha.isoformat())
        current = self.uso_tokens.get(key, 0) + tokens
        self.uso_tokens[key] = current
        return current

    def get_tokens(self, clave: str, tipo_sujeto: str, fecha: date) -> int:
        key = (clave, tipo_sujeto, fecha.isoformat())
        return self.uso_tokens.get(key, 0)

    def record_security_event(
        self,
        tipo_evento: str,
        conversacion_id: Optional[str] = None,
        cliente_id: Optional[int] = None,
        tipo_sujeto: Optional[str] = None,
        ip_hmac: Optional[str] = None,
        detalle: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        record = {
            "id": str(uuid.uuid4()),
            "conversacion_id": conversacion_id,
            "cliente_id": cliente_id,
            "tipo_sujeto": tipo_sujeto,
            "ip_hmac": ip_hmac,
            "tipo_evento": tipo_evento,
            "detalle": detalle or {},
            "creado_en": datetime.now(timezone.utc),
        }
        self.eventos_seguridad.append(record)
        return record

    def record_alert_if_not_sent(self, tipo_alerta: str, fecha: date, exito: bool) -> bool:
        """
        Retorna True si se pudo registrar la alerta (no se había enviado antes hoy).
        Retorna False si ya existía una alerta para ese tipo_alerta y fecha.
        """
        key = (tipo_alerta, fecha.isoformat())
        if key in self.alertas_enviadas:
            return False
        self.alertas_enviadas[key] = exito
        return True

    def has_alert_been_sent_today(self, tipo_alerta: str, fecha: date) -> bool:
        key = (tipo_alerta, fecha.isoformat())
        return key in self.alertas_enviadas
