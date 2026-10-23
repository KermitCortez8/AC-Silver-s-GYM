# Módulo: gym_domain_service.
# Contiene las reglas principales del negocio del gimnasio.
# Procesa membresías, horarios, inventario, tienda y asistencias.
# Trabaja sobre un estado común sin depender del almacenamiento.
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo


_LIMA = ZoneInfo("America/Lima")


# Ítems de INVENTARIO con este Tipo son la reserva de la tienda. Cada tabla tiene su propio stock:
# las unidades solo pasan a TIENDA_PRODUCTOS con una salida de MOV_INV con destino TIENDA.
TIPO_TIENDA = "Tienda"
ESTADO_DESCONTINUADO = "Descontinuado"
# Estados que el backend calcula solo para ítems Tipo 'Tienda' (Descontinuado es la única marca manual).
ESTADO_DISPONIBLE = "Disponible"
ESTADO_STOCK_BAJO = "Stock bajo"
ESTADO_AGOTADO = "Agotado"
# Destino de las salidas de MOV_INV. VENTA solo aparece en los movimientos de pedidos registrados
# mientras el stock estuvo compartido (migración 014); ya no se generan.
DESTINO_TIENDA = "TIENDA"
DESTINO_VENTA = "VENTA"
# Movimientos de pedidos de esa etapa, reconocidos por el inicio de su descripción.
_MOVIMIENTO_PEDIDO = re.compile(r"^(?:Venta pedido|Devolución por cancelación del pedido) #\d+")
ESTADO_PAGO_PAGADO = "PAGADO"
ESTADO_PAGO_PENDIENTE = "PENDIENTE"
ESTADO_PEDIDO_CANCELADO = "CANCELADO"


# Procesa esta operación.
def _today_iso() -> str:
    return datetime.now(_LIMA).date().isoformat()


# Procesa esta operación.
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Procesa esta operación.
def _now_time() -> str:
    return datetime.now().strftime("%H:%M")


# Procesa esta operación.
def _safe_date(value: str) -> str:
    if value:
        return value
    return _today_iso()


# Procesa esta operación.
def _days_until(date_value: Any, today: str) -> int | None:
    try:
        return (datetime.fromisoformat(str(date_value)[:10]) - datetime.fromisoformat(today)).days
    except Exception:
        return None

# Indica si el pedido ya tiene el cobro confirmado. Los pedidos antiguos sin dato se consideran pagados.
def _pedido_pagado(pedido: dict[str, Any]) -> bool:
    return str(pedido.get("estado_pago") or ESTADO_PAGO_PAGADO).strip().upper() == ESTADO_PAGO_PAGADO


# Convierte una fecha ISO (por ejemplo la created_at de Supabase) a datetime con zona horaria.
def _parse_utc(value: Any) -> datetime | None:
    text = str(value or "").strip().replace("Z", "+00:00")
    if not text:
        return None
    # Supabase puede devolver de 1 a 9 decimales; fromisoformat (antes de Python 3.11) solo acepta 3 o 6.
    text = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], text, count=1)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class PedidoCanceladoConPagoError(ValueError):
    """Llegó un pago para un pedido que ya estaba cancelado: requiere reembolso manual."""

