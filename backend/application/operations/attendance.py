"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record


@dataclass(frozen=True)
class AsistenciaQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.ASISTENCIA,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.attendance.asistencia()


@dataclass(frozen=True)
class RegistrarAsistenciaCommand:
    operation_kind: ClassVar[str] = 'command'
    id_cliente: int
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.ASISTENCIA,
        Resource.CLIENTES,
        Resource.CONFIGURACION_GIMNASIO,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.USUARIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.attendance.registrar_asistencia(self.id_cliente)


@dataclass(frozen=True)
class RegistrarAsistenciaDetalladaCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.ASISTENCIA,
        Resource.CLIENTES,
        Resource.CONFIGURACION_GIMNASIO,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.USUARIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.attendance.registrar_asistencia_detallada(self.payload)


@dataclass(frozen=True)
class RegistrarEntradaHorarioCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.CLIENTES,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.ASISTENCIA,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.attendance.registrar_entrada_horario(self.payload)


@dataclass(frozen=True)
class RegistrarSalidaHorarioCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.CLIENTES,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.ASISTENCIA,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.attendance.registrar_salida_horario(self.payload)


@dataclass(frozen=True)
class ActualizarAsistenciaCommand:
    operation_kind: ClassVar[str] = 'command'
    id_asistencia: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.ASISTENCIA,
        Resource.CLIENTES,
        Resource.CONFIGURACION_GIMNASIO,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.USUARIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.attendance.actualizar_asistencia(self.id_asistencia, self.payload)


@dataclass(frozen=True)
class EliminarAsistenciaCommand:
    operation_kind: ClassVar[str] = 'command'
    id_asistencia: int
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.USUARIO,
        Resource.CLIENTES,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.ASISTENCIA,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
    )

    def run(self, rules: DomainComponents) -> None:
        return rules.attendance.eliminar_asistencia(self.id_asistencia)


@dataclass(frozen=True)
class RegistrarAsistenciaPorDniCommand:
    operation_kind: ClassVar[str] = 'command'
    dni: str
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.ASISTENCIA,
        Resource.CLIENTES,
        Resource.CONFIGURACION_GIMNASIO,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
        Resource.MEMBRESIA,
        Resource.PLANES_MEMBRESIA,
        Resource.USUARIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.attendance.registrar_asistencia_por_dni(self.dni)

