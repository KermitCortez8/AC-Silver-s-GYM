from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class UsuarioInput(BaseModel):
    id_usuario: str | int | None = None
    nombre: str = ""
    correo: str = ""
    telefono: str = ""
    dni: str = ""
    password: str = ""
    contrasena: str = ""
    rol: Literal["admin", "trainer", "staff"]


class ClienteInput(BaseModel):
    id_usuario: str | int | None = None
    nombre: str = ""
    correo: str = ""
    telefono: str = ""
    dni: str = ""
    password: str = ""
    contrasena: str = ""
    plan: Literal["MENSUAL", "3 MESES", "ANUAL"] = "MENSUAL"
    promocion: str = "SIN PROMOCION"
    estado: str = "ACTIVO"


class PlanMembresiaInput(BaseModel):
    id_pm: int | None = None
    nombre_plan: str
    duracion: str
    precio: int
    activo: bool = True


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


class RegistroPublicoClienteInput(BaseModel):
    nombre: str = ""
    correo: str = ""
    telefono: str = ""
    dni: str = ""
    password: str = ""
    contrasena: str = ""
    plan: Literal["MENSUAL", "3 MESES", "ANUAL"] = "MENSUAL"
    promocion: str = "SIN PROMOCION"
    metodo_pago: str = "pasarela"
    referencia_pago: str = ""
    google_email: str = ""
    google_name: str = ""


class PagoPublicoClienteInput(BaseModel):
    metodo_pago: str = "pasarela"
    referencia_pago: str = ""


class InventarioInput(BaseModel):
    id_item: int | None = None
    nombre_item: str
    tipo: str
    cantidad_stock: int
    estado: str = "Operativo"
    n_activo: int | None = None
    unidad_venta: str = "unidad"
    precio_venta: float | None = None
    stock_minimo: int = 1
    ubicacion: str = "Almacén"
    observaciones: str = ""


class ProductoTiendaInput(BaseModel):
    id_producto: Optional[int] = None
    id_item: Optional[int] = None
    nombre_producto: str
    descripcion: Optional[str] = ""
    categoria: Optional[str] = "General"
    unidad_venta: str = "unidad"
    precio_venta: float
    cantidad_stock: int = 0
    stock_minimo: Optional[int] = 5
    estado: Optional[str] = "Disponible"


class PedidoTiendaItemInput(BaseModel):
    id_producto: int
    cantidad: int = Field(default=1, ge=1)


class PedidoTiendaInput(BaseModel):
    id_cliente: int | None = None
    cliente_nombre: str = ""
    cliente_correo: str = ""
    cliente_dni: str = ""
    metodo_pago: str = "tarjeta"
    referencia_pago: str = ""
    items: list[PedidoTiendaItemInput] = Field(default_factory=list)


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
    capacidad_maxima: int = 1


class HorarioServicioInput(BaseModel):
    id_horario_servicio: int | None = None
    servicio: Literal["fitness", "musculacion", "cardio", "baile"]
    hora_inicio: str = "06:00"
    hora_fin: str = "07:00"
    codigo_dia: str = "LUN"
    dia: str = "lunes"
    dias: list[str] = Field(default_factory=list)
    cupos: int = 10
    activo: bool = True


class MatriculaHorarioInput(BaseModel):
    id_cliente: str | int | None = None
    dni: str = ""
    id_horario_servicio: int


class AsistenciaInput(BaseModel):
    id_asistencia: int | None = None
    id_cliente: str | int
    fecha: str = ""
    hora: str = ""
    servicio: Literal["fitness", "musculacion", "cardio", "baile"] = "fitness"
    id_usuario: str | int | None = None


class AsistenciaUpdateInput(BaseModel):
    id_cliente: str | int | None = None
    fecha: str | None = None
    hora: str | None = None
    servicio: Literal["fitness", "musculacion", "cardio", "baile"] | None = None
    id_usuario: str | int | None = None


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


class AsistenciaEntradaInput(BaseModel):
    id_cliente: str | int | None = None
    dni: str = ""
    id_matricula: int | None = None
    id_horario_servicio: int | None = None
    fecha: str | None = None
    hora_entrada: str | None = None
    id_usuario: str | int | None = None


class AsistenciaSalidaInput(BaseModel):
    id_asistencia: int
    hora_salida: str | None = None
    id_usuario: str | int | None = None


class ConfiguracionGimnasioInput(BaseModel):
    capacidad_total: int = Field(default=30, ge=1)
    capacidad_por_hora: int = Field(default=10, ge=1)


class SummaryResponse(BaseModel):
    stats: dict[str, Any]
    flujos: dict[str, Any]
    alertas: list[dict[str, Any]]
