-- Ejecutar después de 014. No utiliza compensaciones ni admite un fallback de escrituras REST.
-- Verifica la instantánea que leyó el backend y confirma todos los cambios o ninguno.
begin;

-- Marca de identidad creciente: borrar un registro no permite reutilizar su ID.
create table if not exists public.gym_identity_counters (
  table_name text primary key,
  last_id bigint not null check (last_id >= 0)
);
revoke all on public.gym_identity_counters from public, anon, authenticated;
grant select, insert, update on public.gym_identity_counters to service_role;

create or replace function public.gym_identity_floors(p_tables text[])
returns jsonb language plpgsql security invoker set search_path = pg_catalog, public as $$
declare
  allowed constant jsonb := '{"USUARIO":"id_usuario","PLANES_MEMBRESIA":"id_PM","PROMOCIONES":"id_promocion","CLIENTES":"id_cliente","MEMBRESIA":"id_membresia","INVENTARIO":"id_item","TIENDA_PRODUCTOS":"id_producto","CATALOGO_RUTINA":"id_rutina","HORARIO":"id_horario","HORARIOS_SERVICIO":"id_horario_servicio","MATRICULAS_HORARIO":"id_matricula","RUTINA_PROGRESO":"id_progreso","MOV_INV":"id_mov","TICKETS_ATENCION":"id_ticket","ASISTENCIA":"id_asistencia","VENTAS":"id_venta","DETALLE_VENTA":"id_detalle","CONFIGURACION_GIMNASIO":"id_config"}';
  name text; top_id bigint; counter_id bigint; sequence_id bigint; sequence_name text;
  result jsonb := '{}'::jsonb;
begin
  foreach name in array p_tables loop
    if not allowed ? name then raise exception 'Tabla de identidad no permitida' using errcode = '22023'; end if;
    execute format('select coalesce(max(%I), 0) from public.%I', allowed ->> name, name) into top_id;
    select last_id into counter_id from public.gym_identity_counters where table_name = name;
    sequence_name := pg_get_serial_sequence(format('public.%I', name), allowed ->> name);
    sequence_id := 0;
    if sequence_name is not null then
      execute format('select case when is_called then last_value else 0 end from %s', sequence_name) into sequence_id;
    end if;
    result := result || jsonb_build_object(name, greatest(top_id, coalesce(counter_id, 0), sequence_id));
  end loop;
  return result;
end; $$;
revoke all on function public.gym_identity_floors(text[]) from public, anon, authenticated;
grant execute on function public.gym_identity_floors(text[]) to service_role;

