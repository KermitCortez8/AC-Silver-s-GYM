"""Operaciones de aplicación del módulo inventory."""
from __future__ import annotations

from typing import Any


class InventoryOperations:
    def inventario(self) -> list[dict[str, Any]]:
        return self._execute("inventario", False)

    def get_item_inventario(self, id_item: int) -> dict[str, Any] | None:
        return self._execute("get_item_inventario", False, id_item)

    def upsert_inventario(self, payload: dict[str, Any], actor: Any=None) -> dict[str, Any]:
        return self._execute("upsert_inventario", True, payload, actor)

    def delete_inventario(self, id_item: int) -> dict[str, Any] | None:
        return self._execute("delete_inventario", True, id_item)

    def movimientos_inventario(self) -> list[dict[str, Any]]:
        return self._execute("movimientos_inventario", False)

    def registrar_movimiento_inventario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("registrar_movimiento_inventario", True, payload)

    def actualizar_movimiento_inventario(self, id_mov: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("actualizar_movimiento_inventario", True, id_mov, payload)
