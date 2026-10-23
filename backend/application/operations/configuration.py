"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record, Identifier


@dataclass(frozen=True)
class TicketsQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.TICKETS_ATENCION,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.tickets()


@dataclass(frozen=True)
class UpsertTicketCommand:
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.TICKETS_ATENCION,)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.upsert_ticket(self.payload)


@dataclass(frozen=True)
class ConfiguracionGimnasioQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CONFIGURACION_GIMNASIO,)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.configuracion_gimnasio()


@dataclass(frozen=True)
class SummaryQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.PEDIDOS_TIENDA, Resource.ASISTENCIA, Resource.MOV_INV, Resource.USUARIO, Resource.CONFIGURACION_GIMNASIO, Resource.MATRICULAS_HORARIO, Resource.HORARIOS_SERVICIO)

    def run(self, rules: DomainComponents) -> Record:
        return rules.dashboard.summary()

