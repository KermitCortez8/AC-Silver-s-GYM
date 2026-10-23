"""Operaciones de aplicación del módulo inventory."""
from __future__ import annotations

from typing import Any
from application.operations.inventory import (
    InventarioQuery, GetItemInventarioQuery, UpsertInventarioCommand, DeleteInventarioCommand, MovimientosInventarioQuery, RegistrarMovimientoInventarioCommand, ActualizarMovimientoInventarioCommand
)


class InventoryOperations:
    def __init__(self, executor):
        self.executor = executor

    def inventario(self) -> list[dict[str, Any]]:
        return self.executor.query(InventarioQuery())

    def get_item_inventario(self, id_item: int) -> dict[str, Any] | None:
        return self.executor.query(GetItemInventarioQuery(id_item))

    def upsert_inventario(self, payload: dict[str, Any], actor: Any=None) -> dict[str, Any]:
        return self.executor.execute(UpsertInventarioCommand(payload, actor))

    def delete_inventario(self, id_item: int) -> dict[str, Any] | None:
        return self.executor.execute(DeleteInventarioCommand(id_item))

    def movimientos_inventario(self) -> list[dict[str, Any]]:
        return self.executor.query(MovimientosInventarioQuery())

    def registrar_movimiento_inventario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(RegistrarMovimientoInventarioCommand(payload))

    def actualizar_movimiento_inventario(self, id_mov: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(ActualizarMovimientoInventarioCommand(id_mov, payload))
