-- Supabase > SQL Editor. Ejecutar después de 001–005.
-- Avisos administrativos y recordatorios semanales, privados y persistentes.
begin;

alter table public."MATRICULAS_HORARIO"
  add column if not exists email_registered_at timestamptz;
-- No envía avisos de inscripción por las matrículas históricas.
update public."MATRICULAS_HORARIO" m
set email_registered_at = coalesce(
  nullif(to_jsonb(m)->>'fecha_matricula', '')::date::timestamp at time zone 'America/Lima',
  now() - interval '7 days')
where email_registered_at is null;
alter table public."MATRICULAS_HORARIO"
  alter column email_registered_at set default now(),
  alter column email_registered_at set not null;

create table if not exists public.schedule_email_notifications (
  event_key text primary key,
  id_matricula bigint not null references public."MATRICULAS_HORARIO" (id_matricula) on delete cascade,
  event_type text not null check (event_type in ('enrollment', 'reminder')),
  class_start timestamptz,
  schedule_signature text not null,
  registered_by text,
  status text not null default 'pending' check (status in ('pending', 'processing', 'sent', 'cancelled')),
  available_at timestamptz not null default now(),
  attempts integer not null default 0,
  claim_token text,
  locked_until timestamptz,
  delivery_id text,
  last_error text,
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  check ((event_type = 'reminder') = (class_start is not null))
);
create index if not exists schedule_email_due_idx
  on public.schedule_email_notifications (available_at, created_at)
  where status in ('pending', 'processing');
alter table public.schedule_email_notifications enable row level security;
revoke all on public.schedule_email_notifications from anon, authenticated;
grant all on public.schedule_email_notifications to service_role;

create or replace function public.schedule_email_signature(p_schedule jsonb)
returns text language sql immutable set search_path = pg_catalog, public as $$
  select md5(concat_ws('|', p_schedule->>'dia', (p_schedule->>'hora_inicio')::time::text,
    (p_schedule->>'hora_fin')::time::text, p_schedule->>'servicio'));
$$;

-- La creación y su aviso se guardan en la misma transacción: un reinicio entre
-- matricular y enviar nunca pierde el aviso. Solo la API con rol admin usa esta RPC.
create or replace function public.matricular_cliente_horario_admin(
  p_id_cliente bigint, p_id_horario_servicio bigint, p_admin_id text
) returns jsonb language plpgsql security definer set search_path = pg_catalog, public as $$
declare
  created jsonb;
  schedule jsonb;
begin
  if length(trim(coalesce(p_admin_id, ''))) = 0 then
    raise exception 'Falta identificar al administrador';
  end if;
  created := public.matricular_cliente_horario(p_id_cliente, p_id_horario_servicio);
  select to_jsonb(s) into schedule from public."HORARIOS_SERVICIO" s
    where s.id_horario_servicio = p_id_horario_servicio;
  insert into public.schedule_email_notifications (event_key, id_matricula, event_type, schedule_signature, registered_by)
  values ('enrollment/' || (created->>'id_matricula'), (created->>'id_matricula')::bigint,
    'enrollment', public.schedule_email_signature(schedule), p_admin_id);
  return created;
end;
$$;

-- El proceso revisa hoy y mañana para incluir clases cuya hora previa cae antes
-- de medianoche. Una clave por matrícula/inicio identifica cada clase semanal.
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
  where m.estado = 'ACTIVA' and s.activo and c."Estado" is true
    and s.dia = (array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[
      extract(isodow from occurrence.starts at time zone 'America/Lima')::integer]
    and occurrence.starts > p_now and occurrence.starts <= p_now + interval '1 hour'
    and m.email_registered_at <= occurrence.starts - interval '1 hour'
    and exists (
      select 1 from public."MEMBRESIA" membership
      where membership.id_cliente = m.id_cliente and upper(membership."Estado") in ('ACTIVA', 'ACTIVO')
        and upper(membership.estado_pago) = 'PAGADO'
        and membership."Fecha_Inicio" <= (occurrence.starts at time zone 'America/Lima')::date
        and membership."Fecha_Fin" >= (occurrence.starts at time zone 'America/Lima')::date
    )
  on conflict (event_key) do update
    set schedule_signature = excluded.schedule_signature, status = 'pending',
        available_at = excluded.available_at, claim_token = null, locked_until = null, last_error = null
    where job.status = 'cancelled' or (job.status = 'pending' and job.schedule_signature <> excluded.schedule_signature);
  get diagnostics added = row_count;
  return added;
end;
$$;

create or replace function public.claim_schedule_email(p_claim_token text, p_event_key text default null)
returns setof public.schedule_email_notifications language sql security definer set search_path = pg_catalog, public as $$
  update public.schedule_email_notifications as job
  set status = 'processing', claim_token = p_claim_token, locked_until = now() + interval '5 minutes', attempts = attempts + 1
  where job.event_key = (
    select candidate.event_key from public.schedule_email_notifications candidate
    where (p_event_key is null or candidate.event_key = p_event_key)
      and ((candidate.status = 'pending' and candidate.available_at <= now())
        or (candidate.status = 'processing' and candidate.locked_until < now()))
    order by candidate.available_at, candidate.created_at, candidate.event_key
    for update skip locked limit 1
  ) returning job.*;
$$;

-- Consulta datos actuales justo antes de SMTP. No guarda contraseñas, DNI ni
-- credenciales de Google en la cola, ni utiliza direcciones enviadas por el navegador.
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
    if job.class_start <= now() or job.class_start > now() + interval '1 hour'
      or (client->>'Estado')::boolean is not true
      or local_start::time <> schedule.hora_inicio::time
      or schedule.dia <> (array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[extract(isodow from local_start)::integer]
      or not exists (
        select 1 from public."MEMBRESIA" membership where membership.id_cliente = enrollment.id_cliente
          and upper(membership."Estado") in ('ACTIVA', 'ACTIVO') and upper(membership.estado_pago) = 'PAGADO'
          and membership."Fecha_Inicio" <= local_start::date and membership."Fecha_Fin" >= local_start::date
      ) then return null; end if;
  end if;
  return jsonb_build_object(
    'nombre', trim(concat_ws(' ', client->>'Nombres', client->>'Apellidos')),
    'correo', coalesce(nullif(trim(client->>'Correo'), ''), nullif(trim(client->>'Email'), '')),
    'servicio', schedule.servicio, 'dia', schedule.dia,
    'hora_inicio', schedule.hora_inicio, 'hora_fin', schedule.hora_fin,
    'class_start', job.class_start, 'event_type', job.event_type
  );
end;
$$;

revoke all on function public.schedule_email_signature(jsonb) from public, anon, authenticated;
revoke all on function public.matricular_cliente_horario_admin(bigint, bigint, text) from public, anon, authenticated;
revoke all on function public.enqueue_due_schedule_reminders(timestamptz) from public, anon, authenticated;
revoke all on function public.claim_schedule_email(text, text) from public, anon, authenticated;
revoke all on function public.schedule_email_delivery_context(text, text) from public, anon, authenticated;
grant execute on function public.matricular_cliente_horario_admin(bigint, bigint, text) to service_role;
grant execute on function public.enqueue_due_schedule_reminders(timestamptz) to service_role;
grant execute on function public.claim_schedule_email(text, text) to service_role;
grant execute on function public.schedule_email_delivery_context(text, text) to service_role;
notify pgrst, 'reload schema';
commit;
