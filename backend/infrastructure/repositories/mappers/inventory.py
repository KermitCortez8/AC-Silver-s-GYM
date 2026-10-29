"""Mapeos de inventory: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any
from .common import _remote_user_id_or_none, _date_or_today, _remote_user_id


def _map_inventory(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_item": int(row.get("id_item", 0) or 0),
        "nombre_item": str(row.get("Nombre_item") or ""),
        "tipo": str(row.get("Tipo") or "General"),
        "cantidad_stock": int(row.get("Cantidad_Stock_E", 0) or 0),
        "estado": str(row.get("Estado") or "Operativo"),
        "n_activo": row.get("N_ACTIVO"),
        "unidad_venta": str(row.get("unidad_venta") or "unidad"),
        "precio_venta": float(row.get("precio_venta") or 0),
        "stock_minimo": int(row["stock_minimo"] if row.get("stock_minimo") is not None else 1),
        "ubicacion": str(row.get("ubicacion") or "Almacén"),
        "observaciones": str(row.get("observaciones") or ""),
        "archivado": bool(row.get("archivado") or False),
    }


def _archived_field(row: dict[str, Any]) -> dict[str, Any]:
    # Solo se envía al archivar: las instalaciones sin la migración 018 siguen guardando lo demás.
    return {"archivado": True} if row.get("archivado") else {}


def _inventory_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_archived_field(row),
        "id_item": int(row.get("id_item", 0) or 0),
        "Nombre_item": str(row.get("nombre_item") or ""),
        "Tipo": str(row.get("tipo") or "General"),
        "Cantidad_Stock_E": int(row.get("cantidad_stock", 0) or 0),
        "Estado": str(row.get("estado") or "Operativo"),
        "N_ACTIVO": int(row.get("n_activo") or 0) or None,
        "unidad_venta": str(row.get("unidad_venta") or "unidad"),
        "precio_venta": float(row.get("precio_venta") or 0),
        "stock_minimo": int(row["stock_minimo"] if row.get("stock_minimo") is not None else 1),
        "ubicacion": str(row.get("ubicacion") or "Almacén"),
        "observaciones": str(row.get("observaciones") or ""),
    }


def _map_inventory_move(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_mov": int(row.get("id_mov", 0) or 0),
        "id_item": int(row.get("id_item", 0) or 0),
        "id_usuario": int(row.get("id_usuario", 0) or 0) if row.get("id_usuario") else None,
        "tipo_movimiento": str(row.get("tipo_movimiento") or "entrada"),
        "fecha_movimiento": str(row.get("fecha_movimiento") or ""),
        "descripcion": str(row.get("descripcion") or ""),
        "cantidad": int(row.get("cantidad", 1) or 1),
        "destino": str(row.get("destino") or "").strip().upper() or None,
    }


def _inventory_move_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_mov": int(row.get("id_mov", 0) or 0),
        "id_item": int(row.get("id_item", 0) or 0),
        "id_usuario": _remote_user_id_or_none(row.get("id_usuario")),
        "tipo_movimiento": str(row.get("tipo_movimiento") or "entrada").strip().lower(),
        "fecha_movimiento": _date_or_today(row.get("fecha_movimiento")),
        "descripcion": str(row.get("descripcion") or ""),
        "cantidad": max(1, int(row.get("cantidad", 1) or 1)),
        "destino": str(row.get("destino") or "").strip().upper() or None,
    }


def _map_product(row: dict[str, Any]) -> dict[str, Any]:
    stock = int(row.get("cantidad_stock", 0) or 0)
    return {
        "id_producto": int(row.get("id_producto", 0) or 0),
        "id_item": int(row.get("id_item") or 0) or None,
        "nombre_producto": str(row.get("nombre_Producto") or ""),
        "categoria": str(row.get("categoria") or "General"),
        "descripcion": str(row.get("descripcion") or ""),
        "unidad_venta": str(row.get("unidad_venta") or "unidad"),
        "precio_venta": float(row.get("precio_Venta") or 0),
        "cantidad_stock": stock,
        "stock_minimo": int(row["stock_minimo"] if row.get("stock_minimo") is not None else 5),
        "estado": "Disponible" if stock > 0 else "Sin stock",
        "imagen_url": str(row.get("imagen_url") or ""),
        "archivado": bool(row.get("archivado") or False),
    }


def _product_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_archived_field(row),
        "id_producto": int(row.get("id_producto", 0) or 0),
        "id_item": int(row.get("id_item") or 0) or None,
        "nombre_Producto": str(row.get("nombre_producto") or ""),
        "categoria": str(row.get("categoria") or "General"),
        "descripcion": str(row.get("descripcion") or ""),
        "unidad_venta": str(row.get("unidad_venta") or "unidad"),
        "precio_Venta": float(row.get("precio_venta") or 0),
        # Stock propio de la tienda: sube con reposiciones desde INVENTARIO y baja con ventas.
        "cantidad_stock": int(row.get("cantidad_stock", 0) or 0),
        "stock_minimo": int(row["stock_minimo"] if row.get("stock_minimo") is not None else 5),
        "imagen_url": str(row.get("imagen_url") or ""),
    }
