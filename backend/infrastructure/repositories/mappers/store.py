"""Mapeos de store: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any
from domain.money import cents
from domain.services.gym_values import _now_iso
from .common import _date_or_today


def _map_sale_detail(row: dict[str, Any], product_names: dict[int, str]) -> dict[str, Any]:
    product_id = int(row.get("id_producto", 0) or 0)
    return {
        "id_producto": product_id,
        "nombre_producto": product_names.get(product_id, ""),
        "cantidad": int(row.get("Cantidad", 1) or 1),
        "precio_unitario": float(row.get("Precio_Unitario") or 0),
        "subtotal": float(row.get("Subtotal") or 0),
    }


def _map_sale(row: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    total_cents = cents(row.get("total_Venta"))
    # Las líneas conservan la base cobrada; no se recalcula con precios ni tasas actuales.
    subtotal_cents = sum(cents(item["subtotal"]) for item in items) if items else total_cents
    return {
        "id_pedido": int(row.get("id_venta", 0) or 0),
        "id_cliente": int(row.get("id_cliente") or 0) or None,
        "cliente_nombre": str(row.get("cliente_nombre") or "Cliente"),
        "cliente_correo": str(row.get("cliente_correo") or ""),
        "cliente_dni": str(row.get("cliente_dni") or ""),
        "fecha_pedido": str(row.get("Fecha_Venta") or _now_iso()),
        "creado_en": str(row.get("created_at") or ""),
        "metodo_pago": str(row.get("metodo_Pago") or ""),
        "referencia_pago": str(row.get("referencia_pago") or ""),
        "observacion_admin": str(row.get("observacion_admin") or ""),
        "estado_pago": str(row.get("estado_pago") or "PAGADO").strip().upper(),
        "estado_pedido": str(row.get("estado_pedido") or "COMPLETADO"),
        "fecha_actualizacion": str(row.get("fecha_actualizacion") or row.get("Fecha_Venta") or _now_iso()),
        "subtotal": subtotal_cents / 100,
        "igv": (total_cents - subtotal_cents) / 100,
        "total": total_cents / 100,
        "items": items,
    }


def _sale_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_venta": int(row.get("id_pedido", 0) or 0),
        "id_cliente": int(row.get("id_cliente") or 0) or None,
        "cliente_nombre": str(row.get("cliente_nombre") or ""),
        "cliente_correo": str(row.get("cliente_correo") or ""),
        "cliente_dni": str(row.get("cliente_dni") or ""),
        "Fecha_Venta": _date_or_today(row.get("fecha_pedido")),
        "total_Venta": float(row["total"] if row.get("total") is not None else row.get("subtotal", 0)),
        "metodo_Pago": str(row.get("metodo_pago") or "tarjeta"),
        "referencia_pago": str(row.get("referencia_pago") or ""),
        "estado_pedido": str(row.get("estado_pedido") or "PENDIENTE"),
        "estado_pago": str(row.get("estado_pago") or "PAGADO"),
        "observacion_admin": str(row.get("observacion_admin") or ""),
        "fecha_actualizacion": _date_or_today(row.get("fecha_actualizacion")),
    }


def _sale_detail_to_remote(sale_id: int, row: dict[str, Any]) -> dict[str, Any]:
    quantity = int(row.get("cantidad", 1) or 1)
    price = float(row["precio_unitario"] if row.get("precio_unitario") is not None else row.get("precio", 0))
    return {
        "id_venta": int(sale_id),
        "id_producto": int(row.get("id_producto", 0) or 0),
        "Cantidad": quantity,
        "Precio_Unitario": price,
        "Subtotal": float(row["subtotal"] if row.get("subtotal") is not None else price * quantity),
    }
