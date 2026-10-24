"""Mapeos de configuration: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any


def _map_config(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "capacidad_total": max(1, int(row.get("capacidad_total") or 30)),
        "capacidad_por_hora": max(1, int(row.get("capacidad_por_hora") or 10)),
    }


def _config_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "capacidad_total": max(1, int(row.get("capacidad_total") or 30)),
        "capacidad_por_hora": max(1, int(row.get("capacidad_por_hora") or 10)),
    }
