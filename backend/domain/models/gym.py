# Módulo: gym.
# Define los esquemas de clientes, membresías y operaciones del gimnasio.
# Valida tipos, campos obligatorios y valores permitidos.
# Sirve como contrato entre las rutas y los servicios.
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from domain.validation import required_text, email_address, nonnegative, civil_date, clock_time, date_range, time_range


class ValidatedInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    @field_validator("nombre", "nombre_plan", "nombre_item", "nombre_producto", "nombre_rutina", "tipo", "duracion", check_fields=False)
    @classmethod
    def nonempty_name(cls, value):
        return required_text(value)

    @field_validator("correo", check_fields=False)
    @classmethod
    def valid_email(cls, value):
        return email_address(value)

    @field_validator("precio", "precio_venta", "stock_minimo", "cantidad_stock", "valor_descuento", check_fields=False)
    @classmethod
    def valid_nonnegative(cls, value):
        return nonnegative(value) if value is not None else value

    @field_validator("fecha_inicio", "fecha_fin", "fecha", "fecha_movimiento", "fecha_emitido", "fecha_cierre", check_fields=False)
    @classmethod
    def valid_date(cls, value, info):
        if not value and cls.model_fields[info.field_name].is_required():
            raise ValueError("La fecha es obligatoria")
        return civil_date(value) if value else value

    @field_validator("hora", "hora_inicio", "hora_fin", "hora_entrada", "hora_salida", check_fields=False)
    @classmethod
    def valid_time(cls, value, info):
        if not value and cls.model_fields[info.field_name].is_required():
            raise ValueError("La hora es obligatoria")
        return clock_time(value) if value else value

    @model_validator(mode="after")
    def valid_ranges(self):
        date_range(getattr(self, "fecha_inicio", None), getattr(self, "fecha_fin", None))
        start, end = getattr(self, "hora_inicio", None), getattr(self, "hora_fin", None)
        time_range(start, end)
        if getattr(self, "tipo_descuento", None) == "porcentaje" and self.valor_descuento > 100:
            raise ValueError("El porcentaje no puede ser mayor a 100")
        return self


class HorarioPublico(BaseModel):
    id_horario_servicio: int
    servicio: str
    dia: str
    hora_inicio: str
    hora_fin: str
    rutina_nombre: str = ""
    entrenador: str = ""
    cupos: int
    cupos_usados: int
    cupos_disponibles: int


class UsuarioInput(ValidatedInput):
    id_usuario: str | int | None = None
    nombre: str
    correo: str
    telefono: str = ""
    dni: str = ""
    password: str = ""
    contrasena: str = ""
    rol: Literal["admin", "trainer", "staff"]


class ClienteInput(ValidatedInput):
    id_usuario: str | int | None = None
    nombre: str
    correo: str
    telefono: str = ""
    dni: str = ""
    password: str = ""
    contrasena: str = ""
    plan: Literal["MENSUAL", "3 MESES", "ANUAL"] = "MENSUAL"
    promocion: str = "SIN PROMOCION"
    estado: str = "ACTIVO"


class PlanMembresiaInput(ValidatedInput):
    id_pm: int | None = None
    nombre_plan: str
    duracion: str
    precio: int = Field(ge=0)
    descripcion: str = ""
    beneficios: str = ""
    activo: bool = True


class PromocionInput(ValidatedInput):
    id_promocion: int | None = None
    nombre: str
    descripcion: str = ""
    tipo_descuento: Literal["porcentaje", "monto"] = "porcentaje"
    valor_descuento: float = Field(default=0, ge=0)
    fecha_inicio: str = ""
    fecha_fin: str = ""
    icono_etiqueta: str = "🏷️"
    palabra_clave: str = ""
    activo: bool = True
    planes_aplicables: list[int] = Field(default_factory=list)
    limite_cupos: int | None = Field(default=None, ge=1)
    usos_actuales: int = Field(default=0, ge=0)



