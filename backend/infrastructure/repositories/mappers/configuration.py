"""Mapeos de configuration: conversión explícita entre filas y datos de negocio."""
from __future__ import annotations
from typing import Any


def _map_config(row: dict[str, Any]) -> dict[str, Any]:
    return _config_to_remote(row)


def _config_to_remote(row: dict[str, Any]) -> dict[str, Any]:
    config = {
        "capacidad_total": max(1, int(row.get("capacidad_total") or 30)),
        "capacidad_por_hora": max(1, int(row.get("capacidad_por_hora") or 10)),
    }
    if row.get("parametros_horarios") is not None:
        config["parametros_horarios"] = row["parametros_horarios"]
    return config
