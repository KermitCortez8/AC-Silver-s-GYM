"""Operaciones de aplicación del módulo schedules."""
from __future__ import annotations

from typing import Any


class SchedulesOperations:
    def catalogo_rutina(self) -> list[dict[str, Any]]:
        return self._execute("catalogo_rutina", False)

    def upsert_rutina(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("upsert_rutina", True, payload)

    def horarios(self) -> list[dict[str, Any]]:
        return self._execute("horarios", False)

    def upsert_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("upsert_horario", True, payload)

    def horarios_servicio(self, solo_activos: bool=False) -> list[dict[str, Any]]:
        return self._execute("horarios_servicio", False, solo_activos)

    def get_horario_servicio(self, id_horario_servicio: int) -> dict[str, Any] | None:
        return self._execute("get_horario_servicio", False, id_horario_servicio)

    def upsert_horario_servicio(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("upsert_horario_servicio", True, payload)

    def delete_horario_servicio(self, id_horario_servicio: int) -> None:
        return self._execute("delete_horario_servicio", True, id_horario_servicio)

    def matriculas_horario(self, id_cliente: int | None=None, dni: str | None=None, solo_activas: bool=False) -> list[dict[str, Any]]:
        return self._execute("matriculas_horario", False, id_cliente, dni, solo_activas)

    def get_matricula_horario(self, id_matricula: int) -> dict[str, Any] | None:
        return self._execute("get_matricula_horario", False, id_matricula)

    def asignar_rutina_matricula(self, id_matricula: int, id_rutina: int) -> dict[str, Any]:
        return self._execute("asignar_rutina_matricula", True, id_matricula, id_rutina)

    def trainer_rutinas_cliente(self, dni: str) -> dict[str, Any]:
        return self._execute("trainer_rutinas_cliente", False, dni)

    def registrar_progreso_rutina(self, id_matricula: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("registrar_progreso_rutina", True, id_matricula, payload)

    def trainer_overview(self) -> dict[str, Any]:
        return self._execute("trainer_overview", False)

    def cancelar_matricula_horario(self, id_matricula: int, id_cliente: int | None=None) -> None:
        return self._execute("cancelar_matricula_horario", True, id_matricula, id_cliente)
