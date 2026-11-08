# Módulo: domain.services.chatbot_rate_limiter
# HU-CB14: Límite de mensajes y frecuencia (Rate Limiting).
# Reglas asociadas: RN-10 (10/min, 100/día cliente; 5/min, 20/día visitante), EX-04, RNF-CB07.
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
from typing import Optional
from pydantic import BaseModel

from domain.services.chatbot_permissions import ContextoUsuario
from infrastructure.repositories.chatbot_repository import MemoryChatbotRepository


class ResultadoRateLimit(BaseModel):
    permitido: bool
    limite_actual: int
    contador_actual: int
    ventana_afectada: Optional[str] = None  # 'minuto' | 'dia'
    retry_after_seconds: Optional[int] = None


def anonimizar_ip(ip: str, secreto: str) -> str:
    """
    Computa HMAC-SHA256(ip, secreto) para cumplir la Ley 29733 (Perú).
    Nunca guarda la IP en texto claro.
    """
    if not ip:
        return "anon_unknown"
    return hmac.new(secreto.encode("utf-8"), ip.strip().encode("utf-8"), hashlib.sha256).hexdigest()


def obtener_clave_sujeto(
    contexto: ContextoUsuario,
    ip_real: Optional[str],
    secreto_hmac: str,
) -> tuple[str, str]:
    """
    Genera la tupla (clave, tipo_sujeto) para indexar en rate limit y tokens:
    - Cliente: (str(cliente_id), 'cliente')
    - Visitante: (ip_hmac, 'visitante')
    """
    if contexto.is_authenticated and contexto.cliente_id is not None:
        return str(contexto.cliente_id), "cliente"

    ip_hash = anonimizar_ip(ip_real or "127.0.0.1", secreto_hmac)
    return ip_hash, "visitante"


class ChatbotRateLimiter:
    def __init__(
        self,
        repository: MemoryChatbotRepository,
        limite_cliente_min: int = 10,
        limite_cliente_dia: int = 100,
        limite_visitante_min: int = 5,
        limite_visitante_dia: int = 20,
    ) -> None:
        self.repo = repository
        self.limite_cliente_min = limite_cliente_min
        self.limite_cliente_dia = limite_cliente_dia
        self.limite_visitante_min = limite_visitante_min
        self.limite_visitante_dia = limite_visitante_dia

    def verificar_y_consumir(
        self,
        clave: str,
        tipo_sujeto: str,
        ahora: Optional[datetime] = None,
    ) -> ResultadoRateLimit:
        """
        Verifica ventanas de minuto y día (RN-10). Si no excede, incrementa contador.
        Si excede, devuelve permitido=False con retry_after_seconds (EX-04).
        """
        now = ahora or datetime.now(timezone.utc)

        # Truncamiento de ventanas fijas
        ventana_minuto = now.replace(second=0, microsecond=0)
        ventana_dia = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Definir límites según tipo de sujeto
        if tipo_sujeto == "cliente":
            max_min = self.limite_cliente_min
            max_dia = self.limite_cliente_dia
        else:
            max_min = self.limite_visitante_min
            max_dia = self.limite_visitante_dia

        # 1. Evaluar ventana de minuto
        conteo_min = self.repo.get_rate_limit(clave, tipo_sujeto, "minuto", ventana_minuto)
        if conteo_min >= max_min:
            segundos_restantes = 60 - now.second
            return ResultadoRateLimit(
                permitido=False,
                limite_actual=max_min,
                contador_actual=conteo_min,
                ventana_afectada="minuto",
                retry_after_seconds=max(1, segundos_restantes),
            )

        # 2. Evaluar ventana de día
        conteo_dia = self.repo.get_rate_limit(clave, tipo_sujeto, "dia", ventana_dia)
        if conteo_dia >= max_dia:
            segundos_dia = 86400 - (now.hour * 3600 + now.minute * 60 + now.second)
            return ResultadoRateLimit(
                permitido=False,
                limite_actual=max_dia,
                contador_actual=conteo_dia,
                ventana_afectada="dia",
                retry_after_seconds=max(1, segundos_dia),
            )

        # 3. Si ambas están dentro de la cuota, incrementar atómicamente
        nuevo_min = self.repo.increment_rate_limit(clave, tipo_sujeto, "minuto", ventana_minuto)
        self.repo.increment_rate_limit(clave, tipo_sujeto, "dia", ventana_dia)

        return ResultadoRateLimit(
            permitido=True,
            limite_actual=max_min,
            contador_actual=nuevo_min,
        )
