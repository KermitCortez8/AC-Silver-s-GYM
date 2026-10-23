"""Operaciones de aplicación del módulo configuration."""
from __future__ import annotations

from typing import Any


class ConfigurationOperations:
    def tickets(self) -> list[dict[str, Any]]:
        return self._execute("tickets", False)

    def upsert_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("upsert_ticket", True, payload)

    def configuracion_gimnasio(self) -> dict[str, Any]:
        return self._execute("configuracion_gimnasio", False)

    def summary(self) -> dict[str, Any]:
        return self._execute("summary", False)
