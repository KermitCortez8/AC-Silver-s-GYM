# Módulo: app.core.chatbot_settings
# Re-exporta la configuración del Chatbot para acceso centralizado.
from __future__ import annotations

from infrastructure.chatbot_config import ChatbotSettings, get_chatbot_settings

__all__ = ["ChatbotSettings", "get_chatbot_settings"]
