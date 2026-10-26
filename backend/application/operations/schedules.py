"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record


@dataclass(frozen=True)
class CatalogoRutinaQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CATALOGO_RUTINA,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.catalogo_rutina()


@dataclass(frozen=True)
class UpsertRutinaCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.CATALOGO_RUTINA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.upsert_rutina(self.payload)


@dataclass(frozen=True)
class HorariosQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.HORARIO,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.horarios()


@dataclass(frozen=True)
class UpsertHorarioCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.CLIENTES,
        Resource.CATALOGO_RUTINA,
        Resource.HORARIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.upsert_horario(self.payload)


@dataclass(frozen=True)
class HorariosServicioQuery:
    operation_kind: ClassVar[str] = 'query'
    solo_activos: bool = False
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CATALOGO_RUTINA, Resource.HORARIOS_SERVICIO, Resource.MATRICULAS_HORARIO)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.horarios_servicio(self.solo_activos)


@dataclass(frozen=True)
class GetHorarioServicioQuery:
    operation_kind: ClassVar[str] = 'query'
    id_horario_servicio: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.HORARIOS_SERVICIO,)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.schedules.get_horario_servicio(self.id_horario_servicio)


@dataclass(frozen=True)
class UpsertHorarioServicioCommand:
    operation_kind: ClassVar[str] = 'command'
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.CATALOGO_RUTINA,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.upsert_horario_servicio(self.payload)


@dataclass(frozen=True)
class DeleteHorarioServicioCommand:
    operation_kind: ClassVar[str] = 'command'
    id_horario_servicio: int
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
    )

    def run(self, rules: DomainComponents) -> None:
        return rules.schedules.delete_horario_servicio(self.id_horario_servicio)


@dataclass(frozen=True)
class MatriculasHorarioQuery:
    operation_kind: ClassVar[str] = 'query'
    id_cliente: int | None = None
    dni: str | None = None
    solo_activas: bool = False
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.ASISTENCIA,
        Resource.CATALOGO_RUTINA,
        Resource.CLIENTES,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
        Resource.MEMBRESIA,
    )

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.matriculas_horario(self.id_cliente, self.dni, self.solo_activas)


@dataclass(frozen=True)
class GetMatriculaHorarioQuery:
    operation_kind: ClassVar[str] = 'query'
    id_matricula: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.MATRICULAS_HORARIO,)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.schedules.get_matricula_horario(self.id_matricula)


@dataclass(frozen=True)
class AsignarRutinaMatriculaCommand:
    operation_kind: ClassVar[str] = 'command'
    id_matricula: int
    id_rutina: int
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.CLIENTES,
        Resource.CATALOGO_RUTINA,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
        Resource.ASISTENCIA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.asignar_rutina_matricula(self.id_matricula, self.id_rutina)


@dataclass(frozen=True)
class TrainerRutinasClienteQuery:
    operation_kind: ClassVar[str] = 'query'
    dni: str
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.ASISTENCIA,
        Resource.CATALOGO_RUTINA,
        Resource.CLIENTES,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
        Resource.MEMBRESIA,
        Resource.RUTINA_PROGRESO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.trainer_rutinas_cliente(self.dni)


@dataclass(frozen=True)
class RegistrarProgresoRutinaCommand:
    operation_kind: ClassVar[str] = 'command'
    id_matricula: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.CLIENTES,
        Resource.CATALOGO_RUTINA,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
        Resource.ASISTENCIA,
        Resource.RUTINA_PROGRESO,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.registrar_progreso_rutina(self.id_matricula, self.payload)


@dataclass(frozen=True)
class TrainerOverviewQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.ASISTENCIA,
        Resource.CATALOGO_RUTINA,
        Resource.CLIENTES,
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
        Resource.MEMBRESIA,
    )

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.trainer_overview()


@dataclass(frozen=True)
class CancelarMatriculaHorarioCommand:
    operation_kind: ClassVar[str] = 'command'
    id_matricula: int
    id_cliente: int | None = None
    resources: ClassVar[tuple[Resource, ...]] = (
        Resource.HORARIOS_SERVICIO,
        Resource.MATRICULAS_HORARIO,
    )

    def run(self, rules: DomainComponents) -> None:
        return rules.schedules.cancelar_matricula_horario(self.id_matricula, self.id_cliente)

