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
        Resource.INVENTARIO_UNIDADES,
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
        Resource.INVENTARIO_UNIDADES,
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
        Resource.INVENTARIO_UNIDADES,
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
        Resource.INVENTARIO_UNIDADES,
        Resource.PRODUCTOS_TIENDA,
        Resource.MOV_INV,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.actualizar_movimiento_inventario(self.id_mov, self.payload)



@dataclass(frozen=True)
class UnidadesInventarioQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO, Resource.INVENTARIO_UNIDADES)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.inventory.unidades_inventario()


@dataclass(frozen=True)
class ActualizarUnidadInventarioCommand:
    operation_kind: ClassVar[str] = 'command'
    id_unidad: int
    payload: Record
    # MOV_INV y USUARIO: el cambio de ubicación queda registrado como traslado.
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.INVENTARIO,
        Resource.INVENTARIO_UNIDADES,
        Resource.PRODUCTOS_TIENDA,
        Resource.MOV_INV,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.actualizar_unidad_inventario(self.id_unidad, self.payload)


@dataclass(frozen=True)
class RestablecerUnidadInventarioCommand:
    operation_kind: ClassVar[str] = 'command'
    id_unidad: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.INVENTARIO,
        Resource.INVENTARIO_UNIDADES,
        Resource.PRODUCTOS_TIENDA,
        Resource.MOV_INV,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.restablecer_unidad_inventario(self.id_unidad, self.payload)


@dataclass(frozen=True)
class DarDeBajaUnidadInventarioCommand:
    operation_kind: ClassVar[str] = 'command'
    id_unidad: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.INVENTARIO,
        Resource.INVENTARIO_UNIDADES,
        Resource.PRODUCTOS_TIENDA,
        Resource.MOV_INV,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.inventory.dar_de_baja_unidad_inventario(self.id_unidad, self.payload)
