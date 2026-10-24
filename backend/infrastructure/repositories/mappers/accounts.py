"""Mapeos de accounts: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any
from domain.services.accounts_rules import user_role_prefix, internal_account_active
from .common import _bool_to_status, _date_or_today, _phone_number, _remote_user_id, _split_name, _status_to_bool


def _map_client(row: dict[str, Any]) -> dict[str, Any]:
    client_id = int(row.get("id_cliente", 0) or 0)
    name = " ".join([str(row.get("Nombres") or "").strip(), str(row.get("Apellidos") or "").strip()]).strip()
    return {
        "id_cliente": client_id,
        "id_usuario": f"SGCLI{client_id:03d}",
        "nombre": name,
        "correo": str(row.get("Correo") or row.get("Email") or ""),
        "telefono": str(row.get("Telefono") or ""),
        "dni": str(row.get("DNI") or ""),
        "plan": str(row.get("Plan") or "MENSUAL").strip().upper(),
        "promocion": "SIN PROMOCION",
        "estado": _bool_to_status(row.get("Estado")),
        "password_hash": str(row.get("password_hash") or row.get("Password_Hash") or ""),
        "google_sub": str(row.get("google_sub") or ""),
        "fecha_registro": str(row.get("Fecha_Registro") or ""),
        "origen_registro": str(row.get("origen_registro") or ""),
    }


def _client_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    nombres, apellidos = _split_name(str(row.get("nombre") or ""))
    correo = str(row.get("correo") or row.get("email") or "").strip()
    return {
        "id_cliente": int(row.get("id_cliente", 0) or 0),
        "Nombres": nombres,
        "Apellidos": apellidos,
        "DNI": str(row.get("dni") or ""),
        "Telefono": _phone_number(row.get("telefono")),
        "Email": correo,
        "Correo": correo,
        "Fecha_Registro": _date_or_today(row.get("fecha_registro")),
        "Estado": _status_to_bool(row.get("estado")),
        "Plan": str(row.get("plan") or "MENSUAL").strip().upper(),
        "password_hash": str(row.get("password_hash") or ""),
        "google_sub": str(row.get("google_sub") or "") or None,
        "origen_registro": str(row.get("origen_registro") or "") or None,
    }


def _map_user(row: dict[str, Any]) -> dict[str, Any]:
    user_id = int(row.get("id_usuario", 0) or 0)
    role = str(row.get("Rol") or "staff").strip().lower()
    prefix = user_role_prefix(role)
    return {
        "id_usuario": str(row.get("codigo_usuario") or (f"SG{prefix}{user_id:03d}" if user_id else "")),
        "nombre": str(row.get("Nombre") or f"Usuario {row.get('id_usuario', '')}"),
        "correo": str(row.get("Correo") or row.get("Email") or ""),
        "telefono": str(row.get("Telefono") or ""),
        "dni": str(row.get("DNI") or ""),
        "rol": role,
        "estado": "ACTIVO" if bool(row.get("Estado", True)) else "INACTIVO",
        "password_hash": str(row.get("Contraseña") or row.get("ContraseÃ±a") or ""),
        "google_sub": str(row.get("google_sub") or ""),
    }


def _map_user_legacy(row: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
    password = str(row.get("Contraseña") or local.get("password_hash") or "")
    return {
        "id_usuario": int(row.get("id_usuario", 0) or 0),
        "nombre": str(local.get("nombre") or f"Usuario {row.get('id_usuario', '')}"),
        "correo": str(local.get("correo") or ""),
        "telefono": str(local.get("telefono") or ""),
        "dni": str(row.get("DNI") or local.get("dni") or ""),
        "rol": str(row.get("Rol") or local.get("rol") or "staff").strip().lower(),
        "estado": "ACTIVO" if bool(row.get("Estado", True)) else "INACTIVO",
        "password_hash": password,
        "google_sub": str(row.get("google_sub") or ""),
    }


def _user_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_usuario": _remote_user_id(row.get("id_usuario")),
        "codigo_usuario": str(row.get("id_usuario") or ""),
        "Nombre": str(row.get("nombre") or ""),
        "Correo": str(row.get("correo") or row.get("email") or ""),
        "Telefono": str(row.get("telefono") or ""),
        "DNI": str(row.get("dni") or ""),
        "Contraseña": str(row.get("password_hash") or ""),
        "google_sub": str(row.get("google_sub") or "") or None,
        "Rol": str(row.get("rol") or "staff").strip().lower(),
        "Estado": internal_account_active({"estado": row.get("estado", "ACTIVO")}),
    }
