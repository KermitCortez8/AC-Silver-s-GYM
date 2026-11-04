"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record


@dataclass(frozen=True)
class PlanesMembresiaQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PLANES_MEMBRESIA,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.memberships.planes_membresia()


@dataclass(frozen=True)
class GetPlanMembresiaQuery:
    operation_kind: ClassVar[str] = 'query'
    id_pm: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PLANES_MEMBRESIA,)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.memberships.get_plan_membresia(self.id_pm)


@dataclass(frozen=True)
class UpsertPlanMembresiaCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PLANES_MEMBRESIA,)

    def run(self, rules: DomainComponents) -> Record:
        return rules.memberships.upsert_plan_membresia(self.payload)


@dataclass(frozen=True)
class DeletePlanMembresiaCommand:
    operation_kind: ClassVar[str] = 'command'
    id_pm: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PLANES_MEMBRESIA, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PREREGISTROS)

    def run(self, rules: DomainComponents) -> None:
        return rules.memberships.delete_plan_membresia(self.id_pm)


@dataclass(frozen=True)
class PromocionesQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.memberships.promociones()


@dataclass(frozen=True)
class UpsertPromocionCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> Record:
        return rules.memberships.upsert_promocion(self.payload)


@dataclass(frozen=True)
class DeletePromocionCommand:
    operation_kind: ClassVar[str] = 'command'
    id_promocion: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PROMOCIONES, Resource.MEMBRESIA)

    def run(self, rules: DomainComponents) -> None:
        return rules.memberships.delete_promocion(self.id_promocion)


@dataclass(frozen=True)
class GetPromocionVigenteParaPlanQuery:
    operation_kind: ClassVar[str] = 'query'
    state: Record
    id_pm: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.memberships.get_promocion_vigente_para_plan(self.state, self.id_pm)


@dataclass(frozen=True)
class PromocionesVigentesPublicasQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.memberships.promociones_vigentes_publicas()


@dataclass(frozen=True)
class MembresiasQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.memberships.membresias()


@dataclass(frozen=True)
class MembresiasPorClienteQuery:
    operation_kind: ClassVar[str] = 'query'
    id_cliente: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.memberships.membresias_por_cliente(self.id_cliente)


@dataclass(frozen=True)
class CrearMembresiaCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.CLIENTES,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.PROMOCIONES,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.memberships.crear_membresia(self.payload)


@dataclass(frozen=True)
class RegistrarClienteConMembresiaCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.CLIENTES,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.PROMOCIONES,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.memberships.registrar_cliente_con_membresia(self.payload)


@dataclass(frozen=True)
class ActivarMembresiaClienteCommand:
    operation_kind: ClassVar[str] = 'command'
    id_cliente: int
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.CLIENTES,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.PROMOCIONES,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.memberships.activar_membresia_cliente(self.id_cliente)

