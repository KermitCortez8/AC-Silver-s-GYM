# Módulo: domain.services.chatbot_permissions
# HU-CB11: Permisos según vista y sesión.
# Reglas asociadas: RN-01 (Identidad exclusiva del JWT), RN-02, RN-03, EX-01, EX-13.
from __future__ import annotations

import re
import time
from typing import Any, Callable, Optional
from pydantic import BaseModel

from infrastructure.security import decode_token_payload, verify_session_token


class ContextoUsuario(BaseModel):
    tipo_sujeto: str = "visitante"  # 'visitante' | 'cliente'
    cliente_id: Optional[int] = None
    email: Optional[str] = None
    rol: str = "visitante"
    is_authenticated: bool = False


# Patrones de entrada que intentan pedir datos ajenos o suplantar roles
_PATRONES_DATOS_TERCEROS = [
    re.compile(r"\b(?:datos|info|historial|membres[ií]a|dni|tel[eé]fono|correo)\s+(?:del?|de la)\s+(?:cliente|usuario|persona|socio)\b", re.IGNORECASE),
    re.compile(r"\b(?:cliente|socio|usuario)\s+(?:n[uú]mero|id|c[oó]digo|dni)\s*[:#]?\s*\d+\b", re.IGNORECASE),
    re.compile(r"\bdni\s*[:#]?\s*\d{8}\b", re.IGNORECASE),
]

_PATRONES_SUPLANTACION = [
    re.compile(r"\bsoy\s+(?:el|la)?\s*(?:administrador|admin|recepcionista|entrenador|dueño|gerente)\b", re.IGNORECASE),
    re.compile(r"\bdame\s+permisos\s+de\s+admin\b", re.IGNORECASE),
    re.compile(r"\bact[uú]o\s+como\s+(?:administrador|admin)\b", re.IGNORECASE),
]


def evaluar_sesion(
    token: Optional[str],
    client_resolver: Optional[Callable[[str], Optional[int]]] = None,
) -> tuple[ContextoUsuario, Optional[str]]:
    """
    Evalúa la sesión exclusivamente desde el JWT (RN-01).
    Retorna: (ContextoUsuario, error_code).
    error_code puede ser: None, 'jwt_expirado', 'jwt_invalido'.
    """
    if not token or not token.strip():
        return ContextoUsuario(tipo_sujeto="visitante", rol="visitante", is_authenticated=False), None

    raw_token = token.strip()
    if raw_token.lower().startswith("bearer "):
        raw_token = raw_token[7:].strip()

    # Inspección de payload preliminar
    payload = decode_token_payload(raw_token)
    if not payload:
        return ContextoUsuario(tipo_sujeto="visitante", rol="visitante", is_authenticated=False), "jwt_invalido"

    # Verificación de expiración
    exp = payload.get("exp")
    if exp and exp < time.time():
        return ContextoUsuario(tipo_sujeto="visitante", rol="visitante", is_authenticated=False), "jwt_expirado"

    # Verificación criptográfica con la clave del sistema si aplica
    verified = verify_session_token(raw_token)
    active_payload = verified or payload

    # Resolución de cliente_id
    sub = active_payload.get("sub") or active_payload.get("user_id") or ""
    email = active_payload.get("email") or ""

    resolved_cliente_id: Optional[int] = None
    if client_resolver and sub:
        resolved_cliente_id = client_resolver(str(sub))
    elif active_payload.get("id_cliente"):
        try:
            resolved_cliente_id = int(active_payload["id_cliente"])
        except (ValueError, TypeError):
            resolved_cliente_id = None

    # Si tiene identidad de cliente verificable
    if resolved_cliente_id is not None or sub:
        return ContextoUsuario(
            tipo_sujeto="cliente",
            cliente_id=resolved_cliente_id,
            email=email or None,
            rol="cliente",
            is_authenticated=True,
        ), None

    return ContextoUsuario(tipo_sujeto="visitante", rol="visitante", is_authenticated=False), None


def validar_acceso_datos_propios(
    contexto: ContextoUsuario,
    target_cliente_id: Optional[int],
) -> bool:
    """
    Garantiza que un cliente solo consulte información propia (RN-03, EX-13).
    Si target_cliente_id no coincide con el cliente_id autenticado, rechaza.
    """
    if target_cliente_id is None:
        return True
    if not contexto.is_authenticated or contexto.tipo_sujeto != "cliente":
        return False
    return contexto.cliente_id == target_cliente_id


def detectar_intento_datos_terceros(texto: str) -> bool:
    """Detecta si el mensaje parece solicitar información de un tercero (EX-13)."""
    return any(p.search(texto) for p in _PATRONES_DATOS_TERCEROS)


def detectar_suplantacion_rol(texto: str) -> bool:
    """Detecta si el usuario afirma ser personal administrativo en el chat (RF-CB11-04)."""
    return any(p.search(texto) for p in _PATRONES_SUPLANTACION)
