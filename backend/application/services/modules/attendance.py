"""Operaciones de aplicación del módulo attendance."""
from __future__ import annotations

from typing import Any


class AttendanceOperations:
    def asistencia(self) -> list[dict[str, Any]]:
        return self._execute("asistencia", False)

    def registrar_asistencia(self, id_cliente: int) -> dict[str, Any]:
        return self._execute("registrar_asistencia", True, id_cliente)

    def registrar_asistencia_detallada(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("registrar_asistencia_detallada", True, payload)

    def registrar_entrada_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("registrar_entrada_horario", True, payload)

    def registrar_salida_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("registrar_salida_horario", True, payload)

    def actualizar_asistencia(self, id_asistencia: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("actualizar_asistencia", True, id_asistencia, payload)

    def eliminar_asistencia(self, id_asistencia: int) -> None:
        return self._execute("eliminar_asistencia", True, id_asistencia)

    def registrar_asistencia_por_dni(self, dni: str) -> dict[str, Any]:
        return self._execute("registrar_asistencia_por_dni", True, dni)
