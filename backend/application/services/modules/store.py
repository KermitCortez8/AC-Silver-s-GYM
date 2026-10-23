"""Operaciones de aplicación del módulo store."""
from __future__ import annotations

from typing import Any
from application.operations.store import (
    ProductosTiendaQuery, GetProductoTiendaQuery, UpsertProductoTiendaCommand, DeleteProductoTiendaCommand, PedidosTiendaQuery, CrearPedidoTiendaCommand, CrearPedidoTiendaPagoPendienteCommand, GetPedidoTiendaQuery, PedidosPagoPendienteQuery, MinutosDesdeCreacionQuery, RegistrarSesionPagoPedidoCommand, ConfirmarPagoPedidoTiendaCommand, CancelarPedidoPagoPendienteCommand, ActualizarPedidoTiendaCommand
)


class StoreOperations:
    def __init__(self, executor):
        self.executor = executor

    def productos_tienda(self) -> list[dict[str, Any]]:
        return self.executor.query(ProductosTiendaQuery())

    def get_producto_tienda(self, id_producto: int) -> dict[str, Any] | None:
        return self.executor.query(GetProductoTiendaQuery(id_producto))

    def upsert_producto_tienda(self, payload: dict[str, Any], actor: Any=None) -> dict[str, Any]:
        return self.executor.execute(UpsertProductoTiendaCommand(payload, actor))

    def delete_producto_tienda(self, id_producto: int) -> None:
        return self.executor.execute(DeleteProductoTiendaCommand(id_producto))

    def pedidos_tienda(self) -> list[dict[str, Any]]:
        return self.executor.query(PedidosTiendaQuery())

    def crear_pedido_tienda(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(CrearPedidoTiendaCommand(payload))

    def crear_pedido_tienda_pago_pendiente(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(CrearPedidoTiendaPagoPendienteCommand(payload))

    def get_pedido_tienda(self, id_pedido: int) -> dict[str, Any] | None:
        return self.executor.query(GetPedidoTiendaQuery(id_pedido))

    def pedidos_pago_pendiente(self) -> list[dict[str, Any]]:
        return self.executor.query(PedidosPagoPendienteQuery())

    def minutos_desde_creacion(self, pedido: dict[str, Any]) -> float | None:
        return self.executor.query(MinutosDesdeCreacionQuery(pedido))

    def registrar_sesion_pago_pedido(self, id_pedido: int, session_id: str) -> dict[str, Any]:
        return self.executor.execute(RegistrarSesionPagoPedidoCommand(id_pedido, session_id))

    def confirmar_pago_pedido_tienda(self, id_pedido: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(ConfirmarPagoPedidoTiendaCommand(id_pedido, payload))

    def cancelar_pedido_pago_pendiente(self, id_pedido: int, observacion: str='') -> dict[str, Any]:
        return self.executor.execute(CancelarPedidoPagoPendienteCommand(id_pedido, observacion))

    def actualizar_pedido_tienda(self, id_pedido: int, payload: dict[str, Any], actor: Any=None) -> dict[str, Any]:
        return self.executor.execute(ActualizarPedidoTiendaCommand(id_pedido, payload, actor))
