"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record


@dataclass(frozen=True)
class TicketsQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.TICKETS_ATENCION,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.tickets()


@dataclass(frozen=True)
class UpsertTicketCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.TICKETS_ATENCION, Resource.USUARIO)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.upsert_ticket(self.payload)


@dataclass(frozen=True)
class ConfiguracionGimnasioQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CONFIGURACION_GIMNASIO,)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.configuracion_gimnasio()


@dataclass(frozen=True)
class SummaryQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.ASISTENCIA,
        Resource.CLIENTES,
        Resource.CONFIGURACION_GIMNASIO,
        Resource.INVENTARIO,
        Resource.MEMBRESIA,
        Resource.MOV_INV,
        Resource.PEDIDOS_TIENDA,
        Resource.USUARIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.dashboard.summary()