class PedidoTiendaUpdateInput(ValidatedInput):
    estado_pedido: Literal["PENDIENTE", "CONFIRMADO", "ENTREGADO", "CANCELADO"]
    observacion_admin: str = ""


class MembresiaInput(ValidatedInput):
    id_membresia: int | None = None
    fecha_inicio: str
    fecha_fin: str
    estado: Literal["ACTIVO", "VENCIDA", "EN_TRAMITE"] = "EN_TRAMITE"
    id_cliente: int
    id_pm: int
    id_promocion: int | None = None


class RegistrarClienteMembresiaInput(ValidatedInput):
    cliente: ClienteInput
    id_pm: int
    fecha_inicio: str
    fecha_fin: str
    id_promocion: int | None = None


class RegistroAdminClienteInput(ClienteInput):
    id_promocion: int | None = Field(default=None, gt=0)
    pagar_con_stripe: bool = False


class RegistroPublicoClienteInput(ValidatedInput):
    nombre: str
    correo: str
    telefono: str = ""
    dni: str = ""
    password: str = ""
    contrasena: str = ""
    plan: Literal["MENSUAL", "3 MESES", "ANUAL"] = "MENSUAL"
    promocion: str = "SIN PROMOCION"
    google_credential: str = ""


class PagoPublicoClienteInput(ValidatedInput):
    metodo_pago: str = "pasarela"
    referencia_pago: str = ""


class InventarioInput(ValidatedInput):
    id_item: int | None = None
    nombre_item: str
    tipo: str
    cantidad_stock: int = Field(ge=0)
    estado: str = "Operativo"
    n_activo: int | None = None
    unidad_venta: str = "unidad"
    precio_venta: float | None = None
    stock_minimo: int = 1
    ubicacion: str = "Almacén"
    observaciones: str = ""


class ProductoTiendaInput(ValidatedInput):
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
    imagen_url: Optional[str] = ""


class PedidoTiendaItemInput(ValidatedInput):
    id_producto: int
    cantidad: int = Field(default=1, ge=1)


class PedidoTiendaInput(ValidatedInput):
    id_cliente: int | None = None
    cliente_nombre: str = ""
    cliente_correo: str = ""
    cliente_dni: str = ""
    metodo_pago: str = "tarjeta"
    referencia_pago: str = ""
    items: list[PedidoTiendaItemInput] = Field(default_factory=list)

class PedidoTiendaCheckoutInput(ValidatedInput):
    # Los datos del cliente son solo informativos: el id_cliente siempre sale del token de sesión.
    cliente_nombre: str = ""
    cliente_correo: str = ""
    cliente_dni: str = ""
    items: list[PedidoTiendaItemInput] = Field(min_length=1)


class MovimientoInventarioInput(ValidatedInput):
    id_mov: int | None = None
    id_item: int
    id_usuario: str | int
    tipo_movimiento: Literal["entrada", "salida", "ajuste"]
    fecha_movimiento: str = ""
    descripcion: str = ""
    cantidad: int = Field(default=1, ge=1)
    # Solo para salidas: "TIENDA" repone el stock del producto enlazado.
    destino: str | None = None


class MovimientoInventarioUpdateInput(ValidatedInput):
    id_item: int | None = None
    tipo_movimiento: Literal["entrada", "salida", "ajuste"] | None = None
    fecha_movimiento: str | None = None
    descripcion: str | None = None
    cantidad: int | None = Field(default=None, ge=1)
    # "TIENDA" para una reposición; "" quita el destino.
    destino: str | None = None


class TicketAtencionInput(ValidatedInput):
    id_ticket: int | None = None
    id_cliente: int
    id_usuario: str | int
    tipo_ticket: str
    descripcion: str
    estado_ticket: str = "Abierto"
    fecha_emitido: str = ""
    fecha_cierre: str = ""


