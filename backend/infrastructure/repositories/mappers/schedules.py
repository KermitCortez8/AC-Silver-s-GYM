"""Mapeos de schedules: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any
import json
from domain.services.gym_domain_service import GymDomainService
from .common import _remote_user_id_or_none, _date_or_none, _date_or_today, _remote_user_id


def _map_routine(row: dict[str, Any]) -> dict[str, Any]:
    ejercicios = row.get("ejercicios")
    if isinstance(ejercicios, str):
        try:
            ejercicios = json.loads(ejercicios)
        except Exception:
            ejercicios = []
    elif not isinstance(ejercicios, list):
        ejercicios = []
    return {
        "id_rutina": int(row.get("id_rutina", 0) or 0),
        "servicio": str(row.get("servicio") or "fitness").strip().lower(),
        "nombre_rutina": str(row.get("Nombre_rutina") or ""),
        "zonas_musculares": str(row.get("Zonas_musculares") or ""),
        "color": str(row.get("Color") or "Azul"),
        "ejercicios": ejercicios,
    }


def _routine_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_rutina": int(row.get("id_rutina", 0) or 0),
        "servicio": str(row.get("servicio") or "fitness").strip().lower(),
        "Nombre_rutina": str(row.get("nombre_rutina") or ""),
        "Zonas_musculares": str(row.get("zonas_musculares") or ""),
        "Color": str(row.get("color") or "Azul"),
        "ejercicios": row.get("ejercicios") if isinstance(row.get("ejercicios"), list) else [],
    }


def _map_schedule(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_horario": int(row.get("id_horario", 0) or 0),
        "id_cliente": int(row.get("id_cliente", 0) or 0),
        "id_rutina": int(row.get("id_rutina", 0) or 0),
        "dia_semana": str(row.get("Dia_semana") or "Lunes"),
        "hora_inicio": str(row.get("Hora_inicio") or "06:00"),
        "hora_fin": str(row.get("Hora_fin") or "07:00"),
        "capacidad_maxima": 1,
        "cupos_usados": 1,
    }


def _schedule_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_horario": int(row.get("id_horario", 0) or 0),
        "id_cliente": int(row.get("id_cliente", 0) or 0),
        "id_rutina": int(row.get("id_rutina", 0) or 0),
        "Dia_semana": str(row.get("dia_semana") or "Lunes"),
        "Hora_inicio": str(row.get("hora_inicio") or "06:00"),
        "Hora_fin": str(row.get("hora_fin") or "07:00"),
    }


def _map_service_schedule(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
        "servicio": str(row.get("servicio") or "fitness"),
        "id_rutina": int(row.get("id_rutina", 0) or 0),
        "codigo_dia": str(row.get("codigo_dia") or "LUN"),
        "dia": str(row.get("dia") or "lunes"),
        "hora_inicio": str(row.get("hora_inicio") or "06:00"),
        "hora_fin": str(row.get("hora_fin") or "07:00"),
        "cupos": max(1, int(row.get("cupos", 10) or 10)),
        "cupos_usados": 0,
        "activo": bool(row.get("activo", True)),
    }


def _service_schedule_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
        "servicio": str(row.get("servicio") or "fitness").strip().lower(),
        "id_rutina": int(row.get("id_rutina", 0) or 0) or None,
        "codigo_dia": str(row.get("codigo_dia") or GymDomainService().schedule_day_code(str(row.get("dia") or ""))).strip().upper(),
        "dia": GymDomainService().normalize_schedule_day(row.get("dia")) or "lunes",
        "hora_inicio": str(row.get("hora_inicio") or "06:00"),
        "hora_fin": str(row.get("hora_fin") or "07:00"),
        "cupos": max(1, int(row.get("cupos", 10) or 10)),
        "activo": bool(row.get("activo", True)),
    }


def _map_schedule_enrollment(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_matricula": int(row.get("id_matricula", 0) or 0),
        "id_cliente": int(row.get("id_cliente", 0) or 0),
        "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
        "id_rutina": int(row.get("id_rutina", 0) or 0) or None,
        "fecha_matricula": str(row.get("fecha_matricula") or ""),
        "fecha_clase": str(row.get("fecha_clase") or "") or None,
        "estado": str(row.get("estado") or "ACTIVA").strip().upper(),
    }


def _schedule_enrollment_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_matricula": int(row.get("id_matricula", 0) or 0),
        "id_cliente": int(row.get("id_cliente", 0) or 0),
        "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
        "id_rutina": int(row.get("id_rutina", 0) or 0) or None,
        "fecha_matricula": _date_or_today(row.get("fecha_matricula")),
        "fecha_clase": _date_or_none(row.get("fecha_clase")),
        "estado": str(row.get("estado") or "ACTIVA").strip().upper(),
    }


def _map_routine_progress(row: dict[str, Any]) -> dict[str, Any]:
    ejercicios_detalle = row.get("ejercicios_detalle")
    if isinstance(ejercicios_detalle, str):
        try:
            ejercicios_detalle = json.loads(ejercicios_detalle)
        except Exception:
            ejercicios_detalle = []
    elif not isinstance(ejercicios_detalle, list):
        ejercicios_detalle = []
    return {
        "id_progreso": int(row.get("id_progreso", 0) or 0),
        "id_matricula": int(row.get("id_matricula", 0) or 0),
        "id_rutina": int(row.get("id_rutina", 0) or 0),
        "fecha": str(row.get("fecha") or ""),
        "estado": str(row.get("estado") or "REALIZADO").strip().upper(),
        "observacion": str(row.get("observacion") or ""),
        "id_usuario": row.get("id_usuario"),
        "ejercicios_detalle": ejercicios_detalle,
    }


def _routine_progress_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_progreso": int(row.get("id_progreso", 0) or 0),
        "id_matricula": int(row.get("id_matricula", 0) or 0),
        "id_rutina": int(row.get("id_rutina", 0) or 0),
        "fecha": _date_or_today(row.get("fecha")),
        "estado": str(row.get("estado") or "REALIZADO").strip().upper(),
        "observacion": str(row.get("observacion") or ""),
        "id_usuario": _remote_user_id_or_none(row.get("id_usuario")),
        "ejercicios_detalle": row.get("ejercicios_detalle") if isinstance(row.get("ejercicios_detalle"), list) else [],
    }


def _map_ticket(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_ticket": int(row.get("id_ticket", 0) or 0),
        "id_cliente": int(row.get("id_cliente", 0) or 0),
        "id_usuario": int(row.get("id_usuario", 0) or 0) if row.get("id_usuario") else None,
        "tipo_ticket": str(row.get("tipo_ticket") or ""),
        "descripcion": str(row.get("descripcion") or ""),
        "estado_ticket": str(row.get("estado_ticket") or "Abierto"),
        "fecha_emitido": str(row.get("fecha_emitido") or ""),
        "fecha_cierre": str(row.get("fecha_cierre") or ""),
    }


def _ticket_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_ticket": int(row.get("id_ticket", 0) or 0),
        "id_cliente": int(row.get("id_cliente", 0) or 0),
        "id_usuario": _remote_user_id_or_none(row.get("id_usuario")),
        "tipo_ticket": str(row.get("tipo_ticket") or ""),
        "descripcion": str(row.get("descripcion") or ""),
        "estado_ticket": str(row.get("estado_ticket") or "Abierto"),
        "fecha_emitido": _date_or_today(row.get("fecha_emitido")),
        "fecha_cierre": _date_or_none(row.get("fecha_cierre")),
    }
