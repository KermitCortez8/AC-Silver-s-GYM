"""Mapeos de inventory: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any
from .common import _remote_user_id_or_none, _date_or_today, _date_or_none, _remote_user_id


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
        "eliminado": bool(row.get("eliminado") or False),
        "prefijo_activo": str(row.get("prefijo_activo") or ""),
    }


def _archived_field(row: dict[str, Any]) -> dict[str, Any]:
    # archivado (papelera, migración 018) siempre se envía para poder restaurar.
    # eliminado solo al eliminar: las instalaciones sin la migración 019 siguen guardando lo demás.
    return {"archivado": bool(row.get("archivado")), **({"eliminado": True} if row.get("eliminado") else {})}


def _inventory_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_archived_field(row),
        # El prefijo solo viaja cuando existe: sin la migración 026 los demás artículos se siguen guardando.
        **({"prefijo_activo": str(row["prefijo_activo"])} if row.get("prefijo_activo") else {}),
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


def _map_inventory_unit(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_unidad": int(row.get("id_unidad", 0) or 0),
        "id_item": int(row.get("id_item", 0) or 0),
        "correlativo": int(row.get("correlativo", 0) or 0),
        "codigo": str(row.get("codigo") or ""),
        "estado": str(row.get("estado") or "Operativo"),
        "ubicacion": str(row.get("ubicacion") or "Almacén"),
        "observaciones": str(row.get("observaciones") or ""),
        "fecha_alta": str(row.get("fecha_alta") or "")[:10],
        "fecha_baja": str(row.get("fecha_baja") or "")[:10] or None,
    }


def _inventory_unit_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_unidad": int(row.get("id_unidad", 0) or 0),
        "id_item": int(row.get("id_item", 0) or 0),
        "correlativo": int(row.get("correlativo", 0) or 0),
        "codigo": str(row.get("codigo") or ""),
        "estado": str(row.get("estado") or "Operativo"),
        "ubicacion": str(row.get("ubicacion") or "Almacén"),
        "observaciones": str(row.get("observaciones") or ""),
        "fecha_alta": _date_or_today(row.get("fecha_alta")),
        "fecha_baja": _date_or_none(row.get("fecha_baja")),
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
        "id_unidad": int(row["id_unidad"]) if row.get("id_unidad") else None,
        "hora_movimiento": str(row.get("hora_movimiento") or "")[:8] or None,
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
        # Solo viajan cuando existen: sin la migración 027 los movimientos de cantidad se siguen guardando.
        **({"id_unidad": int(row["id_unidad"])} if row.get("id_unidad") else {}),
        **({"hora_movimiento": str(row["hora_movimiento"])[:8]} if row.get("hora_movimiento") else {}),
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
        "eliminado": bool(row.get("eliminado") or False),
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
