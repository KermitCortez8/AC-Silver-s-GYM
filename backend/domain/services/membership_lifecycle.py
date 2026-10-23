"""Vigencia de membresías: la fecha de fin incluye todo el último día en Perú."""
from __future__ import annotations

from datetime import date


ACTIVE = {"ACTIVA", "ACTIVO"}
EXPIRED = {"VENCIDA", "VENCIDO"}


def normalize_membership_status(value) -> str:
    """Compatibilidad de lectura; toda escritura usa los tres estados canónicos."""
    status = str(value or "").strip().upper().replace(" ", "_")
    if status in ACTIVE:
        return "ACTIVO"
    if status in EXPIRED:
        return "VENCIDA"
    # Los estados antiguos inactivos o pendientes nunca conceden acceso.
    return "EN_TRAMITE"


def _status(row: dict) -> str:
    return str(row.get("estado") or "").strip().upper()


def _date(value) -> date | None:
    try:
        return date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def membership_expired(membership: dict, today: str) -> bool:
    end = _date(membership.get("fecha_fin"))
    return _status(membership) in EXPIRED or (
        _status(membership) in ACTIVE and end is not None and end < date.fromisoformat(today)
    )


def membership_current(membership: dict, today: str) -> bool:
    start, end = _date(membership.get("fecha_inicio")), _date(membership.get("fecha_fin"))
    return bool(
        _status(membership) in ACTIVE
        and str(membership.get("estado_pago") or "").strip().upper() == "PAGADO"
        and start and end and start <= date.fromisoformat(today) <= end
    )


def apply_membership_expiration(state: dict, today: str) -> bool:
    changed = False
    by_client: dict[int, list[dict]] = {}
    for membership in state.get("membresia", []):
        by_client.setdefault(int(membership.get("id_cliente") or 0), []).append(membership)
        if _status(membership) in ACTIVE and membership_expired(membership, today):
            membership["estado"] = "VENCIDA"
            changed = True
    for client in state.get("clientes", []):
        memberships = by_client.get(int(client.get("id_cliente") or 0), [])
        # Una renovación vigente conserva el acceso, aunque haya historial vencido.
        if any(membership_current(membership, today) for membership in memberships):
            continue
        if any(membership_expired(membership, today) for membership in memberships):
            if _status(client) != "VENCIDA":
                client["estado"] = "VENCIDA"
                changed = True
    return changed
