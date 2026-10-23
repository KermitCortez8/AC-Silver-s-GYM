"""Operaciones de aplicación del módulo memberships."""
from __future__ import annotations

from typing import Any


class MembershipsOperations:
    def planes_membresia(self) -> list[dict[str, Any]]:
        return self._execute("planes_membresia", False)

    def get_plan_membresia(self, id_pm: int) -> dict[str, Any] | None:
        return self._execute("get_plan_membresia", False, id_pm)

    def upsert_plan_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("upsert_plan_membresia", True, payload)

    def delete_plan_membresia(self, id_pm: int) -> None:
        return self._execute("delete_plan_membresia", True, id_pm)

    def promociones(self) -> list[dict[str, Any]]:
        return self._execute("promociones", False)

    def upsert_promocion(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("upsert_promocion", True, payload)

    def delete_promocion(self, id_promocion: int) -> None:
        return self._execute("delete_promocion", True, id_promocion)

    def get_promocion_vigente_para_plan(self, state: dict[str, Any], id_pm: int) -> dict[str, Any] | None:
        return self._execute("get_promocion_vigente_para_plan", False, state, id_pm)

    def promociones_vigentes_publicas(self) -> list[dict[str, Any]]:
        return self._execute("promociones_vigentes_publicas", False)

    def membresias(self) -> list[dict[str, Any]]:
        return self._execute("membresias", False)

    def membresias_por_cliente(self, id_cliente: int) -> list[dict[str, Any]]:
        return self._execute("membresias_por_cliente", False, id_cliente)

    def crear_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("crear_membresia", True, payload)

    def registrar_cliente_con_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("registrar_cliente_con_membresia", True, payload)

    def activar_membresia_cliente(self, id_cliente: int) -> dict[str, Any]:
        return self._execute("activar_membresia_cliente", True, id_cliente)
