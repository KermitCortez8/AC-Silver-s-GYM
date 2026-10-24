-- Ejecutar después de 015 como propietario de las secuencias (Supabase SQL Editor).
-- Las RPC SECURITY INVOKER necesitan leer y avanzar las identidades al insertar.
-- Se limita el permiso a service_role y a las tablas admitidas por la transacción.
begin;

do $$
declare
  resource record;
  sequence_name text;
begin
  for resource in
    select * from (values
      ('USUARIO', 'id_usuario'),
      ('PLANES_MEMBRESIA', 'id_PM'),
      ('PROMOCIONES', 'id_promocion'),
      ('CLIENTES', 'id_cliente'),
      ('MEMBRESIA', 'id_membresia'),
      ('INVENTARIO', 'id_item'),
      ('TIENDA_PRODUCTOS', 'id_producto'),
      ('CATALOGO_RUTINA', 'id_rutina'),
      ('HORARIO', 'id_horario'),
      ('HORARIOS_SERVICIO', 'id_horario_servicio'),
      ('MATRICULAS_HORARIO', 'id_matricula'),
      ('RUTINA_PROGRESO', 'id_progreso'),
      ('MOV_INV', 'id_mov'),
      ('TICKETS_ATENCION', 'id_ticket'),
      ('ASISTENCIA', 'id_asistencia'),
      ('VENTAS', 'id_venta'),
      ('DETALLE_VENTA', 'id_detalle'),
      ('CONFIGURACION_GIMNASIO', 'id_config')
    ) as resources(table_name, primary_key)
  loop
    if to_regclass(format('public.%I', resource.table_name)) is null then
      continue;
    end if;
    sequence_name := pg_get_serial_sequence(
      format('public.%I', resource.table_name), resource.primary_key
    );
    if sequence_name is not null then
      execute format('grant usage, select, update on sequence %s to service_role', sequence_name);
    end if;
  end loop;
end;
$$;

commit;
