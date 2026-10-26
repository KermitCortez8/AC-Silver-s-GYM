"""Datos declarados por las consultas de aplicación, independientes de las URLs."""

ACCOUNTS = ("usuario",)
CLIENTS = ("clientes", "membresia", "planes_membresia")
SCHEDULES = (*CLIENTS, "matriculas_horario", "horarios_servicio", "catalogo_rutina", "asistencia", "rutina_progreso")
INVENTORY = ("inventario", "productos_tienda")
ORDERS = (*INVENTORY, "pedidos_tienda")

READ_RESOURCES = {
    **dict.fromkeys(("get_usuario", "get_usuario_by_email", "usuarios", "usuarios_normalized", "authenticate_usuario_password"), ACCOUNTS),
    **dict.fromkeys(("clientes", "clientes_normalized", "get_cliente", "get_cliente_by_dni", "get_cliente_by_email", "authenticate_cliente_password"), CLIENTS),
    "get_account_by_google_sub": (*ACCOUNTS, *CLIENTS),
    **dict.fromkeys(("planes_membresia", "get_plan_membresia"), ("planes_membresia",)),
    **dict.fromkeys(("promociones", "get_promocion_vigente_para_plan", "promociones_vigentes_publicas"), ("promociones", "planes_membresia", "clientes", "membresia")),
    **dict.fromkeys(("membresias", "membresias_por_cliente"), CLIENTS),
    "asistencia": ("asistencia", "clientes"),
    **dict.fromkeys(("inventario", "get_item_inventario", "productos_tienda", "get_producto_tienda"), INVENTORY),
    "movimientos_inventario": ("mov_inv",),
    **dict.fromkeys(("pedidos_tienda", "get_pedido_tienda", "pedidos_pago_pendiente"), ORDERS),
    "minutos_desde_creacion": (),
    "tickets": ("tickets_atencion",),
    "configuracion_gimnasio": ("configuracion_gimnasio",),
    "summary": (*CLIENTS, *ORDERS, "asistencia", "mov_inv", "usuario", "configuracion_gimnasio", "matriculas_horario", "horarios_servicio"),
    "catalogo_rutina": ("catalogo_rutina",),
    "horarios": ("horario",),
    **dict.fromkeys(("horarios_servicio", "get_horario_servicio", "matriculas_horario", "get_matricula_horario", "trainer_rutinas_cliente", "trainer_overview"), SCHEDULES),
}
