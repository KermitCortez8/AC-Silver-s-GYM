"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record


@dataclass(frozen=True)
class ProductosTiendaQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PRODUCTOS_TIENDA,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.store.productos_tienda()


@dataclass(frozen=True)
class GetProductoTiendaQuery:
    operation_kind: ClassVar[str] = 'query'
    id_producto: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PRODUCTOS_TIENDA,)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.store.get_producto_tienda(self.id_producto)


@dataclass(frozen=True)
class UpsertProductoTiendaCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    actor: object = None
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.INVENTARIO,
        Resource.PRODUCTOS_TIENDA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.upsert_producto_tienda(self.payload, self.actor)


@dataclass(frozen=True)
class DeleteProductoTiendaCommand:
    operation_kind: ClassVar[str] = 'command'
    id_producto: int
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.PRODUCTOS_TIENDA,
    )

    def run(self, rules: DomainComponents) -> None:
        return rules.store.delete_producto_tienda(self.id_producto)


@dataclass(frozen=True)
class PedidosTiendaQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PEDIDOS_TIENDA,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.store.pedidos_tienda()


@dataclass(frozen=True)
class CrearPedidoTiendaCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.INVENTARIO,
        Resource.PRODUCTOS_TIENDA,
        Resource.PEDIDOS_TIENDA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.crear_pedido_tienda(self.payload)


@dataclass(frozen=True)
class CrearPedidoTiendaPagoPendienteCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.INVENTARIO,
        Resource.PRODUCTOS_TIENDA,
        Resource.PEDIDOS_TIENDA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.crear_pedido_tienda_pago_pendiente(self.payload)


@dataclass(frozen=True)
class GetPedidoTiendaQuery:
    operation_kind: ClassVar[str] = 'query'
    id_pedido: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PEDIDOS_TIENDA,)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.store.get_pedido_tienda(self.id_pedido)


@dataclass(frozen=True)
class PedidosPagoPendienteQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.PEDIDOS_TIENDA,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.store.pedidos_pago_pendiente()


@dataclass(frozen=True)
class MinutosDesdeCreacionQuery:
    operation_kind: ClassVar[str] = 'query'
    pedido: Record
    resources: ClassVar[tuple[Resource, ...]] = ()

    def run(self, rules: DomainComponents) -> float | None:
        return rules.store.minutos_desde_creacion(self.pedido)


@dataclass(frozen=True)
class RegistrarSesionPagoPedidoCommand:
    operation_kind: ClassVar[str] = 'command'
    id_pedido: int
    session_id: str
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.PEDIDOS_TIENDA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.registrar_sesion_pago_pedido(self.id_pedido, self.session_id)


@dataclass(frozen=True)
class ConfirmarPagoPedidoTiendaCommand:
    operation_kind: ClassVar[str] = 'command'
    id_pedido: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.PEDIDOS_TIENDA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.confirmar_pago_pedido_tienda(self.id_pedido, self.payload)


@dataclass(frozen=True)
class CancelarPedidoPagoPendienteCommand:
    operation_kind: ClassVar[str] = 'command'
    id_pedido: int
    observacion: str = ''
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.INVENTARIO,
        Resource.PRODUCTOS_TIENDA,
        Resource.PEDIDOS_TIENDA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.cancelar_pedido_pago_pendiente(self.id_pedido, self.observacion)


@dataclass(frozen=True)
class ActualizarPedidoTiendaCommand:
    operation_kind: ClassVar[str] = 'command'
    id_pedido: int
    payload: Record
    actor: object = None
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.INVENTARIO,
        Resource.PRODUCTOS_TIENDA,
        Resource.PEDIDOS_TIENDA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.actualizar_pedido_tienda(self.id_pedido, self.payload, self.actor)

