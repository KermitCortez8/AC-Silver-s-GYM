"""Operaciones de aplicación del módulo attendance."""
from __future__ import annotations

from typing import Any
from application.operations.attendance import (
    AsistenciaQuery, RegistrarAsistenciaCommand, RegistrarAsistenciaDetalladaCommand, RegistrarEntradaHorarioCommand, RegistrarSalidaHorarioCommand, ActualizarAsistenciaCommand, EliminarAsistenciaCommand, RegistrarAsistenciaPorDniCommand
)


class AttendanceOperations:
    def __init__(self, executor):
        self.executor = executor

    def asistencia(self) -> list[dict[str, Any]]:
        return self.executor.query(AsistenciaQuery())

    def registrar_asistencia(self, id_cliente: int) -> dict[str, Any]:
        return self.executor.execute(RegistrarAsistenciaCommand(id_cliente))

    def registrar_asistencia_detallada(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(RegistrarAsistenciaDetalladaCommand(payload))

    def registrar_entrada_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(RegistrarEntradaHorarioCommand(payload))

    def registrar_salida_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(RegistrarSalidaHorarioCommand(payload))

    def actualizar_asistencia(self, id_asistencia: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(ActualizarAsistenciaCommand(id_asistencia, payload))

    def eliminar_asistencia(self, id_asistencia: int) -> None:
        return self.executor.execute(EliminarAsistenciaCommand(id_asistencia))

    def registrar_asistencia_por_dni(self, dni: str) -> dict[str, Any]:
        return self.executor.execute(RegistrarAsistenciaPorDniCommand(dni))
