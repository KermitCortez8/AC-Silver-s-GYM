# Módulo: domain.services.chatbot_actions
# HU-CB13: Lista cerrada de acciones permitidas y re-validación en backend.
# Reglas asociadas: RN-04, RN-05 (Acciones prohibidas), RN-06 (Confirmación previa), EX-10.
from __future__ import annotations

import re
from typing import Any, Optional
from pydantic import BaseModel

from domain.services.chatbot_permissions import ContextoUsuario


# Lista cerrada y taxativa de acciones permitidas
ACCIONES_PERMITIDAS = {
    "consulta_informacion_publica",
    "gym_hours",
    "attention_hours",
    "activities",
    "products",
    "contact_human",
    "consulta_membresia_propia",
    "inscripcion_actividad",
    "cancelacion_inscripcion",
    "agregar_carrito",
    "generar_solicitud_compra",
    "consultar_pedidos_propios",
}

# Acciones que requieren rol de cliente autenticado
ACCIONES_SOLO_CLIENTE = {
    "consulta_membresia_propia",
    "inscripcion_actividad",
    "cancelacion_inscripcion",
    "agregar_carrito",
    "generar_solicitud_compra",
    "consultar_pedidos_propios",
}

# Acciones que modifican estado y requieren confirmación explícita previa (RN-06)
ACCIONES_CON_MUTACION = {
    "inscripcion_actividad",
    "cancelacion_inscripcion",
    "generar_solicitud_compra",
}

# Patrones de acciones prohibidas terminantemente (RN-05, EX-10)
_PATRONES_PROHIBIDOS = [
    re.compile(r"\b(?:confirmar|aprobar|validar|registrar|anular|devolver)\s+(?:el\s+|la\s+|mi\s+|un\s+|una\s+)?(?:pago|pagos|transferencia|voucher)\b", re.IGNORECASE),
    re.compile(r"\b(?:activar|renovar|congelar|descongelar)\s+(?:el\s+|la\s+|mi\s+|un\s+|una\s+)?(?:membres[ií]a|plan)\b", re.IGNORECASE),
    re.compile(r"\b(?:cambiar|modificar|alterar|editar)\s+(?:el\s+|la\s+|los\s+|las\s+|mi\s+)?(?:precio|precios|tarifa|costo)\b", re.IGNORECASE),
    re.compile(r"\b(?:editar|modificar|borrar|eliminar)\s+(?:datos|perfil|cliente|usuario)\b", re.IGNORECASE),
    re.compile(r"\bdescuento\s+especial\b", re.IGNORECASE),
    re.compile(r"\bcongelar\s+(?:el\s+|mi\s+)?plan\b", re.IGNORECASE),
]


class ResultadoAutorizacion(BaseModel):
    autorizada: bool
    requiere_confirmacion: bool = False
    accion: str
    motivo_rechazo: Optional[str] = None
    es_prohibida: bool = False


def es_accion_prohibida(texto: str) -> bool:
    """Verifica si el mensaje solicita una acción administrativa prohibida (RN-05, EX-10)."""
    if not texto:
        return False
    return any(p.search(texto) for p in _PATRONES_PROHIBIDOS)


def autorizar_accion(
    accion: str,
    contexto: ContextoUsuario,
    parametros: Optional[dict[str, Any]] = None,
    confirmado: bool = False,
) -> ResultadoAutorizacion:
    """
    Función determinista que re-valida la acción en el backend FastAPI (RN-04).
    No confía en el LLM ni en el frontend.
    """
    parametros = parametros or {}

    # 1. Validar que la acción esté en la lista cerrada
    if accion not in ACCIONES_PERMITIDAS:
        return ResultadoAutorizacion(
            autorizada=False,
            accion=accion,
            motivo_rechazo=f"La acción '{accion}' no forma parte de la lista cerrada permitida.",
            es_prohibida=True,
        )

    # 2. Validar privilegios de sesión si la acción es solo para clientes
    if accion in ACCIONES_SOLO_CLIENTE:
        if not contexto.is_authenticated or contexto.tipo_sujeto != "cliente":
            return ResultadoAutorizacion(
                autorizada=False,
                accion=accion,
                motivo_rechazo="Esta acción requiere iniciar sesión como cliente del gimnasio.",
            )

    # 3. Validar si requiere confirmación explícita previa (RN-06)
    if accion in ACCIONES_CON_MUTACION:
        if not confirmado:
            return ResultadoAutorizacion(
                autorizada=True,
                requiere_confirmacion=True,
                accion=accion,
            )

    return ResultadoAutorizacion(
        autorizada=True,
        requiere_confirmacion=False,
        accion=accion,
    )