class EjercicioInput(ValidatedInput):
    id_ejercicio: int | str | None = None
    nombre_ejercicio: str = ""
    series: int = Field(default=3, ge=1)
    repeticiones: str = "10-12"
    descanso_segundos: int = Field(default=60, ge=0)
    peso_sugerido_kg: float | None = None
    grupo_muscular: str = ""
    notas: str = ""


class CatalogoRutinaInput(ValidatedInput):
    id_rutina: int | None = None
    servicio: Literal["fitness", "musculacion", "cardio", "baile"] = "fitness"
    nombre_rutina: str
    zonas_musculares: str
    color: str = "Azul"
    ejercicios: list[EjercicioInput] = Field(default_factory=list)


class HorarioInput(ValidatedInput):
    id_horario: int | None = None
    id_cliente: int
    id_rutina: int
    dia_semana: str
    hora_inicio: str
    hora_fin: str
    capacidad_maxima: int = Field(default=1, ge=1)


class HorarioServicioInput(ValidatedInput):
    id_horario_servicio: int | None = None
    servicio: Literal["fitness", "musculacion", "cardio", "baile"]
    id_rutina: int
    hora_inicio: str = "06:00"
    hora_fin: str = "07:00"
    codigo_dia: str = "LUN"
    dia: str = "lunes"
    dias: list[str] = Field(default_factory=list)
    cupos: int = Field(default=10, ge=1)
    activo: bool = True


class MatriculaHorarioInput(ValidatedInput):
    id_cliente: str | int | None = None
    dni: str = ""
    id_horario_servicio: int


class MatriculaRutinaInput(ValidatedInput):
    id_rutina: int


class EjercicioProgresoInput(ValidatedInput):
    id_ejercicio: int | str | None = None
    nombre_ejercicio: str = ""
    completado: bool = True
    series_completadas: int = Field(default=3, ge=0)
    repeticiones_logradas: str = ""
    peso_utilizado_kg: float | None = None
    observaciones: str = ""


class RutinaProgresoInput(ValidatedInput):
    fecha: str = ""
    estado: str = "REALIZADO"
    observacion: str = ""
    id_usuario: str | int | None = None
    ejercicios_detalle: list[EjercicioProgresoInput] = Field(default_factory=list)



class AsistenciaInput(ValidatedInput):
    id_asistencia: int | None = None
    id_cliente: str | int
    fecha: str = ""
    hora: str = ""
    servicio: Literal["fitness", "musculacion", "cardio", "baile"] = "fitness"
    id_usuario: str | int | None = None


class AsistenciaUpdateInput(ValidatedInput):
    id_cliente: str | int | None = None
    fecha: str | None = None
    hora: str | None = None
    servicio: Literal["fitness", "musculacion", "cardio", "baile"] | None = None
    id_usuario: str | int | None = None


class CheckinAsistenciaInput(ValidatedInput):
    id_cliente: str | int
    id_usuario: str | int | None = None
    fecha: str = ""
    hora: str = ""
    servicio: Literal["fitness", "musculacion", "cardio", "baile"] = "fitness"


class CheckinAsistenciaDniInput(ValidatedInput):
    dni: str
    id_usuario: str | int | None = None
    fecha: str = ""
    hora: str = ""
    servicio: Literal["fitness", "musculacion", "cardio", "baile"] = "fitness"


class AsistenciaEntradaInput(ValidatedInput):
    id_cliente: str | int | None = None
    dni: str = ""
    id_matricula: int | None = None
    id_horario_servicio: int | None = None
    fecha: str | None = None
    hora_entrada: str | None = None
    id_usuario: str | int | None = None


class AsistenciaSalidaInput(ValidatedInput):
    id_asistencia: int
    hora_salida: str | None = None
    id_usuario: str | int | None = None


class ConfiguracionGimnasioInput(ValidatedInput):
    capacidad_total: int = Field(default=30, ge=1)
    capacidad_por_hora: int = Field(default=10, ge=1)


class SummaryResponse(BaseModel):
    stats: dict[str, Any]
    flujos: dict[str, Any]
    alertas: list[dict[str, Any]]
