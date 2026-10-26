"""Operaciones de aplicación del módulo schedules."""
from __future__ import annotations

from typing import Any
from application.operations.schedules import (
    CatalogoRutinaQuery, UpsertRutinaCommand, HorariosQuery, UpsertHorarioCommand, HorariosServicioQuery, GetHorarioServicioQuery, UpsertHorarioServicioCommand, DeleteHorarioServicioCommand, MatriculasHorarioQuery, GetMatriculaHorarioQuery, AsignarRutinaMatriculaCommand, TrainerRutinasClienteQuery, RegistrarProgresoRutinaCommand, TrainerOverviewQuery, CancelarMatriculaHorarioCommand
)


class SchedulesOperations:
    def __init__(self, executor):
        self.executor = executor

    def catalogo_rutina(self) -> list[dict[str, Any]]:
        return self.executor.query(CatalogoRutinaQuery())

    def upsert_rutina(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(UpsertRutinaCommand(payload))

    def horarios(self) -> list[dict[str, Any]]:
        return self.executor.query(HorariosQuery())

    def upsert_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(UpsertHorarioCommand(payload))

    def horarios_servicio(self, solo_activos: bool=False) -> list[dict[str, Any]]:
        return self.executor.query(HorariosServicioQuery(solo_activos))

    def get_horario_servicio(self, id_horario_servicio: int) -> dict[str, Any] | None:
        return self.executor.query(GetHorarioServicioQuery(id_horario_servicio))

    def upsert_horario_servicio(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(UpsertHorarioServicioCommand(payload))

    def delete_horario_servicio(self, id_horario_servicio: int) -> None:
        return self.executor.execute(DeleteHorarioServicioCommand(id_horario_servicio))

    def matriculas_horario(self, id_cliente: int | None=None, dni: str | None=None, solo_activas: bool=False) -> list[dict[str, Any]]:
        return self.executor.query(MatriculasHorarioQuery(id_cliente, dni, solo_activas))

    def get_matricula_horario(self, id_matricula: int) -> dict[str, Any] | None:
        return self.executor.query(GetMatriculaHorarioQuery(id_matricula))

    def asignar_rutina_matricula(self, id_matricula: int, id_rutina: int) -> dict[str, Any]:
        return self.executor.execute(AsignarRutinaMatriculaCommand(id_matricula, id_rutina))

    def trainer_rutinas_cliente(self, dni: str) -> dict[str, Any]:
        return self.executor.query(TrainerRutinasClienteQuery(dni))

    def registrar_progreso_rutina(self, id_matricula: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(RegistrarProgresoRutinaCommand(id_matricula, payload))

    def trainer_overview(self) -> dict[str, Any]:
        return self.executor.query(TrainerOverviewQuery())

    def cancelar_matricula_horario(self, id_matricula: int, id_cliente: int | None=None) -> None:
        return self.executor.execute(CancelarMatriculaHorarioCommand(id_matricula, id_cliente))
