-- Matrículas y cupos por fecha concreta; la programación continúa siendo semanal.
-- Precondiciones: esquema existente, 002_harden_schedule_enrollment.sql,
-- 006_schedule_email_notifications.sql y 018_attendance_schedule_exit_deadline.sql.
-- Aplicar antes del nuevo backend. No modifica ni elimina visitas históricas.
-- Recuperación: volver al código anterior y restaurar funciones/triggers de
-- 002/006/018, conservando fecha_clase y sus datos. No restaurar el índice antiguo
-- sin resolver matrículas del mismo cliente/horario en fechas distintas.
-- Verificación: test_schedule_sessions.py y test_schedule_sessions_postgres.py
-- en un PostgreSQL desechable explícito con base gym_test.
begin;

alter table public."MATRICULAS_HORARIO" add column if not exists fecha_clase date;

create or replace function public.schedule_session_date(p_registered text, p_day text)
returns date language plpgsql immutable set search_path = pg_catalog, public as $$
declare
  registered date;
  weekday integer := array_position(array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'], p_day);
begin
  if p_registered is null or left(p_registered,10) !~ '^\d{4}-\d{2}-\d{2}$' or weekday is null then return null; end if;
  registered := left(p_registered,10)::date;
  return registered + ((weekday - extract(isodow from registered)::integer + 7) % 7);
exception when invalid_datetime_format or datetime_field_overflow then return null;
end;
$$;

-- Una sola fecha histórica, derivada del alta, nunca de la semana de despliegue.
-- Las altas sin fecha fiable quedan sin sesión y no autorizan una nueva entrada.
-- La transacción ya mantiene el bloqueo de esquema; evita revalidar el backfill
-- como una matrícula nueva al volver a ejecutar esta migración.
drop trigger if exists validar_cupo_matricula_horario_trigger on public."MATRICULAS_HORARIO";
update public."MATRICULAS_HORARIO" m
set fecha_clase = public.schedule_session_date(m.fecha_matricula::text, h.dia)
from public."HORARIOS_SERVICIO" h
where h.id_horario_servicio = m.id_horario_servicio and m.fecha_clase is null;

drop index if exists public.matriculas_horario_cliente_horario_activa_unique;
create unique index if not exists matriculas_cliente_sesion_activa_unique
  on public."MATRICULAS_HORARIO" (id_cliente, id_horario_servicio, fecha_clase)
  where upper(trim(coalesce(estado, ''))) = 'ACTIVA';

create or replace function public.validar_cupo_matricula_horario()
returns trigger language plpgsql security definer set search_path = pg_catalog, public as $$
declare
  horario public."HORARIOS_SERVICIO"%rowtype;
  today date := (clock_timestamp() at time zone 'America/Lima')::date;
  excluded bigint;
begin
  if tg_op = 'UPDATE' and old.fecha_clase is not null and old.fecha_clase is distinct from new.fecha_clase then
    raise exception 'La fecha de clase de una matrícula no se puede cambiar. Cancela y reserva otra sesión.';
  end if;
  if upper(trim(coalesce(new.estado, ''))) <> 'ACTIVA' then return new; end if;
  if tg_op = 'UPDATE' then excluded := old.id_matricula; end if;
  -- Serializa reservas, cambios de día y capacidad entre todos los procesos.
  select * into horario from public."HORARIOS_SERVICIO"
    where id_horario_servicio = new.id_horario_servicio for update;
  if not found or not coalesce(horario.activo, false) then raise exception 'Horario no disponible'; end if;
  if new.fecha_clase is null and tg_op = 'INSERT' then
    new.fecha_clase := public.schedule_session_date(today::text, horario.dia);
  end if;
  if new.fecha_clase is null or new.fecha_clase < today then
    raise exception 'Selecciona una fecha de clase vigente.';
  end if;
  if horario.dia <> (array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[extract(isodow from new.fecha_clase)::integer] then
    raise exception 'La fecha de clase no corresponde al día del horario.';
  end if;
  if not exists (select 1 from public."MEMBRESIA" m where m.id_cliente = new.id_cliente
    and upper(trim(coalesce(m."Estado", ''))) in ('ACTIVA','ACTIVO')
    and m."Fecha_Inicio"::date <= today and m."Fecha_Fin"::date >= today
    and m."Fecha_Inicio"::date <= new.fecha_clase and m."Fecha_Fin"::date >= new.fecha_clase) then
    raise exception 'Cliente sin membresia activa para la fecha de clase';
  end if;
  if exists (select 1 from public."MATRICULAS_HORARIO" m
    where m.id_cliente = new.id_cliente and m.id_horario_servicio = new.id_horario_servicio
      and m.fecha_clase = new.fecha_clase and upper(trim(coalesce(m.estado, ''))) = 'ACTIVA'
      and (excluded is null or m.id_matricula <> excluded)) then
    raise exception 'El cliente ya esta matriculado en este horario para esa fecha';
  end if;
  if (select count(*) from public."MATRICULAS_HORARIO" m
    where m.id_horario_servicio = new.id_horario_servicio and m.fecha_clase = new.fecha_clase
      and upper(trim(coalesce(m.estado, ''))) = 'ACTIVA'
      and (excluded is null or m.id_matricula <> excluded)) >= horario.cupos then
    raise exception 'Horario sin cupos disponibles para esa fecha';
  end if;
  return new;
end;
$$;
drop trigger if exists validar_cupo_matricula_horario_trigger on public."MATRICULAS_HORARIO";
create trigger validar_cupo_matricula_horario_trigger
  before insert or update of id_cliente, id_horario_servicio, estado, fecha_clase
  on public."MATRICULAS_HORARIO" for each row execute function public.validar_cupo_matricula_horario();

create or replace function public.validar_capacidad_horario_servicio()
returns trigger language plpgsql security definer set search_path = pg_catalog, public as $$
declare
  used bigint;
begin
  select coalesce(max(amount), 0) into used from (
    select count(*) amount from public."MATRICULAS_HORARIO" m
    where m.id_horario_servicio = new.id_horario_servicio
      and upper(trim(coalesce(m.estado, ''))) = 'ACTIVA'
      and m.fecha_clase >= (clock_timestamp() at time zone 'America/Lima')::date
    group by m.fecha_clase
  ) counts;
  if new.cupos < used then raise exception 'No puedes reducir cupos por debajo de los matriculados'; end if;
  if old.dia is distinct from new.dia and used > 0 then
    raise exception 'No puedes cambiar el día de un horario con matrículas pendientes.';
  end if;
  return new;
end;
$$;
drop trigger if exists validar_capacidad_horario_servicio_trigger on public."HORARIOS_SERVICIO";
create trigger validar_capacidad_horario_servicio_trigger before update of cupos, dia
  on public."HORARIOS_SERVICIO" for each row execute function public.validar_capacidad_horario_servicio();

create or replace function public.matricular_cliente_sesion(
  p_id_cliente bigint, p_id_horario_servicio bigint, p_fecha_clase date
) returns jsonb language plpgsql security definer set search_path = pg_catalog, public as $$
declare
  created public."MATRICULAS_HORARIO"%rowtype;
begin
  insert into public."MATRICULAS_HORARIO" (id_cliente, id_horario_servicio, fecha_clase, fecha_matricula, estado)
  values (p_id_cliente, p_id_horario_servicio, p_fecha_clase,
    (clock_timestamp() at time zone 'America/Lima')::date, 'ACTIVA') returning * into created;
  return to_jsonb(created);
end;
$$;

create or replace function public.matricular_cliente_sesion_admin(
  p_id_cliente bigint, p_id_horario_servicio bigint, p_fecha_clase date, p_admin_id text
) returns jsonb language plpgsql security definer set search_path = pg_catalog, public as $$
declare
  created jsonb;
  schedule jsonb;
begin
  if length(trim(coalesce(p_admin_id, ''))) = 0 then raise exception 'Falta identificar al administrador'; end if;
  created := public.matricular_cliente_sesion(p_id_cliente, p_id_horario_servicio, p_fecha_clase);
  select to_jsonb(h) into schedule from public."HORARIOS_SERVICIO" h where h.id_horario_servicio = p_id_horario_servicio;
  insert into public.schedule_email_notifications (event_key, id_matricula, event_type, schedule_signature, registered_by)
  values ('enrollment/' || (created->>'id_matricula'), (created->>'id_matricula')::bigint,
    'enrollment', public.schedule_email_signature(schedule), p_admin_id);
  return created;
end;
$$;

-- Compatibilidad con clientes antiguos: también reservan una sola sesión.
create or replace function public.matricular_cliente_horario(p_id_cliente bigint, p_id_horario_servicio bigint)
returns jsonb language sql security definer set search_path = pg_catalog, public as $$
  select public.matricular_cliente_sesion(p_id_cliente, p_id_horario_servicio, null);
$$;
create or replace function public.matricular_cliente_horario_admin(p_id_cliente bigint, p_id_horario_servicio bigint, p_admin_id text)
returns jsonb language sql security definer set search_path = pg_catalog, public as $$
  select public.matricular_cliente_sesion_admin(p_id_cliente, p_id_horario_servicio, null, p_admin_id);
$$;

revoke all on function public.schedule_session_date(text,text) from public, anon, authenticated;
revoke all on function public.matricular_cliente_sesion(bigint,bigint,date) from public, anon, authenticated;
revoke all on function public.matricular_cliente_sesion_admin(bigint,bigint,date,text) from public, anon, authenticated;
grant execute on function public.matricular_cliente_sesion(bigint,bigint,date) to service_role;
grant execute on function public.matricular_cliente_sesion_admin(bigint,bigint,date,text) to service_role;

-- Mantiene aforo, reintentos, auditoría y salidas; valida también la sesión.
create or replace function public.guardar_asistencia(p_registro jsonb, p_version integer, p_evento jsonb)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  anterior public."ASISTENCIA"%rowtype;
  registro public."ASISTENCIA"%rowtype;
  matricula public."MATRICULAS_HORARIO"%rowtype;
  horario public."HORARIOS_SERVICIO"%rowtype;
  accion text := p_evento->>'accion';
  ahora timestamp := date_trunc('second', clock_timestamp() at time zone 'America/Lima');
  entrada timestamp;
  salida timestamp;
  capacidad integer;
  evento jsonb;
begin
  if accion not in ('entrada', 'salida', 'correccion', 'anulacion')
     or coalesce(p_evento->>'actor_id', '') = '' then
    raise exception 'Operación de asistencia inválida';
  end if;
  -- Serializa escrituras, incluso desde distintos procesos del backend.
  -- También protege aforo, IDs explícitos y la regla de una sola entrada abierta.
  perform pg_advisory_xact_lock(51005, 1);
  ahora := date_trunc('second', clock_timestamp() at time zone 'America/Lima');
  registro := jsonb_populate_record(null::public."ASISTENCIA", p_registro);

  if p_version is null then
    if accion <> 'entrada' then raise exception 'Operación inválida'; end if;
    if registro.servicio = 'gimnasio' then
      if coalesce(p_evento->>'request_id', '') = '' then
        raise exception 'La entrada general requiere un identificador de solicitud.';
      end if;
      perform (p_evento->>'request_id')::uuid;
      -- El mismo intento devuelve su primera visita, incluso después de cerrarla.
      select * into anterior from public."ASISTENCIA"
        where id_cliente = registro.id_cliente and servicio = 'gimnasio'
          and auditoria @> jsonb_build_array(jsonb_build_object('request_id', p_evento->>'request_id'))
        order by id_asistencia desc limit 1;
    else
      select * into anterior from public."ASISTENCIA"
        where id_cliente = registro.id_cliente and id_matricula = registro.id_matricula
          and "Fecha"::date = ahora::date and not anulado
        order by id_asistencia desc limit 1;
    end if;
    if found then return to_jsonb(anterior); end if;

    perform 1 from public."CLIENTES" where id_cliente = registro.id_cliente and "Estado" is true for share;
    if not found then raise exception 'La cuenta debe estar activada por el administrador.'; end if;
    perform 1 from public."MEMBRESIA"
      where id_membresia = registro.id_membresia and id_cliente = registro.id_cliente
        and upper("Estado") in ('ACTIVA', 'ACTIVO') and upper(estado_pago) = 'PAGADO'
        and "Fecha_Inicio"::date <= ahora::date and "Fecha_Fin"::date >= ahora::date for share;
    if not found then raise exception 'El cliente necesita una membresía activa, pagada y vigente.'; end if;
    if registro.servicio = 'gimnasio' then
      registro.id_matricula := null;
      registro.id_horario_servicio := null;
      registro.limite_salida := null;
    else
      select * into matricula from public."MATRICULAS_HORARIO"
        where id_matricula = registro.id_matricula and id_cliente = registro.id_cliente and estado = 'ACTIVA' for share;
      if not found then raise exception 'La matrícula no está activa.'; end if;
      if matricula.fecha_clase is distinct from ahora::date then
        raise exception 'La matrícula no corresponde a la fecha de esta clase.';
      end if;
      select * into horario from public."HORARIOS_SERVICIO"
        where id_horario_servicio = matricula.id_horario_servicio and activo for share;
      if not found then raise exception 'El horario no está disponible.'; end if;
      if horario.dia <> (array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[extract(isodow from ahora)::integer]
         or ahora::time < horario.hora_inicio::time then
        raise exception 'La entrada solo se puede registrar durante el horario matriculado (hora de Perú).';
      end if;
      if ahora::time >= horario.hora_fin::time then
        raise exception 'La hora de esta clase ya pasó. No se puede registrar la asistencia.';
      end if;
      registro.limite_salida := ((ahora::date + horario.hora_fin::time + interval '1 hour') at time zone 'America/Lima');
      registro.id_horario_servicio := horario.id_horario_servicio;
      registro.servicio := horario.servicio;
    end if;
    if exists(select 1 from public."ASISTENCIA"
      where id_cliente = registro.id_cliente and not anulado and coalesce(hora_salida::text, '') = '') then
      raise exception 'El cliente tiene una entrada sin salida. Registra su salida primero.';
    end if;
    if to_regclass('public."CONFIGURACION_GIMNASIO"') is not null then
      select capacidad_total into capacidad from public."CONFIGURACION_GIMNASIO" order by id_config limit 1;
    end if;
    if (select count(distinct id_cliente) from public."ASISTENCIA" where not anulado and coalesce(hora_salida::text, '') = '') >= coalesce(capacidad, 30) then
      raise exception 'El gimnasio alcanzó su aforo. Registra una salida antes de otra entrada.';
    end if;
    registro."Fecha" := ahora::date;
    registro."Hora" := ahora::time;
    registro.hora_entrada := ahora::time;
    registro.hora_salida := null;
    registro.fecha_salida := null;
    registro.anulado := false;
    registro."Validación" := true;
    select coalesce(max(id_asistencia), 0) + 1 into registro.id_asistencia from public."ASISTENCIA";
    registro.auditoria := '[]'::jsonb;
    registro.version := 1;
  else
    select * into anterior from public."ASISTENCIA" where id_asistencia = registro.id_asistencia for update;
    if not found then raise exception 'Asistencia no encontrada.'; end if;
    if anterior.anulado then raise exception 'La asistencia ya está anulada.'; end if;
    -- Un reintento de salida nunca reemplaza la primera hora guardada.
    if accion = 'salida' and coalesce(anterior.hora_salida::text, '') <> '' then return to_jsonb(anterior); end if;
    if anterior.version <> p_version then
      raise exception 'El registro cambió. Actualiza el historial e inténtalo de nuevo.';
    end if;
    if accion in ('correccion', 'anulacion') and length(trim(coalesce(p_evento->>'motivo', ''))) < 5 then
      raise exception 'Escribe un motivo de al menos 5 caracteres.';
    end if;
    -- Las modificaciones conservan identidad, membresía, matrícula y servicio.
    registro.id_cliente := anterior.id_cliente;
    registro.id_membresia := anterior.id_membresia;
    registro.id_matricula := anterior.id_matricula;
    registro.id_horario_servicio := anterior.id_horario_servicio;
    registro.servicio := anterior.servicio;
    registro.id_usuario_registra := anterior.id_usuario_registra;
    registro.limite_salida := anterior.limite_salida;
    if accion = 'salida' then
      registro := anterior;
      registro.hora_entrada := coalesce(nullif(anterior.hora_entrada::text, ''), anterior."Hora"::text)::time;
      registro.hora_salida := ahora::time;
      registro.fecha_salida := ahora::date;
    elsif accion = 'anulacion' then
      registro := anterior;
      registro.anulado := true;
    end if;
    registro.auditoria := anterior.auditoria;
    registro.version := anterior.version + 1;
  end if;

  if not registro.anulado then
    entrada := registro."Fecha"::date + coalesce(nullif(registro.hora_entrada::text, ''), registro."Hora"::text)::time;
    salida := coalesce(registro.fecha_salida, registro."Fecha")::date + nullif(registro.hora_salida::text, '')::time;
    if entrada is null or entrada > ahora or salida > ahora or salida < entrada then
      raise exception 'Revisa las horas: la salida debe ser posterior a la entrada y no puede haber fechas futuras.';
    end if;
    if exists(select 1 from public."ASISTENCIA" a where a.id_cliente = registro.id_cliente
      and a.id_asistencia <> registro.id_asistencia and not a.anulado and (
        (a.id_matricula = registro.id_matricula and a."Fecha" = registro."Fecha") or
        (coalesce(a.hora_salida::text, '') = '' and coalesce(registro.hora_salida::text, '') = '')
      )) then raise exception 'El cliente ya tiene una asistencia para ese horario y día, o una entrada sin salida.'; end if;
    registro."Hora" := registro.hora_entrada;
  end if;
  registro.salida_tardia := coalesce((salida at time zone 'America/Lima') > registro.limite_salida, false);
  evento := p_evento || jsonb_build_object('fecha', to_char(ahora, 'YYYY-MM-DD"T"HH24:MI:SS') || '-05:00',
    'antes', case when p_version is null then null else to_jsonb(anterior) - 'auditoria' end,
    'despues', to_jsonb(registro) - 'auditoria');
  registro.auditoria := coalesce(registro.auditoria, '[]'::jsonb) || jsonb_build_array(evento);

  if p_version is null then
    insert into public."ASISTENCIA" (id_asistencia, id_cliente, id_membresia, "Fecha", "Hora", "Validación", servicio,
      id_usuario_registra, id_matricula, id_horario_servicio, hora_entrada, hora_salida, fecha_salida, anulado, auditoria, version, limite_salida, salida_tardia)
    overriding system value
    values (registro.id_asistencia, registro.id_cliente, registro.id_membresia, registro."Fecha", registro."Hora", registro."Validación", registro.servicio,
      registro.id_usuario_registra, registro.id_matricula, registro.id_horario_servicio, registro.hora_entrada, registro.hora_salida,
      registro.fecha_salida, registro.anulado, registro.auditoria, registro.version, registro.limite_salida, registro.salida_tardia)
    returning * into registro;
  else
    update public."ASISTENCIA" set "Fecha" = registro."Fecha", "Hora" = registro."Hora", hora_entrada = registro.hora_entrada,
      hora_salida = registro.hora_salida, fecha_salida = registro.fecha_salida, anulado = registro.anulado,
      auditoria = registro.auditoria, version = registro.version,
      limite_salida = registro.limite_salida, salida_tardia = registro.salida_tardia
      where id_asistencia = registro.id_asistencia returning * into registro;
  end if;
  return to_jsonb(registro);
end;
$$;

revoke all on function public.guardar_asistencia(jsonb, integer, jsonb) from public, anon, authenticated;
grant execute on function public.guardar_asistencia(jsonb, integer, jsonb) to service_role;
notify pgrst, 'reload schema';

-- Recordatorios limitados a la fecha reservada.
create or replace function public.enqueue_due_schedule_reminders(p_now timestamptz default now())
returns integer language plpgsql security definer set search_path = pg_catalog, public as $$
declare
  added integer;
begin
  -- Descarta en lote recordatorios vencidos para que no retrasen los nuevos.
  update public.schedule_email_notifications
  set status = 'cancelled', claim_token = null, locked_until = null, last_error = 'La clase ya comenzó.'
  where event_type = 'reminder' and class_start <= p_now
    and (status = 'pending' or (status = 'processing' and locked_until < p_now));
  insert into public.schedule_email_notifications as job
    (event_key, id_matricula, event_type, class_start, schedule_signature, available_at)
  select 'class/' || m.id_matricula || '/' || to_char(occurrence.starts at time zone 'UTC', 'YYYYMMDDHH24MISS'),
    m.id_matricula, 'reminder', occurrence.starts, public.schedule_email_signature(to_jsonb(s)),
    occurrence.starts - interval '1 hour'
  from public."MATRICULAS_HORARIO" m
  join public."HORARIOS_SERVICIO" s on s.id_horario_servicio = m.id_horario_servicio
  join public."CLIENTES" c on c.id_cliente = m.id_cliente
  cross join generate_series(0, 1) as day_offset(value)
  cross join lateral (
    select ((p_now at time zone 'America/Lima')::date + day_offset.value + s.hora_inicio::time)
      at time zone 'America/Lima' as starts
  ) occurrence
  where m.fecha_clase = (occurrence.starts at time zone 'America/Lima')::date
    and m.estado = 'ACTIVA' and s.activo and c."Estado" is true
    and s.dia = (array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[
      extract(isodow from occurrence.starts at time zone 'America/Lima')::integer]
    and occurrence.starts > p_now and occurrence.starts <= p_now + interval '1 hour'
    and m.email_registered_at <= occurrence.starts - interval '1 hour'
    and exists (
      select 1 from public."MEMBRESIA" membership
      where membership.id_cliente = m.id_cliente and upper(membership."Estado") in ('ACTIVA', 'ACTIVO')
        and upper(membership.estado_pago) = 'PAGADO'
        and membership."Fecha_Inicio"::date <= (occurrence.starts at time zone 'America/Lima')::date
        and membership."Fecha_Fin"::date >= (occurrence.starts at time zone 'America/Lima')::date
    )
  on conflict (event_key) do update
    set schedule_signature = excluded.schedule_signature, status = 'pending',
        available_at = excluded.available_at, claim_token = null, locked_until = null, last_error = null
    where job.status = 'cancelled' or (job.status = 'pending' and job.schedule_signature <> excluded.schedule_signature);
  get diagnostics added = row_count;
  return added;
end;
$$;

create or replace function public.schedule_email_delivery_context(p_event_key text, p_claim_token text)
returns jsonb language plpgsql security definer set search_path = pg_catalog, public as $$
declare
  job public.schedule_email_notifications%rowtype;
  enrollment public."MATRICULAS_HORARIO"%rowtype;
  schedule public."HORARIOS_SERVICIO"%rowtype;
  client jsonb;
  local_start timestamp;
begin
  select * into job from public.schedule_email_notifications
    where event_key = p_event_key and claim_token = p_claim_token
      and status = 'processing' and locked_until > now();
  if not found then return null; end if;
  select * into enrollment from public."MATRICULAS_HORARIO"
    where id_matricula = job.id_matricula and estado = 'ACTIVA';
  if not found then return null; end if;
  select * into schedule from public."HORARIOS_SERVICIO"
    where id_horario_servicio = enrollment.id_horario_servicio and activo;
  if not found or public.schedule_email_signature(to_jsonb(schedule)) <> job.schedule_signature then return null; end if;
  select to_jsonb(c) into client from public."CLIENTES" c where id_cliente = enrollment.id_cliente;
  if client is null then return null; end if;
  if job.event_type = 'reminder' then
    local_start := job.class_start at time zone 'America/Lima';
    if enrollment.fecha_clase is distinct from local_start::date
      or job.class_start <= now() or job.class_start > now() + interval '1 hour'
      or (client->>'Estado')::boolean is not true
      or local_start::time <> schedule.hora_inicio::time
      or schedule.dia <> (array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[extract(isodow from local_start)::integer]
      or not exists (
        select 1 from public."MEMBRESIA" membership where membership.id_cliente = enrollment.id_cliente
          and upper(membership."Estado") in ('ACTIVA', 'ACTIVO') and upper(membership.estado_pago) = 'PAGADO'
          and membership."Fecha_Inicio"::date <= local_start::date and membership."Fecha_Fin"::date >= local_start::date
      ) then return null; end if;
  end if;
  return jsonb_build_object(
    'nombre', trim(concat_ws(' ', client->>'Nombres', client->>'Apellidos')),
    'correo', coalesce(nullif(trim(client->>'Correo'), ''), nullif(trim(client->>'Email'), '')),
    'servicio', schedule.servicio, 'dia', schedule.dia,
    'hora_inicio', schedule.hora_inicio, 'hora_fin', schedule.hora_fin,
    'fecha_clase', enrollment.fecha_clase, 'class_start', job.class_start, 'event_type', job.event_type
  );
end;
$$;


commit;