create or replace function public.commit_gym_transaction(p_expected jsonb, p_operations jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = pg_catalog, public
as $$
declare
  allowed constant jsonb := '{"USUARIO":"id_usuario","PLANES_MEMBRESIA":"id_PM","PROMOCIONES":"id_promocion","CLIENTES":"id_cliente","MEMBRESIA":"id_membresia","INVENTARIO":"id_item","TIENDA_PRODUCTOS":"id_producto","CATALOGO_RUTINA":"id_rutina","HORARIO":"id_horario","HORARIOS_SERVICIO":"id_horario_servicio","MATRICULAS_HORARIO":"id_matricula","RUTINA_PROGRESO":"id_progreso","MOV_INV":"id_mov","TICKETS_ATENCION":"id_ticket","ASISTENCIA":"id_asistencia","VENTAS":"id_venta","DETALLE_VENTA":"id_detalle","CONFIGURACION_GIMNASIO":"id_config"}';
  parent_order constant text[] := array['USUARIO','PLANES_MEMBRESIA','PROMOCIONES','CLIENTES','MEMBRESIA','INVENTARIO','TIENDA_PRODUCTOS','CATALOGO_RUTINA','HORARIO','HORARIOS_SERVICIO','MATRICULAS_HORARIO','RUTINA_PROGRESO','MOV_INV','TICKETS_ATENCION','ASISTENCIA','VENTAS','DETALLE_VENTA','CONFIGURACION_GIMNASIO'];
  table_name text;
  pk text;
  actual jsonb;
  expected jsonb;
  op jsonb;
  body jsonb;
  columns_list text;
  column_name text;
  initial_floors jsonb;
  explicit_id bigint;
  affected integer;
  sequence_name text;
  sequence_id bigint;
  outcome jsonb := '{}'::jsonb;
begin
  if jsonb_typeof(p_expected) is distinct from 'object'
     or jsonb_typeof(p_operations) is distinct from 'array'
     or p_expected = '{}'::jsonb then
    raise exception 'Instantánea y operaciones inválidas' using errcode = '22023';
  end if;

  -- El orden único de locks evita ciclos entre dos ejecuciones de esta función.
  -- Estos locks también excluyen escrituras de otras RPC o conexiones, no solo de Python.
  for table_name in select jsonb_object_keys(p_expected) order by 1 loop
    if not allowed ? table_name or jsonb_typeof(p_expected -> table_name) is distinct from 'array' then
      raise exception 'Tabla o instantánea no permitida' using errcode = '22023';
    end if;
    execute format('lock table public.%I in share row exclusive mode', table_name);
  end loop;

  for table_name in select jsonb_object_keys(p_expected) order by 1 loop
    execute format('select coalesce(jsonb_agg(to_jsonb(t) order by to_jsonb(t)::text), ''[]''::jsonb) from public.%I t', table_name)
      into actual;
    select coalesce(jsonb_agg(value order by value::text), '[]'::jsonb)
      into expected from jsonb_array_elements(p_expected -> table_name);
    if actual is distinct from expected then
      raise exception 'La instantánea cambió; recalcular la operación' using errcode = '40001';
    end if;
  end loop;

  select public.gym_identity_floors(array(select jsonb_object_keys(p_expected))) into initial_floors;

  -- Primero hijos al borrar; después padres al insertar. Las actualizaciones de
  -- membresía preceden a CLIENTES para que sus triggers observen el pago confirmado.
  for op in
    select value from jsonb_array_elements(p_operations)
    order by
      case value ->> 'action' when 'delete_details' then 0 when 'delete' then 1 when 'insert' then 2 when 'update' then 3 else 4 end,
      case when value ->> 'action' = 'delete' then -array_position(parent_order, value ->> 'table')
           when value ->> 'action' = 'update' and value ->> 'table' = 'MEMBRESIA' then -1
           else array_position(parent_order, value ->> 'table') end
  loop
    table_name := op ->> 'table';
    pk := allowed ->> table_name;
    if pk is null or op ->> 'pk' is distinct from pk or not p_expected ? table_name then
      raise exception 'Operación fuera de la instantánea autorizada' using errcode = '22023';
    end if;
    if op ->> 'action' = 'delete_details' then
      if table_name <> 'DETALLE_VENTA' or jsonb_typeof(op -> 'id') is distinct from 'number' then
        raise exception 'Borrado de detalles inválido' using errcode = '22023';
      end if;
      delete from public."DETALLE_VENTA" where id_venta = (op ->> 'id')::bigint;
    elsif op ->> 'action' = 'delete' then
      execute format('delete from public.%I t where to_jsonb(t) -> %L = $1', table_name, pk) using op -> 'id';
    elsif op ->> 'action' in ('insert', 'update') then
      body := op -> 'body';
      if jsonb_typeof(body) is distinct from 'object' or body = '{}'::jsonb then
        raise exception 'Registro inválido' using errcode = '22023';
      end if;
      if op ->> 'action' = 'update' and body -> pk is distinct from op -> 'id' then
        raise exception 'No se puede modificar la identidad del registro' using errcode = '22023';
      end if;
      for column_name in select jsonb_object_keys(body) loop
        if not exists (select 1 from pg_attribute a where a.attrelid = to_regclass(format('public.%I', table_name))
                       and a.attname = column_name and a.attnum > 0 and not a.attisdropped and a.attgenerated = '') then
          raise exception 'Columna desconocida en %.%; comprobar migración 014', table_name, column_name using errcode = '42703';
        end if;
      end loop;
      select string_agg(format('%I', key), ',' order by key) into columns_list
        from jsonb_object_keys(body) key where op ->> 'action' = 'insert' or key <> pk;
      if op ->> 'action' = 'insert' then
        if body ? pk then
          explicit_id := (body ->> pk)::bigint;
          if table_name <> 'CONFIGURACION_GIMNASIO' and explicit_id <= (initial_floors ->> table_name)::bigint then
            raise exception 'La identidad fue utilizada; recalcular la operación' using errcode = '40001';
          end if;
        end if;
        execute format('insert into public.%1$I (%2$s) overriding system value select %2$s from jsonb_populate_record(null::public.%1$I, $1)', table_name, columns_list) using body;
        if body ? pk then
          insert into public.gym_identity_counters as c (table_name, last_id) values (table_name, explicit_id)
            on conflict on constraint gym_identity_counters_pkey do update set last_id = greatest(c.last_id, excluded.last_id);
          sequence_name := pg_get_serial_sequence(format('public.%I', table_name), pk);
          if sequence_name is not null then
            execute format('select last_value from %s', sequence_name) into sequence_id;
            perform setval(sequence_name::regclass, greatest(sequence_id, explicit_id), true);
          end if;
        end if;
      elsif columns_list is not null then
        execute format('update public.%1$I t set (%2$s) = (select %2$s from jsonb_populate_record(null::public.%1$I, $1)) where to_jsonb(t) -> %3$L = $2', table_name, columns_list, pk) using body, op -> 'id';
        get diagnostics affected = row_count;
        if affected <> 1 then raise exception 'El registro cambió durante la operación' using errcode = '40001'; end if;
      end if;
    else
      raise exception 'Acción no permitida' using errcode = '22023';
    end if;
  end loop;

  -- Devuelve la instantánea real, incluyendo defaults y cambios de triggers.
  for table_name in select jsonb_object_keys(p_expected) order by 1 loop
    execute format('select coalesce(jsonb_agg(to_jsonb(t)), ''[]''::jsonb) from public.%I t', table_name) into actual;
    outcome := outcome || jsonb_build_object(table_name, actual);
  end loop;
  return jsonb_build_object('tables', outcome);
end;
$$;

revoke all on function public.commit_gym_transaction(jsonb, jsonb) from public;
revoke all on function public.commit_gym_transaction(jsonb, jsonb) from anon, authenticated;
grant execute on function public.commit_gym_transaction(jsonb, jsonb) to service_role;
notify pgrst, 'reload schema';
commit;
