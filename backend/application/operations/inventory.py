"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record


@dataclass(frozen=True)
class InventarioQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.inventory.inventario()


@dataclass(frozen=True)
class GetItemInventarioQuery:
    operation_kind: ClassVar[str] = 'query'
    id_item: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO,)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.inventory.get_item_inventario(self.id_item)


@dataclass(frozen=True)
class UpsertInventarioCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    actor: object = None
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.INVENTARIO,
        Resource.PRODUCTOS_TIENDA,
        Resource.MOV_INV,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.upsert_inventario(self.payload, self.actor)


@dataclass(frozen=True)
class DeleteInventarioCommand:
    operation_kind: ClassVar[str] = 'command'
    id_item: int
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.INVENTARIO,
        Resource.PRODUCTOS_TIENDA,
        Resource.MOV_INV,
    )

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.inventory.delete_inventario(self.id_item)


@dataclass(frozen=True)
class MovimientosInventarioQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.MOV_INV,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.inventory.movimientos_inventario()


@dataclass(frozen=True)
class RegistrarMovimientoInventarioCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.INVENTARIO,
        Resource.PRODUCTOS_TIENDA,
        Resource.MOV_INV,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.registrar_movimiento_inventario(self.payload)


@dataclass(frozen=True)
class ActualizarMovimientoInventarioCommand:
    operation_kind: ClassVar[str] = 'command'
    id_mov: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.INVENTARIO,
        Resource.PRODUCTOS_TIENDA,
        Resource.MOV_INV,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.actualizar_movimiento_inventario(self.id_mov, self.payload)

