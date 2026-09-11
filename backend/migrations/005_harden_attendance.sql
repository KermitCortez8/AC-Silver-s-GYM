-- Supabase > SQL Editor, después de las migraciones 001–004.
-- Conserva los registros históricos. Las anulaciones son lógicas y auditadas.
begin;

alter table public."ASISTENCIA"
  add column if not exists id_matricula bigint,
  add column if not exists id_horario_servicio bigint,
  add column if not exists id_usuario_registra bigint,
  add column if not exists servicio text default 'fitness',
  add column if not exists hora_entrada time,
  add column if not exists hora_salida time,
  add column if not exists fecha_salida date,
  add column if not exists anulado boolean not null default false,
  add column if not exists auditoria jsonb not null default '[]'::jsonb,
  add column if not exists version integer not null default 0;

create index if not exists asistencia_cliente_fecha_idx
  on public."ASISTENCIA" (id_cliente, "Fecha" desc);
create index if not exists asistencia_matricula_fecha_idx
  on public."ASISTENCIA" (id_matricula, "Fecha") where not anulado;

-- Las cuentas del navegador no acceden directamente a las asistencias.
-- La API verifica la sesión propia y el rol antes de usar service_role.
alter table public."ASISTENCIA" enable row level security;
revoke all on table public."ASISTENCIA" from anon, authenticated;
grant all on table public."ASISTENCIA" to service_role;

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
  registro := jsonb_populate_record(null::public."ASISTENCIA", p_registro);

  if p_version is null then
    if accion <> 'entrada' then raise exception 'Operación inválida'; end if;
    select * into anterior from public."ASISTENCIA"
      where id_cliente = registro.id_cliente and id_matricula = registro.id_matricula
        and "Fecha" = ahora::date and not anulado
      order by id_asistencia desc limit 1;
    if found then return to_jsonb(anterior); end if;

    perform 1 from public."CLIENTES" where id_cliente = registro.id_cliente and "Estado" is true for share;
    if not found then raise exception 'La cuenta debe estar activada por el administrador.'; end if;
    perform 1 from public."MEMBRESIA"
      where id_membresia = registro.id_membresia and id_cliente = registro.id_cliente
        and upper("Estado") in ('ACTIVA', 'ACTIVO') and upper(estado_pago) = 'PAGADO'
        and "Fecha_Inicio" <= ahora::date and "Fecha_Fin" >= ahora::date for share;
    if not found then raise exception 'El cliente necesita una membresía activa, pagada y vigente.'; end if;
    select * into matricula from public."MATRICULAS_HORARIO"
      where id_matricula = registro.id_matricula and id_cliente = registro.id_cliente and estado = 'ACTIVA' for share;
    if not found then raise exception 'La matrícula no está activa.'; end if;
    select * into horario from public."HORARIOS_SERVICIO"
      where id_horario_servicio = matricula.id_horario_servicio and activo for share;
    if not found then raise exception 'El horario no está disponible.'; end if;
    if horario.dia <> (array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[extract(isodow from ahora)::integer]
       or ahora::time < horario.hora_inicio::time or ahora::time >= horario.hora_fin::time then
      raise exception 'La entrada solo se puede registrar durante el horario matriculado (hora de Perú).';
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
    registro.id_horario_servicio := horario.id_horario_servicio;
    registro.servicio := horario.servicio;
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
    entrada := registro."Fecha" + coalesce(nullif(registro.hora_entrada::text, ''), registro."Hora"::text)::time;
    salida := coalesce(registro.fecha_salida, registro."Fecha") + nullif(registro.hora_salida::text, '')::time;
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
  evento := p_evento || jsonb_build_object('fecha', to_char(ahora, 'YYYY-MM-DD"T"HH24:MI:SS') || '-05:00',
    'antes', case when p_version is null then null else to_jsonb(anterior) - 'auditoria' end,
    'despues', to_jsonb(registro) - 'auditoria');
  registro.auditoria := coalesce(registro.auditoria, '[]'::jsonb) || jsonb_build_array(evento);

  if p_version is null then
    insert into public."ASISTENCIA" (id_asistencia, id_cliente, id_membresia, "Fecha", "Hora", "Validación", servicio,
      id_usuario_registra, id_matricula, id_horario_servicio, hora_entrada, hora_salida, fecha_salida, anulado, auditoria, version)
    overriding system value
    values (registro.id_asistencia, registro.id_cliente, registro.id_membresia, registro."Fecha", registro."Hora", registro."Validación", registro.servicio,
      registro.id_usuario_registra, registro.id_matricula, registro.id_horario_servicio, registro.hora_entrada, registro.hora_salida,
      registro.fecha_salida, registro.anulado, registro.auditoria, registro.version)
    returning * into registro;
  else
    update public."ASISTENCIA" set "Fecha" = registro."Fecha", "Hora" = registro."Hora", hora_entrada = registro.hora_entrada,
      hora_salida = registro.hora_salida, fecha_salida = registro.fecha_salida, anulado = registro.anulado,
      auditoria = registro.auditoria, version = registro.version
      where id_asistencia = registro.id_asistencia returning * into registro;
  end if;
  return to_jsonb(registro);
end;
$$;

revoke all on function public.guardar_asistencia(jsonb, integer, jsonb) from public, anon, authenticated;
grant execute on function public.guardar_asistencia(jsonb, integer, jsonb) to service_role;
notify pgrst, 'reload schema';
commit;
