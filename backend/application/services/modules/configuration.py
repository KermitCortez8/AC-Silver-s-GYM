"""Operaciones de aplicación del módulo configuration."""
from __future__ import annotations

from typing import Any
from application.operations.configuration import (
    TicketsQuery, UpsertTicketCommand, ConfiguracionGimnasioQuery, SummaryQuery
)


class ConfigurationOperations:
    def __init__(self, executor):
        self.executor = executor

    def tickets(self) -> list[dict[str, Any]]:
        return self.executor.query(TicketsQuery())

    def upsert_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(UpsertTicketCommand(payload))

    def configuracion_gimnasio(self) -> dict[str, Any]:
        return self.executor.query(ConfiguracionGimnasioQuery())

    def summary(self) -> dict[str, Any]:
        return self.executor.query(SummaryQuery())
