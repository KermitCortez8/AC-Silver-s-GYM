"""Mapeos de memberships: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any
from domain.services.membership_lifecycle import normalize_membership_status
from .common import _date_or_none, _date_or_today


def _map_plan(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_pm": int(row.get("id_PM") or row.get("id_pm") or row.get("id_plan") or 0),
        "nombre_plan": str(row.get("Nombre_Plan") or row.get("nombre_plan") or row.get("nombre") or "MENSUAL").strip().upper(),
        "duracion": str(row.get("Duración") or row.get("Duracion") or row.get("duracion") or "30 dias"),
        "precio": float(row.get("Precio") or row.get("precio") or 0),
        "descripcion": str(row.get("descripcion") or ""),
        "beneficios": str(row.get("beneficios") or ""),
        "activo": bool(row.get("Activo", row.get("activo", True))),
    }


def _plan_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_PM": int(row.get("id_pm", 0) or 0),
        "Nombre_Plan": str(row.get("nombre_plan") or "MENSUAL").strip().upper(),
        "Duración": str(row.get("duracion") or "30 dias"),
        "Precio": float(row.get("precio") or 0),
        "descripcion": str(row.get("descripcion") or ""),
        "beneficios": str(row.get("beneficios") or ""),
        "Activo": bool(row.get("activo", True)),
    }


def _map_promotion(row: dict[str, Any]) -> dict[str, Any]:
    raw_plans = row.get("planes_aplicables") or []
    if isinstance(raw_plans, str):
        raw_plans = [part.strip() for part in raw_plans.split(",") if part.strip()]
    return {
        "id_promocion": int(row.get("id_promocion", 0) or 0),
        "nombre": str(row.get("nombre") or ""),
        "limite_cupos": row.get("limite_cupos"),
        "usos_actuales": int(row.get("usos_actuales") or 0),
        "icono_etiqueta": str(row.get("icono_etiqueta") or "🏷️"),
        "palabra_clave": str(row.get("palabra_clave") or ""),
        "descripcion": str(row.get("descripcion") or ""),
        "tipo_descuento": str(row.get("tipo_descuento") or "porcentaje"),
        "valor_descuento": float(row.get("valor_descuento") or 0),
        "fecha_inicio": str(row.get("fecha_inicio") or ""),
        "fecha_fin": str(row.get("fecha_fin") or ""),
        "activo": bool(row.get("activo", True)),
        "planes_aplicables": [int(value) for value in raw_plans if str(value).strip().isdigit()],
    }


def _promotion_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_promocion": int(row.get("id_promocion", 0) or 0),
        "nombre": str(row.get("nombre") or ""),
        "limite_cupos": row.get("limite_cupos"),
        "usos_actuales": int(row.get("usos_actuales") or 0),
        "icono_etiqueta": str(row.get("icono_etiqueta") or "🏷️"),
        "palabra_clave": str(row.get("palabra_clave") or ""),
        "descripcion": str(row.get("descripcion") or ""),
        "tipo_descuento": str(row.get("tipo_descuento") or "porcentaje"),
        "valor_descuento": float(row.get("valor_descuento") or 0),
        "fecha_inicio": _date_or_none(row.get("fecha_inicio")),
        "fecha_fin": _date_or_none(row.get("fecha_fin")),
        "activo": bool(row.get("activo", True)),
        "planes_aplicables": list(row.get("planes_aplicables") or []),
    }


def _map_membership(row: dict[str, Any]) -> dict[str, Any]:
    membership_status = str(row.get("Estado") or "PENDIENTE_PAGO")
    default_payment_status = (
        "PAGADO"
        if membership_status.strip().upper() in {"ACTIVA", "ACTIVO", "EN_TRAMITE"}
        else "PENDIENTE"
    )
    return {
        "id_membresia": int(row.get("id_membresia", 0) or 0),
        "fecha_inicio": str(row.get("Fecha_Inicio") or ""),
        "fecha_fin": str(row.get("Fecha_Fin") or ""),
        "estado": normalize_membership_status(membership_status),
        "id_cliente": int(row.get("id_cliente", 0) or 0),
        "id_promocion": int(row.get("id_promocion") or 0) or None,
        "id_pm": int(row.get("id_PM", 0) or 0),
        "monto_pago": float(row.get("monto_pago", 0) or 0),
        "estado_pago": str(row.get("estado_pago") or default_payment_status),
        "metodo_pago": str(row.get("metodo_pago") or ""),
        "referencia_pago": str(row.get("referencia_pago") or ""),
        "fecha_pago": str(row.get("fecha_pago") or ""),
    }


def _membership_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_membresia": int(row.get("id_membresia", 0) or 0),
        "Fecha_Inicio": _date_or_today(row.get("fecha_inicio")),
        "Fecha_Fin": _date_or_today(row.get("fecha_fin")),
        "Estado": normalize_membership_status(row.get("estado")),
        "id_cliente": int(row.get("id_cliente", 0) or 0),
        "id_promocion": int(row.get("id_promocion") or 0) or None,
        "id_PM": int(row.get("id_pm", 0) or 0) or None,
        "monto_pago": float(row["monto_pago"]) if row.get("monto_pago") is not None else None,
        "estado_pago": str(row.get("estado_pago") or "PENDIENTE"),
        "metodo_pago": str(row.get("metodo_pago") or ""),
        "referencia_pago": str(row.get("referencia_pago") or ""),
        "fecha_pago": _date_or_none(row.get("fecha_pago")),
    }
