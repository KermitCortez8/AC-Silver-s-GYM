-- 018_attendance_schedule_exit_deadline.sql
-- Precondiciones: esquema existente y migraciones 005_harden_attendance.sql y
-- 013_general_attendance.sql; fechas civiles y horas válidas en ASISTENCIA.
-- Ejecutar después de 013, antes del backend que usa limite_salida/salida_tardia.
-- 014–017 no son dependencias de esta migración.
-- Recuperación: restaurar guardar_asistencia desde 013; conservar estas columnas
-- y sus datos. El backend anterior ignora los campos adicionales. No borrar visitas.
-- Verificación: tests/test_schedule_attendance.py y test_attendance_deadline_postgres.py
-- sobre un PostgreSQL desechable (GYM_TEST_POSTGRES_CONTAINER); nunca datos compartidos.
begin;

alter table public."ASISTENCIA"
  add column if not exists limite_salida timestamptz,
  add column if not exists salida_tardia boolean not null default false;

-- Solo visitas aún abiertas: se toma el horario vigente en el momento de migrar.
-- Las visitas cerradas históricas conservan su clasificación anterior.
update public."ASISTENCIA" a
set limite_salida = ((a."Fecha"::date + h.hora_fin::time + interval '1 hour') at time zone 'America/Lima')
from public."HORARIOS_SERVICIO" h
where a.id_horario_servicio = h.id_horario_servicio
  and a.servicio is distinct from 'gimnasio'
  and a.limite_salida is null and not coalesce(a.anulado, false)
  and coalesce(a.hora_salida::text, '') = '';

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
commit;
