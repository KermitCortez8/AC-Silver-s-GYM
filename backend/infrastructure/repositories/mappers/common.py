"""Mapeos de common: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any
import re
from domain.services.gym_values import _today_iso


def _pk(row: dict[str, Any], key: str) -> int:
    if key == "id_usuario":
        return _remote_user_id(row.get(key))
    return int(row.get(key, 0) or 0)


def _remote_pk_value(state_key: str, row: dict[str, Any], fallback: int) -> int:
    if state_key == "usuario":
        return _remote_user_id(row.get("id_usuario")) or int(fallback)
    return int(fallback)


def _remote_user_id(value: Any) -> int:
    raw = str(value or "").strip()
    if raw.isdigit():
        return int(raw)
    match = re.search(r"(\d+)$", raw)
    return int(match.group(1)) if match else 0


def _remote_user_id_or_none(value: Any) -> int | None:
    user_id = _remote_user_id(value)
    return user_id or None


def _split_name(value: str) -> tuple[str, str]:
    parts = [part for part in str(value or "").strip().split() if part]
    if len(parts) <= 1:
        return (parts[0] if parts else "", "")
    return (" ".join(parts[:-1]), parts[-1])


def _phone_number(value: Any) -> int | None:
    digits = re.sub(r"\D+", "", str(value or ""))
    return int(digits) if digits else None


def _status_to_bool(value: Any) -> bool:
    status = str(value or "").strip().upper()
    return status in {"ACTIVO", "ACTIVA", "TRUE", "1", "SI", "SÍ"}


def _bool_to_status(value: Any) -> str:
    return "ACTIVO" if bool(value) else "EN_TRAMITE"


def _date_or_today(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if text else _today_iso()


def _date_or_none(value: Any) -> str | None:
    text = str(value or "").strip()
    return text[:10] if text else None
