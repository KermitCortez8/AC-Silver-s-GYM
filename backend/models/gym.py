from __future__ import annotations

from typing import Any, Literal,Optional

from pydantic import BaseModel, Field


class UsuarioInput(BaseModel):
    id_usuario: str | int | None = None
    nombre: str = ""
    correo: str = ""
    telefono: str = ""
    dni: str = ""
    rol: Literal["admin", "trainer", "staff"]


class ClienteInput(BaseModel):
    id_usuario: str | int | None = None
    nombre: str = ""
    correo: str = ""
    telefono: str = ""
    dni: str = ""
    plan: Literal["MENSUAL", "3 MESES", "ANUAL"] = "MENSUAL"
    promocion: str = "SIN PROMOCION"
    estado: str = "ACTIVO"


class PlanMembresiaInput(BaseModel):
    id_pm: int | None = None
    nombre_plan: str
    duracion: str
    precio: int


class MembresiaInput(BaseModel):
    id_membresia: int | None = None
    fecha_inicio: str
    fecha_fin: str
    estado: str = "Activa"
    id_cliente: int
    id_pm: int


class RegistrarClienteMembresiaInput(BaseModel):
    cliente: ClienteInput
    id_pm: int
    fecha_inicio: str
    fecha_fin: str


class InventarioInput(BaseModel):
    id_item: int | None = None
    nombre_item: str
    tipo: str
    cantidad_stock: int
    estado: str = "Operativo"
    n_activo: int = 1


class ProductoTiendaInput(BaseModel):
    id_producto: Optional[int] = None
    nombre_producto: str
    descripcion: Optional[str] = ""
    categoria: Optional[str] = "General"
    precio_venta: float
    cantidad_stock: int
    stock_minimo: Optional[int] = 5
    estado: Optional[str] = "Disponible"


class MovimientoInventarioInput(BaseModel):
    id_mov: int | None = None
    id_item: int
    id_usuario: str | int
    tipo_movimiento: Literal["entrada", "salida", "ajuste"]
    fecha_movimiento: str = ""
    descripcion: str = ""
    cantidad: int = 1


class TicketAtencionInput(BaseModel):
    id_ticket: int | None = None
    id_cliente: int
    id_usuario: str | int
    tipo_ticket: str
    descripcion: str
    estado_ticket: str = "Abierto"
    fecha_emitido: str = ""
    fecha_cierre: str = ""


class CatalogoRutinaInput(BaseModel):
    id_rutina: int | None = None
    nombre_rutina: str
    zonas_musculares: str
    color: str = "Azul"


class HorarioInput(BaseModel):
    id_horario: int | None = None
    id_cliente: int
    id_rutina: int
    dia_semana: str
    hora_inicio: str
    hora_fin: str


class AsistenciaInput(BaseModel):
    id_asistencia: int | None = None
    id_cliente: str | int
    fecha: str = ""
    hora: str = ""


class CheckinAsistenciaInput(BaseModel):
    id_cliente: str | int
    id_usuario: str | int | None = None
    fecha: str = ""
    hora: str = ""
    servicio: Literal["fitness", "musculacion", "cardio", "baile"] = "fitness"


class CheckinAsistenciaDniInput(BaseModel):
    dni: str
    id_usuario: str | int | None = None
    fecha: str = ""
    hora: str = ""
    servicio: Literal["fitness", "musculacion", "cardio", "baile"] = "fitness"


class SummaryResponse(BaseModel):
    stats: dict[str, Any]
    flujos: dict[str, Any]
    alertas: list[dict[str, Any]]
