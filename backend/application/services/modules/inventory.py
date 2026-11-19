"""Operaciones de aplicación del módulo inventory."""
from __future__ import annotations

from typing import Any
from application.operations.inventory import (
    InventarioQuery, GetItemInventarioQuery, UpsertInventarioCommand, DeleteInventarioCommand, MovimientosInventarioQuery, RegistrarMovimientoInventarioCommand, ActualizarMovimientoInventarioCommand,
    UnidadesInventarioQuery, ActualizarUnidadInventarioCommand, DarDeBajaUnidadInventarioCommand,
    RestablecerUnidadInventarioCommand,
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

    def unidades_inventario(self) -> list[dict[str, Any]]:
        return self.executor.query(UnidadesInventarioQuery())

    def actualizar_unidad_inventario(self, id_unidad: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(ActualizarUnidadInventarioCommand(id_unidad, payload))

    def restablecer_unidad_inventario(self, id_unidad: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(RestablecerUnidadInventarioCommand(id_unidad, payload))

    def dar_de_baja_unidad_inventario(self, id_unidad: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(DarDeBajaUnidadInventarioCommand(id_unidad, payload))
