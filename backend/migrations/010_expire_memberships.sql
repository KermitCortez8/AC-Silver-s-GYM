-- La fecha de fin incluye todo ese día en hora de Perú.
begin;

create extension if not exists pg_cron;

create or replace function public.expirar_membresias()
returns integer
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
    hoy date := (current_timestamp at time zone 'America/Lima')::date;
    vencidas integer;
begin
    update public."MEMBRESIA"
       set "Estado" = 'VENCIDA'
     where upper(trim(coalesce("Estado", ''))) in ('ACTIVA', 'ACTIVO')
       and "Fecha_Fin"::date < hoy;
    get diagnostics vencidas = row_count;

    -- CLIENTES.Estado es booleano; el API expone VENCIDA desde la membresía.
    update public."CLIENTES" as cliente
       set "Estado" = false
     where cliente."Estado" is distinct from false
       and exists (
           select 1 from public."MEMBRESIA" as m
            where m.id_cliente = cliente.id_cliente
              and upper(trim(coalesce(m."Estado", ''))) in ('VENCIDA', 'VENCIDO')
       )
       and not exists (
           select 1 from public."MEMBRESIA" as m
            where m.id_cliente = cliente.id_cliente
              and upper(trim(coalesce(m."Estado", ''))) in ('ACTIVA', 'ACTIVO')
              and upper(trim(coalesce(m.estado_pago, ''))) = 'PAGADO'
              and m."Fecha_Inicio"::date <= hoy
              and m."Fecha_Fin"::date >= hoy
       );
    return vencidas;
end;
$$;

revoke all on function public.expirar_membresias() from public, anon, authenticated;
grant execute on function public.expirar_membresias() to service_role;

select public.expirar_membresias();
select cron.schedule(
    'silver-gym-expire-memberships',
    '* * * * *',
    'select public.expirar_membresias();'
);

notify pgrst, 'reload schema';
commit;
