-- 021_persist_attendance_status.sql
-- Dependencias: 005_harden_attendance.sql, 013_general_attendance.sql y
-- 018_attendance_schedule_exit_deadline.sql. Compatible con 019_schedule_sessions.sql.
-- Aplicar antes de 022_attendance_status_cron.sql y del backend que lee estado_asistencia.
-- Recuperación: pausar el trabajo de 022, retirar el trigger y restaurar el backend
-- anterior. Conservar estado_asistencia y la auditoría; no borrar visitas.
begin;

alter table public."ASISTENCIA"
  add column if not exists estado_asistencia text;

-- Función pura para comprobar también el límite exacto, sin alterar el reloj real.
create or replace function public.estado_visita_asistencia(
  p_anulado boolean, p_limite timestamptz, p_salida timestamp,
  p_tardia boolean, p_ahora timestamptz
) returns text language sql immutable
set search_path = pg_catalog, public as $$
  select case
    when coalesce(p_anulado, false) then 'anulada'
    when coalesce(p_tardia, false)
      or (p_limite is not null and
          coalesce(p_salida at time zone 'America/Lima', p_ahora) > p_limite)
      then 'incompleta'
    when p_salida is not null then 'completada'
    else 'dentro'
  end;
$$;

create or replace function public.actualizar_estado_asistencia()
returns trigger language plpgsql security definer
set search_path = pg_catalog, public as $$
declare
  ahora timestamptz := clock_timestamp();
  salida timestamp;
  previo text;
begin
  salida := coalesce(new.fecha_salida, new."Fecha")::date
    + nullif(new.hora_salida::text, '')::time;
  new.estado_asistencia := public.estado_visita_asistencia(
    new.anulado, new.limite_salida, salida, new.salida_tardia, ahora);
  if tg_op = 'UPDATE' then previo := old.estado_asistencia; end if;
  if new.estado_asistencia = 'incompleta' and previo is distinct from 'incompleta'
     and salida is null then
    new.auditoria := coalesce(new.auditoria, '[]'::jsonb) || jsonb_build_array(
      jsonb_build_object('accion', 'incompleta_automatica',
        'actor_id', 'sistema', 'actor_nombre', 'Sistema', 'fecha', ahora,
        'motivo', 'Se superó el límite de salida sin registrar la salida.',
        'antes', jsonb_build_object('estado_asistencia', previo),
        'despues', jsonb_build_object('estado_asistencia', 'incompleta',
          'limite_salida', new.limite_salida)));
  end if;
  -- Materializar el estado no altera fechas, horas ni la versión de edición:
  -- una salida/corrección pendiente no entra en conflicto por el mero paso del tiempo.
  return new;
end;
$$;

drop trigger if exists asistencia_estado_automatico on public."ASISTENCIA";
create trigger asistencia_estado_automatico
before insert or update on public."ASISTENCIA"
for each row execute function public.actualizar_estado_asistencia();

create index if not exists asistencia_pendiente_limite_idx
on public."ASISTENCIA" (limite_salida)
where not coalesce(anulado, false)
  and coalesce(hora_salida::text, '') = ''
  and estado_asistencia is distinct from 'incompleta';

create or replace function public.marcar_asistencias_incompletas()
returns integer language plpgsql security definer
set search_path = pg_catalog, public as $$
declare
  cantidad integer;
  ahora timestamptz;
begin
  -- Misma exclusión mutua que guardar_asistencia; nunca inventa una salida.
  perform pg_advisory_xact_lock(51005, 1);
  ahora := clock_timestamp();
  update public."ASISTENCIA"
     set estado_asistencia = 'incompleta'
   where not coalesce(anulado, false)
     and coalesce(hora_salida::text, '') = ''
     and limite_salida < ahora
     and estado_asistencia is distinct from 'incompleta';
  get diagnostics cantidad = row_count;
  return cantidad;
end;
$$;

-- Inicializa también visitas históricas. Repetir la migración no duplica eventos.
update public."ASISTENCIA" set estado_asistencia = estado_asistencia
where estado_asistencia is null;
select public.marcar_asistencias_incompletas();

revoke all on function public.estado_visita_asistencia(boolean, timestamptz, timestamp, boolean, timestamptz) from public, anon, authenticated;
revoke all on function public.actualizar_estado_asistencia() from public, anon, authenticated;
revoke all on function public.marcar_asistencias_incompletas() from public, anon, authenticated;
grant execute on function public.estado_visita_asistencia(boolean, timestamptz, timestamp, boolean, timestamptz) to service_role;
grant execute on function public.marcar_asistencias_incompletas() to service_role;
notify pgrst, 'reload schema';
commit;
