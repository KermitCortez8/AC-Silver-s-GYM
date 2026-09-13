-- Ejecutar DESPUÉS de desplegar schedule-emails, configurar Secrets/Vault y 006.
-- Guía: docs/supabase-recordatorios.md. No escribir contraseñas en este archivo.
begin;

create extension if not exists pg_cron;
create extension if not exists pg_net with schema extensions;

-- Solo el propietario de la BD/Cron puede invocarla; no es una ruta pública.
create or replace function public.invoke_schedule_emails(p_dry_run boolean default false)
returns bigint language plpgsql security definer
set search_path = pg_catalog, public as $$
declare
  project_url text;
  cron_secret text;
begin
  select rtrim(decrypted_secret, '/') into project_url
    from vault.decrypted_secrets where name = 'silver_gym_project_url';
  select decrypted_secret into cron_secret
    from vault.decrypted_secrets where name = 'silver_gym_schedule_cron_secret';
  if project_url is null or project_url !~ '^https://[a-z0-9-]+\.supabase\.co$' then
    raise exception 'Configura silver_gym_project_url en Vault con https://TU_PROJECT_REF.supabase.co';
  end if;
  if cron_secret is null or length(cron_secret) not between 32 and 256
    or cron_secret !~ '^[A-Za-z0-9_-]+$' then
    raise exception 'Configura silver_gym_schedule_cron_secret en Vault con el mismo SCHEDULE_CRON_SECRET de Edge Functions';
  end if;
  return net.http_post(
    url := project_url || '/functions/v1/schedule-emails',
    headers := jsonb_build_object('Content-Type', 'application/json', 'Authorization', 'Bearer ' || cron_secret),
    body := jsonb_build_object('dry_run', coalesce(p_dry_run, false)),
    timeout_milliseconds := 110000
  );
end;
$$;
revoke all on function public.invoke_schedule_emails(boolean) from public, anon, authenticated, service_role;

-- Crea el trabajo pausado. Primero verifica con invoke_schedule_emails(true).
-- Al repetir el script, cron.schedule actualiza el mismo trabajo y lo pausa.
select cron.schedule('silver-gym-schedule-emails', '* * * * *',
  'select public.invoke_schedule_emails();');
select cron.alter_job(jobid, active := false)
  from cron.job where jobname = 'silver-gym-schedule-emails';

notify pgrst, 'reload schema';
commit;
