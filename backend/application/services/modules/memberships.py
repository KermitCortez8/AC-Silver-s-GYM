"""Operaciones de aplicación del módulo memberships."""
from __future__ import annotations

from typing import Any
from application.operations.memberships import (
    PlanesMembresiaQuery, GetPlanMembresiaQuery, UpsertPlanMembresiaCommand, DeletePlanMembresiaCommand, PromocionesQuery, UpsertPromocionCommand, DeletePromocionCommand, GetPromocionVigenteParaPlanQuery, PromocionesVigentesPublicasQuery, MembresiasQuery, MembresiasPorClienteQuery, CrearMembresiaCommand, RegistrarClienteConMembresiaCommand, ActivarMembresiaClienteCommand
)


class MembershipsOperations:
    def __init__(self, executor):
        self.executor = executor

    def planes_membresia(self) -> list[dict[str, Any]]:
        return self.executor.query(PlanesMembresiaQuery())

    def get_plan_membresia(self, id_pm: int) -> dict[str, Any] | None:
        return self.executor.query(GetPlanMembresiaQuery(id_pm))

    def upsert_plan_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(UpsertPlanMembresiaCommand(payload))

    def delete_plan_membresia(self, id_pm: int) -> None:
        return self.executor.execute(DeletePlanMembresiaCommand(id_pm))

    def promociones(self) -> list[dict[str, Any]]:
        return self.executor.query(PromocionesQuery())

    def upsert_promocion(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(UpsertPromocionCommand(payload))

    def delete_promocion(self, id_promocion: int) -> None:
        return self.executor.execute(DeletePromocionCommand(id_promocion))

    def get_promocion_vigente_para_plan(self, state: dict[str, Any], id_pm: int) -> dict[str, Any] | None:
        return self.executor.query(GetPromocionVigenteParaPlanQuery(state, id_pm))

    def promociones_vigentes_publicas(self) -> list[dict[str, Any]]:
        return self.executor.query(PromocionesVigentesPublicasQuery())

    def membresias(self) -> list[dict[str, Any]]:
        return self.executor.query(MembresiasQuery())

    def membresias_por_cliente(self, id_cliente: int) -> list[dict[str, Any]]:
        return self.executor.query(MembresiasPorClienteQuery(id_cliente))

    def crear_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(CrearMembresiaCommand(payload))

    def registrar_cliente_con_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(RegistrarClienteConMembresiaCommand(payload))

    def activar_membresia_cliente(self, id_cliente: int) -> dict[str, Any]:
        return self.executor.execute(ActivarMembresiaClienteCommand(id_cliente))
