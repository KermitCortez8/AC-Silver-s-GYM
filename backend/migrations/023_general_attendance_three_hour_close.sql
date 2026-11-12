-- Cierre general a las tres horas; no cambia las salidas reales de las clases.
-- Precondiciones: esquema existente y 005_harden_attendance.sql,
-- 013_general_attendance.sql, 018_attendance_schedule_exit_deadline.sql y
-- 021_persist_attendance_status.sql. Si se usa 019_schedule_sessions.sql,
-- aplicarla antes de 023: se conserva su validación de la fecha de matrícula.
-- 022_attendance_status_cron.sql es opcional para estas RPC; programa la misma
-- función privada cuando pg_cron está disponible. Aplicar antes del backend.
-- Recuperación: pausar el trabajo de 022 y restaurar guardar_asistencia desde
-- guardar_asistencia_sin_cierre_general; restaurar función/trigger de 021.
-- Conservar cierre_automatico, horas, versiones y auditorías; no borrar visitas.
-- Verificación: tests/asistencias/postgres/test_automatic_attendance_postgres.py
-- en un PostgreSQL desechable explícito con base gym_test.
begin;

alter table public."ASISTENCIA"
  add column if not exists cierre_automatico boolean not null default false;

create or replace function public.actualizar_estado_asistencia()
returns trigger language plpgsql security definer
set search_path = pg_catalog, public as $$
declare
  ahora timestamptz := clock_timestamp();
  salida timestamp;
  previo text;
begin
  if tg_op = 'UPDATE' then previo := old.estado_asistencia; end if;
  if new.servicio = 'gimnasio' then
    -- Las visitas cerradas antes de 023 conservan su clasificación histórica.
    if tg_op = 'INSERT' or new.limite_salida is not null
       or coalesce(new.hora_salida::text, '') = '' then
      new.limite_salida := ((new."Fecha"::date
        + coalesce(nullif(new.hora_entrada::text, ''), new."Hora"::text)::time
        + interval '3 hours') at time zone 'America/Lima');
    end if;
    if tg_op = 'INSERT' then
      new.cierre_automatico := false;
    elsif new.auditoria is distinct from old.auditoria
      and new.auditoria->-1->>'accion' = 'correccion' then
      -- Una corrección documentada recupera la salida real sin borrar el cierre.
      new.cierre_automatico := false;
    end if;
  end if;
  salida := coalesce(new.fecha_salida, new."Fecha")::date
    + nullif(new.hora_salida::text, '')::time;
  if new.servicio = 'gimnasio' and new.limite_salida is not null then
    new.salida_tardia := not new.cierre_automatico
      and coalesce((salida at time zone 'America/Lima') > new.limite_salida, false);
  end if;
  new.estado_asistencia := case
    when coalesce(new.anulado, false) then 'anulada'
    when new.cierre_automatico then 'incompleta'
    else public.estado_visita_asistencia(
      new.anulado, new.limite_salida, salida, new.salida_tardia, ahora)
    end;
  if new.servicio is distinct from 'gimnasio'
     and new.estado_asistencia = 'incompleta'
     and previo is distinct from 'incompleta' and salida is null then
    new.auditoria := coalesce(new.auditoria, '[]'::jsonb) || jsonb_build_array(
      jsonb_build_object('accion', 'incompleta_automatica',
        'actor_id', 'sistema', 'actor_nombre', 'Sistema', 'fecha', ahora,
        'motivo', 'Se superó el límite de salida sin registrar la salida.',
        'antes', jsonb_build_object('estado_asistencia', previo),
        'despues', jsonb_build_object('estado_asistencia', 'incompleta',
          'limite_salida', new.limite_salida)));
  end if;
  return new;
end;
$$;

create or replace function public.marcar_asistencias_incompletas()
returns integer language plpgsql security definer
set search_path = pg_catalog, public as $$
declare
  generales integer;
  clases integer;
  ahora timestamptz;
