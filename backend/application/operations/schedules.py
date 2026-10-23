"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record, Identifier


@dataclass(frozen=True)
class CatalogoRutinaQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CATALOGO_RUTINA,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.catalogo_rutina()


@dataclass(frozen=True)
class UpsertRutinaCommand:
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.CATALOGO_RUTINA, Resource.HORARIO, Resource.HORARIOS_SERVICIO, Resource.MATRICULAS_HORARIO, Resource.RUTINA_PROGRESO, Resource.ASISTENCIA, Resource.CONFIGURACION_GIMNASIO)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.upsert_rutina(self.payload)


@dataclass(frozen=True)
class HorariosQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.HORARIO,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.horarios()


@dataclass(frozen=True)
class UpsertHorarioCommand:
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.CATALOGO_RUTINA, Resource.HORARIO, Resource.HORARIOS_SERVICIO, Resource.MATRICULAS_HORARIO, Resource.RUTINA_PROGRESO, Resource.ASISTENCIA, Resource.CONFIGURACION_GIMNASIO)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.upsert_horario(self.payload)


@dataclass(frozen=True)
class HorariosServicioQuery:
    solo_activos: bool = False
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.MATRICULAS_HORARIO, Resource.HORARIOS_SERVICIO, Resource.CATALOGO_RUTINA, Resource.ASISTENCIA, Resource.RUTINA_PROGRESO)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.horarios_servicio(self.solo_activos)


@dataclass(frozen=True)
class GetHorarioServicioQuery:
    id_horario_servicio: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.MATRICULAS_HORARIO, Resource.HORARIOS_SERVICIO, Resource.CATALOGO_RUTINA, Resource.ASISTENCIA, Resource.RUTINA_PROGRESO)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.schedules.get_horario_servicio(self.id_horario_servicio)


@dataclass(frozen=True)
class UpsertHorarioServicioCommand:
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.CATALOGO_RUTINA, Resource.HORARIO, Resource.HORARIOS_SERVICIO, Resource.MATRICULAS_HORARIO, Resource.RUTINA_PROGRESO, Resource.ASISTENCIA, Resource.CONFIGURACION_GIMNASIO)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.upsert_horario_servicio(self.payload)


@dataclass(frozen=True)
class DeleteHorarioServicioCommand:
    id_horario_servicio: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.CATALOGO_RUTINA, Resource.HORARIO, Resource.HORARIOS_SERVICIO, Resource.MATRICULAS_HORARIO, Resource.RUTINA_PROGRESO, Resource.ASISTENCIA, Resource.CONFIGURACION_GIMNASIO)

    def run(self, rules: DomainComponents) -> None:
        return rules.schedules.delete_horario_servicio(self.id_horario_servicio)


@dataclass(frozen=True)
class MatriculasHorarioQuery:
    id_cliente: int | None = None
    dni: str | None = None
    solo_activas: bool = False
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.MATRICULAS_HORARIO, Resource.HORARIOS_SERVICIO, Resource.CATALOGO_RUTINA, Resource.ASISTENCIA, Resource.RUTINA_PROGRESO)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.schedules.matriculas_horario(self.id_cliente, self.dni, self.solo_activas)


@dataclass(frozen=True)
class GetMatriculaHorarioQuery:
    id_matricula: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.MATRICULAS_HORARIO, Resource.HORARIOS_SERVICIO, Resource.CATALOGO_RUTINA, Resource.ASISTENCIA, Resource.RUTINA_PROGRESO)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.schedules.get_matricula_horario(self.id_matricula)


@dataclass(frozen=True)
class AsignarRutinaMatriculaCommand:
    id_matricula: int
    id_rutina: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.CATALOGO_RUTINA, Resource.HORARIO, Resource.HORARIOS_SERVICIO, Resource.MATRICULAS_HORARIO, Resource.RUTINA_PROGRESO, Resource.ASISTENCIA, Resource.CONFIGURACION_GIMNASIO)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.asignar_rutina_matricula(self.id_matricula, self.id_rutina)


@dataclass(frozen=True)
class TrainerRutinasClienteQuery:
    dni: str
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.MATRICULAS_HORARIO, Resource.HORARIOS_SERVICIO, Resource.CATALOGO_RUTINA, Resource.ASISTENCIA, Resource.RUTINA_PROGRESO)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.trainer_rutinas_cliente(self.dni)


@dataclass(frozen=True)
class RegistrarProgresoRutinaCommand:
    id_matricula: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.CATALOGO_RUTINA, Resource.HORARIO, Resource.HORARIOS_SERVICIO, Resource.MATRICULAS_HORARIO, Resource.RUTINA_PROGRESO, Resource.ASISTENCIA, Resource.CONFIGURACION_GIMNASIO)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.registrar_progreso_rutina(self.id_matricula, self.payload)


@dataclass(frozen=True)
class TrainerOverviewQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.MATRICULAS_HORARIO, Resource.HORARIOS_SERVICIO, Resource.CATALOGO_RUTINA, Resource.ASISTENCIA, Resource.RUTINA_PROGRESO)

    def run(self, rules: DomainComponents) -> Record:
        return rules.schedules.trainer_overview()


@dataclass(frozen=True)
class CancelarMatriculaHorarioCommand:
    id_matricula: int
    id_cliente: int | None = None
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.CATALOGO_RUTINA, Resource.HORARIO, Resource.HORARIOS_SERVICIO, Resource.MATRICULAS_HORARIO, Resource.RUTINA_PROGRESO, Resource.ASISTENCIA, Resource.CONFIGURACION_GIMNASIO)

    def run(self, rules: DomainComponents) -> None:
        return rules.schedules.cancelar_matricula_horario(self.id_matricula, self.id_cliente)

