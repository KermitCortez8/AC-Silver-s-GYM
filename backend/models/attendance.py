from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AttendanceCorrection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=0)
    motivo: str = Field(min_length=5, max_length=500)
    fecha: date
    hora_entrada: str = Field(pattern=r"^\d{2}:\d{2}(:\d{2})?$")
    hora_salida: str = Field(default="", pattern=r"^(\d{2}:\d{2}(:\d{2})?)?$")
    fecha_salida: date | None = None


class AttendanceAnnulment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=0)
    motivo: str = Field(min_length=5, max_length=500)


class AttendanceFilters(BaseModel):
    desde: date | None = None
    hasta: date | None = None
    dni: str = Field(default="", pattern=r"^(\d{8})?$")
    servicio: Literal["", "fitness", "musculacion", "cardio", "baile", "gimnasio"] = ""
    tipo: Literal["", "general", "horario"] = ""
    estado: Literal["", "dentro", "completada", "anulada"] = ""


class GeneralAttendanceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dni: str = Field(pattern=r"^\d{8}$")
    request_id: UUID