begin
  -- Misma exclusión mutua que guardar_asistencia: la primera salida prevalece.
  perform pg_advisory_xact_lock(51005, 1);
  ahora := clock_timestamp();
  update public."ASISTENCIA" a
     set hora_salida = (a.limite_salida at time zone 'America/Lima')::time,
         fecha_salida = (a.limite_salida at time zone 'America/Lima')::date,
         cierre_automatico = true, salida_tardia = false,
         estado_asistencia = 'incompleta', version = coalesce(a.version, 0) + 1,
         auditoria = coalesce(a.auditoria, '[]'::jsonb) || jsonb_build_array(
           jsonb_build_object('accion', 'cierre_automatico',
             'actor_id', 'sistema', 'actor_nombre', 'Sistema', 'fecha', ahora,
             'motivo', 'Visita general sin salida después de tres horas desde la entrada.',
             'antes', to_jsonb(a) - 'auditoria',
             'despues', jsonb_build_object('estado_asistencia', 'incompleta',
               'hora_salida', (a.limite_salida at time zone 'America/Lima')::time,
               'fecha_salida', (a.limite_salida at time zone 'America/Lima')::date,
               'cierre_automatico', true)))
   where a.servicio = 'gimnasio' and not coalesce(a.anulado, false)
     and coalesce(a.hora_salida::text, '') = '' and a.limite_salida < ahora;
  get diagnostics generales = row_count;

  -- Las clases vencidas siguen pendientes de una salida real y consumen aforo.
  update public."ASISTENCIA"
     set estado_asistencia = 'incompleta'
   where servicio is distinct from 'gimnasio' and not coalesce(anulado, false)
     and coalesce(hora_salida::text, '') = '' and limite_salida < ahora
     and estado_asistencia is distinct from 'incompleta';
  get diagnostics clases = row_count;
  return generales + clases;
end;
$$;

-- Conserva la RPC instalada (018 o 019), sin duplicar ni perder sus validaciones.
-- El renombrado solo se realiza una vez al repetir esta migración.
do $$ begin
  if to_regprocedure('public.guardar_asistencia_sin_cierre_general(jsonb,integer,jsonb)') is null then
    alter function public.guardar_asistencia(jsonb, integer, jsonb)
      rename to guardar_asistencia_sin_cierre_general;
  end if;
end $$;

create or replace function public.guardar_asistencia(p_registro jsonb, p_version integer, p_evento jsonb)
returns jsonb language plpgsql security definer
set search_path = pg_catalog, public as $$
begin
  -- Reconcilia antes de comprobar versión, reintentos, entrada abierta y aforo.
  perform public.marcar_asistencias_incompletas();
  return public.guardar_asistencia_sin_cierre_general(p_registro, p_version, p_evento);
end;
$$;

-- Recupera también abiertas antiguas, incluso si el plazo cruza medianoche.
update public."ASISTENCIA"
   set limite_salida = (("Fecha"::date
     + coalesce(nullif(hora_entrada::text, ''), "Hora"::text)::time
     + interval '3 hours') at time zone 'America/Lima')
 where servicio = 'gimnasio' and not coalesce(anulado, false)
   and coalesce(hora_salida::text, '') = '';
select public.marcar_asistencias_incompletas();

drop index if exists public.asistencia_pendiente_limite_idx;
create index asistencia_pendiente_limite_idx on public."ASISTENCIA" (limite_salida)
where not coalesce(anulado, false) and coalesce(hora_salida::text, '') = ''
  and (servicio = 'gimnasio' or estado_asistencia is distinct from 'incompleta');

revoke all on function public.guardar_asistencia_sin_cierre_general(jsonb, integer, jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.actualizar_estado_asistencia() from public, anon, authenticated;
revoke all on function public.marcar_asistencias_incompletas() from public, anon, authenticated;
revoke all on function public.guardar_asistencia(jsonb, integer, jsonb) from public, anon, authenticated;
grant execute on function public.marcar_asistencias_incompletas() to service_role;
grant execute on function public.guardar_asistencia(jsonb, integer, jsonb) to service_role;
notify pgrst, 'reload schema';
commit;
