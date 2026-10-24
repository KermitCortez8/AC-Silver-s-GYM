"""Recursos de negocio utilizados por consultas y unidades de trabajo."""
from enum import StrEnum


class Resource(StrEnum):
    USUARIO = 'usuario'
    CLIENTES = 'clientes'
    MEMBRESIA = 'membresia'
    PLANES_MEMBRESIA = 'planes_membresia'
    PROMOCIONES = 'promociones'
    ASISTENCIA = 'asistencia'
    HORARIOS_SERVICIO = 'horarios_servicio'
    MATRICULAS_HORARIO = 'matriculas_horario'
    INVENTARIO = 'inventario'
    PRODUCTOS_TIENDA = 'productos_tienda'
    MOV_INV = 'mov_inv'
    TICKETS_ATENCION = 'tickets_atencion'
    CATALOGO_RUTINA = 'catalogo_rutina'
    HORARIO = 'horario'
    RUTINA_PROGRESO = 'rutina_progreso'
    CONFIGURACION_GIMNASIO = 'configuracion_gimnasio'
    PEDIDOS_TIENDA = 'pedidos_tienda'
