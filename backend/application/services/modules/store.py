"""Operaciones de aplicación del módulo store."""
from __future__ import annotations

from typing import Any


class StoreOperations:
    def productos_tienda(self) -> list[dict[str, Any]]:
        return self._execute("productos_tienda", False)

    def get_producto_tienda(self, id_producto: int) -> dict[str, Any] | None:
        return self._execute("get_producto_tienda", False, id_producto)

    def upsert_producto_tienda(self, payload: dict[str, Any], actor: Any=None) -> dict[str, Any]:
        return self._execute("upsert_producto_tienda", True, payload, actor)

    def delete_producto_tienda(self, id_producto: int) -> None:
        return self._execute("delete_producto_tienda", True, id_producto)

    def pedidos_tienda(self) -> list[dict[str, Any]]:
        return self._execute("pedidos_tienda", False)

    def crear_pedido_tienda(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("crear_pedido_tienda", True, payload)

    def crear_pedido_tienda_pago_pendiente(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("crear_pedido_tienda_pago_pendiente", True, payload)

    def get_pedido_tienda(self, id_pedido: int) -> dict[str, Any] | None:
        return self._execute("get_pedido_tienda", False, id_pedido)

    def pedidos_pago_pendiente(self) -> list[dict[str, Any]]:
        return self._execute("pedidos_pago_pendiente", False)

    def minutos_desde_creacion(self, pedido: dict[str, Any]) -> float | None:
        return self._execute("minutos_desde_creacion", False, pedido)

    def registrar_sesion_pago_pedido(self, id_pedido: int, session_id: str) -> dict[str, Any]:
        return self._execute("registrar_sesion_pago_pedido", True, id_pedido, session_id)

    def confirmar_pago_pedido_tienda(self, id_pedido: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("confirmar_pago_pedido_tienda", True, id_pedido, payload)

    def cancelar_pedido_pago_pendiente(self, id_pedido: int, observacion: str='') -> dict[str, Any]:
        return self._execute("cancelar_pedido_pago_pendiente", True, id_pedido, observacion)

    def actualizar_pedido_tienda(self, id_pedido: int, payload: dict[str, Any], actor: Any=None) -> dict[str, Any]:
        return self._execute("actualizar_pedido_tienda", True, id_pedido, payload, actor)
