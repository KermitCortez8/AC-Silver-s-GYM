"""Tablas y relaciones necesarias para mantener instantáneas coherentes."""

REFRESH_TTL_SECONDS = 5.0

PAYMENT_COLUMNS = {'monto_pago', 'estado_pago', 'referencia_pago', 'fecha_pago', 'metodo_pago'}

STORE_PAYMENT_COLUMNS = {'estado_pago', 'referencia_pago'}

CORE_TABLES = {'planes_membresia': ('PLANES_MEMBRESIA', 'id_pm', 'id_PM'),
 'preregistros': ('PREREGISTROS_MEMBRESIA', 'id_preregistro', 'id_preregistro'),
 'promociones': ('PROMOCIONES', 'id_promocion', 'id_promocion'),
 'clientes': ('CLIENTES', 'id_cliente', 'id_cliente'),
 'membresia': ('MEMBRESIA', 'id_membresia', 'id_membresia'),
 'usuario': ('USUARIO', 'id_usuario', 'id_usuario'),
 'inventario': ('INVENTARIO', 'id_item', 'id_item'),
 'productos_tienda': ('TIENDA_PRODUCTOS', 'id_producto', 'id_producto'),
 'catalogo_rutina': ('CATALOGO_RUTINA', 'id_rutina', 'id_rutina'),
 'horario': ('HORARIO', 'id_horario', 'id_horario'),
 'horarios_servicio': ('HORARIOS_SERVICIO', 'id_horario_servicio', 'id_horario_servicio'),
 'matriculas_horario': ('MATRICULAS_HORARIO', 'id_matricula', 'id_matricula'),
 'rutina_progreso': ('RUTINA_PROGRESO', 'id_progreso', 'id_progreso'),
 'mov_inv': ('MOV_INV', 'id_mov', 'id_mov'),
 'tickets_atencion': ('TICKETS_ATENCION', 'id_ticket', 'id_ticket'),
 'asistencia': ('ASISTENCIA', 'id_asistencia', 'id_asistencia')}

SYNC_STATE_KEYS = tuple(CORE_TABLES.keys()) + ('pedidos_tienda',)

READ_STATE_KEYS = SYNC_STATE_KEYS + ('configuracion_gimnasio',)

RELATED_READS = (frozenset(('clientes', 'membresia')), frozenset(('inventario', 'productos_tienda')), frozenset(('horarios_servicio', 'matriculas_horario')))

def selected_resources(resources=None) -> set[str]:
    selected = set(READ_STATE_KEYS if resources is None else resources)
    if selected - set(READ_STATE_KEYS):
        raise ValueError("Recurso de lectura desconocido")
    for related in RELATED_READS:
        if selected & related:
            selected.update(related)
    return selected
