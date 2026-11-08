# Módulo: domain.services.chatbot_privacy
# HU-CB12: Privacidad de datos personales.
# Reglas asociadas: RN-07 (Enmascaramiento de salida), RN-08 (Contexto mínimo), HU-CB12 Esc. 2 (Filtro entrada).
from __future__ import annotations

import re
from typing import Any, Optional


# Patrones de tarjetas de crédito/débito (16 dígitos continuos o separados por guion/espacio)
_PATRON_TARJETA = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")

# Patrones de contraseñas, claves, pines o CVV/CVC
_PATRON_CONTRASENA = re.compile(
    r"(?:password|contraseña|clave|pin|cvv|cvc)[:=\s]+[^\s,;]+",
    re.IGNORECASE,
)

# Patrones para enmascaramiento de salida (DNI: 8 dígitos, Correo, Teléfono: 9 dígitos peruanos)
_PATRON_DNI = re.compile(r"\b\d{4}(\d{4})\b")
_PATRON_EMAIL = re.compile(r"\b([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b")
_PATRON_TELEFONO = re.compile(r"\b(?:\+?51\s*)?9\d{2}[ -]?\d{3}[ -]?\d{3}\b")


def contiene_datos_sensibles_entrada(texto: str) -> bool:
    """
    Detecta si el usuario ingresó contraseñas, PINs o números de tarjeta en el chat (HU-CB12 Esc. 2).
    """
    if not texto:
        return False
    return bool(_PATRON_TARJETA.search(texto) or _PATRON_CONTRASENA.search(texto))


def enmascarar_dni(texto: str) -> str:
    """Enmascara DNIs de 8 dígitos mostrando solo los últimos 4: ****4521."""
    return _PATRON_DNI.sub(r"****\1", texto)


def enmascarar_email(texto: str) -> str:
    """Enmascara correos mostrando solo la inicial: r***@dominio.com."""
    return _PATRON_EMAIL.sub(r"\1***@\2", texto)


def enmascarar_telefono(texto: str) -> str:
    """Enmascara teléfonos peruanos en formato ***-***-XXX."""
    def _repl(m: re.Match) -> str:
        raw = m.group(0).replace(" ", "").replace("-", "")
        last3 = raw[-3:]
        return f"***-***-{last3}"
    return _PATRON_TELEFONO.sub(_repl, texto)


def enmascarar_datos_sensibles_salida(texto: str) -> str:
    """
    Aplica el pipeline completo de enmascaramiento a la respuesta generada (RN-07).
    """
    if not texto:
        return ""
    enmascarado = enmascarar_email(texto)
    enmascarado = enmascarar_dni(enmascarado)
    enmascarado = enmascarar_telefono(enmascarado)
    return enmascarado


def construir_contexto_minimo(
    info_publica: Optional[dict[str, Any]] = None,
    datos_cliente: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Construye el payload de contexto estructurado para el prompt del LLM (RN-08).
    Excluye identificadores de base de datos internos, DNI en claro, contraseñas o hashes.
    """
    contexto: dict[str, Any] = {}

    if info_publica:
        contexto["info_publica"] = {
            "gimnasio": "Silver Gym Surco",
            "atencion": info_publica.get("atencion", "Lun a Sáb 8:00 am - 8:00 pm"),
            "whatsapp": info_publica.get("whatsapp", "+51 912 794 583"),
        }
        if "horarios" in info_publica:
            contexto["info_publica"]["horarios"] = info_publica["horarios"]
        if "productos" in info_publica:
            contexto["info_publica"]["productos"] = info_publica["productos"]

    if datos_cliente:
        # Solo incluye datos mínimos de membresía/inscripción sin PII completa
        contexto["cliente"] = {
            "tiene_membresia_activa": datos_cliente.get("membresia_activa", False),
            "plan_nombre": datos_cliente.get("plan_nombre"),
            "dias_restantes": datos_cliente.get("dias_restantes"),
            "por_vencer": datos_cliente.get("por_vencer", False),
        }

    return contexto
