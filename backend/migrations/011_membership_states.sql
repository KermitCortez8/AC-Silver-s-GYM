-- Estados de membresía: ACTIVO, VENCIDA y EN_TRAMITE.
-- El estado de pago y el acceso booleano del cliente se conservan separados.
begin;

-- Conservar el significado del pago de los registros antiguos antes de normalizar.
update public."MEMBRESIA"
   set estado_pago = case
       when upper(trim(coalesce("Estado", ''))) in ('ACTIVA', 'ACTIVO', 'EN_TRAMITE')
       then 'PAGADO' else 'PENDIENTE' end
 where estado_pago is null or trim(estado_pago) = '';

update public."MEMBRESIA"
   set "Estado" = case
       when upper(trim(coalesce("Estado", ''))) in ('ACTIVA', 'ACTIVO') then 'ACTIVO'
       when upper(trim(coalesce("Estado", ''))) in ('VENCIDA', 'VENCIDO') then 'VENCIDA'
       else 'EN_TRAMITE' end;

alter table public."MEMBRESIA" alter column "Estado" set default 'EN_TRAMITE';
alter table public."MEMBRESIA" alter column "Estado" set not null;
alter table public."MEMBRESIA" drop constraint if exists membresia_estado_valido;
alter table public."MEMBRESIA" add constraint membresia_estado_valido
    check ("Estado" in ('ACTIVO', 'VENCIDA', 'EN_TRAMITE'));

-- Reemplaza también la función ya instalada por la migración 010.
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
notify pgrst, 'reload schema';
commit;
