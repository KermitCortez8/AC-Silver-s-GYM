"""Compatibilidad explícita del esquema; nunca descarta datos desconocidos."""
from infrastructure.http_transport import database_code
from application.errors import PersistenceUnavailable, SchemaNotReady

PRESERVED = {
    "USUARIO": {"codigo_usuario"},
    "PROMOCIONES": {"limite_cupos", "usos_actuales", "icono_etiqueta", "palabra_clave"},
    "MEMBRESIA": {"id_promocion"},
    "INVENTARIO": {"unidad_venta", "precio_venta", "stock_minimo", "ubicacion", "observaciones"},
    "TIENDA_PRODUCTOS": {"descripcion", "unidad_venta"},
}
MIGRATIONS = {"fecha_clase": "019_schedule_sessions.sql",
              "cliente_nombre": "025_delete_clients_preserve_sales.sql",
              "cliente_correo": "025_delete_clients_preserve_sales.sql",
              "cliente_dni": "025_delete_clients_preserve_sales.sql",
              "origen_registro": "009_admin_client_stripe.sql", "google_sub": "003_add_google_identity.sql",
              "ejercicios": "012_trainer_exercises.sql", "ejercicios_detalle": "012_trainer_exercises.sql",
              "archivado": "018_archivar_inventario_tienda.sql",
              "eliminado": "019_papelera_tienda.sql",
              "prefijo_activo": "026_inventario_unidades.sql",
              "id_unidad": "027_mov_inv_unidad_hora.sql",
              "hora_movimiento": "027_mov_inv_unidad_hora.sql",
              "sala": "030_sala_horario_servicio.sql",
              "medio_pago": "031_pagos_externos_registro.sql"}


def missing_column(error):
    return database_code(error) in {"PGRST204", "42703"}


def prepare_write(table, body, remote_columns, validate):
    body = dict(body)
    columns = remote_columns.get(table)
    # Estos dos nombres corresponden al mismo dato en instalaciones históricas.
    if table == "CLIENTES" and columns:
        for alias, other in (("Correo", "Email"), ("Email", "Correo")):
            if alias not in columns and other in columns:
                body.pop(alias, None)
    for field in ("origen_registro", "google_sub", "sala", "medio_pago"):
        if field not in body or (columns is not None and field in columns):
            continue
        if body[field] is None or body[field] == "":
            # Un registro anterior puede no tener este dato.
            body.pop(field)
            continue
        try:
            validate(table, {field})
        except RuntimeError as error:
            if not missing_column(error):
                raise
            raise SchemaNotReady(MIGRATIONS[field]) from error
        if columns is not None:
            columns.add(field)
    if columns is None:
        # Una tabla vacía no informa sus columnas; PostgREST valida el INSERT completo.
        return body
    unknown = body.keys() - columns
    if unknown:
        migration = "014_preserve_business_fields.sql" if unknown & PRESERVED.get(table, set()) else next(
            (MIGRATIONS[field] for field in unknown if field in MIGRATIONS), None)
        if migration:
            raise SchemaNotReady(migration)
        raise PersistenceUnavailable(f"Faltan columnas de {table}: {', '.join(sorted(unknown))}")
    return body
