"""Mapeos de attendance: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any
from domain.services.client_identifiers import parse_client_id
from .common import _remote_user_id_or_none, _date_or_today, _remote_user_id


def _map_attendance(row: dict[str, Any]) -> dict[str, Any]:
    client_id = int(row.get("id_cliente", 0) or 0)
    hour = str(row.get("Hora") or row.get("hora_entrada") or "")
    return {
        "id_asistencia": int(row.get("id_asistencia", 0) or 0),
        "id_cliente": f"SGCLI{client_id:03d}",
        "id_cliente_num": client_id,
        "fecha": str(row.get("Fecha") or ""),
        "hora": hour,
        "hora_entrada": str(row.get("hora_entrada") or hour),
        "hora_salida": str(row.get("hora_salida") or ""),
        "fecha_salida": str(row.get("fecha_salida") or "") or None,
        "limite_salida": str(row.get("limite_salida") or "") or None,
        "salida_tardia": bool(row.get("salida_tardia", False)),
        "anulado": bool(row.get("anulado", False)),
        "auditoria": row.get("auditoria") or [],
        "version": int(row.get("version") or 0),
        "servicio": str(row.get("servicio") or "fitness"),
        "id_usuario_registra": row.get("id_usuario_registra"),
        "id_membresia": row.get("id_membresia"),
        "id_matricula": row.get("id_matricula"),
        "id_horario_servicio": row.get("id_horario_servicio"),
        "validacion": bool(row.get("Validación", True)),
    }


def _attendance_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    hour = str(row.get("hora") or row.get("hora_entrada") or "00:00")
    return {
        "id_asistencia": int(row.get("id_asistencia", 0) or 0),
        "id_cliente": int(row.get("id_cliente_num") or parse_client_id(row.get("id_cliente"))),
        "id_membresia": int(row.get("id_membresia") or 0) or None,
        "Fecha": _date_or_today(row.get("fecha")),
        "Hora": hour,
        "Validación": bool(row.get("validacion", True)),
        "servicio": str(row.get("servicio") or "fitness").strip().lower(),
        "id_usuario_registra": _remote_user_id_or_none(row.get("id_usuario_registra")),
        "id_matricula": int(row.get("id_matricula") or 0) or None,
        "id_horario_servicio": int(row.get("id_horario_servicio") or 0) or None,
        "hora_entrada": str(row.get("hora_entrada") or hour),
        "hora_salida": str(row.get("hora_salida")) if row.get("hora_salida") else None,
        "fecha_salida": row.get("fecha_salida") or None,
        "limite_salida": row.get("limite_salida") or None,
        "salida_tardia": bool(row.get("salida_tardia", False)),
        "anulado": bool(row.get("anulado", False)),
        "auditoria": row.get("auditoria") or [],
        "version": int(row.get("version") or 0),
    }
