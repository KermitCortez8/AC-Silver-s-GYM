"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record, Identifier


@dataclass(frozen=True)
class InventarioQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.inventory.inventario()


@dataclass(frozen=True)
class GetItemInventarioQuery:
    id_item: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.inventory.get_item_inventario(self.id_item)


@dataclass(frozen=True)
class UpsertInventarioCommand:
    payload: Record
    actor: object = None
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV)

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.upsert_inventario(self.payload, self.actor)


@dataclass(frozen=True)
class DeleteInventarioCommand:
    id_item: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.inventory.delete_inventario(self.id_item)


@dataclass(frozen=True)
class MovimientosInventarioQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.MOV_INV,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.inventory.movimientos_inventario()


@dataclass(frozen=True)
class RegistrarMovimientoInventarioCommand:
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV)

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.registrar_movimiento_inventario(self.payload)


@dataclass(frozen=True)
class ActualizarMovimientoInventarioCommand:
    id_mov: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV)

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.actualizar_movimiento_inventario(self.id_mov, self.payload)

