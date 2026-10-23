"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record, Identifier


@dataclass(frozen=True)
class ProductosTiendaQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.store.productos_tienda()


@dataclass(frozen=True)
class GetProductoTiendaQuery:
    id_producto: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.store.get_producto_tienda(self.id_producto)


@dataclass(frozen=True)
class UpsertProductoTiendaCommand:
    payload: Record
    actor: object = None
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.upsert_producto_tienda(self.payload, self.actor)


@dataclass(frozen=True)
class DeleteProductoTiendaCommand:
    id_producto: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> None:
        return rules.store.delete_producto_tienda(self.id_producto)


@dataclass(frozen=True)
class PedidosTiendaQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.store.pedidos_tienda()


@dataclass(frozen=True)
class CrearPedidoTiendaCommand:
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.crear_pedido_tienda(self.payload)


@dataclass(frozen=True)
class CrearPedidoTiendaPagoPendienteCommand:
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.crear_pedido_tienda_pago_pendiente(self.payload)


@dataclass(frozen=True)
class GetPedidoTiendaQuery:
    id_pedido: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.store.get_pedido_tienda(self.id_pedido)


@dataclass(frozen=True)
class PedidosPagoPendienteQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.store.pedidos_pago_pendiente()


@dataclass(frozen=True)
class MinutosDesdeCreacionQuery:
    pedido: Record
    resources: ClassVar[tuple[Resource, ...]] = ()

    def run(self, rules: DomainComponents) -> float | None:
        return rules.store.minutos_desde_creacion(self.pedido)


@dataclass(frozen=True)
class RegistrarSesionPagoPedidoCommand:
    id_pedido: int
    session_id: str
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.registrar_sesion_pago_pedido(self.id_pedido, self.session_id)


@dataclass(frozen=True)
class ConfirmarPagoPedidoTiendaCommand:
    id_pedido: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.confirmar_pago_pedido_tienda(self.id_pedido, self.payload)


@dataclass(frozen=True)
class CancelarPedidoPagoPendienteCommand:
    id_pedido: int
    observacion: str = ''
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.cancelar_pedido_pago_pendiente(self.id_pedido, self.observacion)


@dataclass(frozen=True)
class ActualizarPedidoTiendaCommand:
    id_pedido: int
    payload: Record
    actor: object = None
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.INVENTARIO, Resource.PRODUCTOS_TIENDA, Resource.MOV_INV, Resource.PEDIDOS_TIENDA)

    def run(self, rules: DomainComponents) -> Record:
        return rules.store.actualizar_pedido_tienda(self.id_pedido, self.payload, self.actor)

