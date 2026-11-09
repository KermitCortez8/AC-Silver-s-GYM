-- Precondiciones: CLIENTES, VENTAS con id_cliente y las RPC de 015/020.
-- Aplicar antes del backend que desvincula pedidos al borrar clientes.
-- No elimina clientes ni ventas al instalarse; no modifica cobros, líneas o stock.
-- La FK histórica de VENTAS a CLIENTES se conserva con su nombre y validación.
-- El trigger desvincula las ventas antes del DELETE que ejecuta la RPC atómica:
-- esta ordena los borrados antes de las actualizaciones de pedidos.
-- Recuperación: volver al backend anterior conservando columnas y trigger.
-- No restaurar NOT NULL ni eliminar las copias históricas: hay ventas sin cuenta.
-- Verificación: test_client_deletion_postgres.py, solo PostgreSQL desechable.
begin;

alter table public."VENTAS"
  alter column id_cliente drop not null,
  add column if not exists cliente_nombre text not null default '',
  add column if not exists cliente_correo text not null default '',
  add column if not exists cliente_dni text not null default '';

create or replace function public.preservar_ventas_cliente_eliminado()
returns trigger language plpgsql security invoker
set search_path = pg_catalog, public as $$
declare
  cliente jsonb := to_jsonb(old);
begin
  update public."VENTAS" v set
    cliente_nombre = coalesce(nullif(btrim(v.cliente_nombre), ''),
      nullif(btrim(concat_ws(' ', cliente->>'Nombres', cliente->>'Apellidos')), ''), 'Cliente'),
    cliente_correo = coalesce(nullif(btrim(v.cliente_correo), ''),
      nullif(cliente->>'Correo', ''), cliente->>'Email', ''),
    cliente_dni = coalesce(nullif(btrim(v.cliente_dni), ''), cliente->>'DNI', ''),
    id_cliente = null
  where v.id_cliente = old.id_cliente;
  return old;
end;
$$;

revoke all on function public.preservar_ventas_cliente_eliminado() from public, anon, authenticated;
grant execute on function public.preservar_ventas_cliente_eliminado() to service_role;
drop trigger if exists preservar_ventas_antes_borrar_cliente on public."CLIENTES";
create trigger preservar_ventas_antes_borrar_cliente
  before delete on public."CLIENTES"
  for each row execute function public.preservar_ventas_cliente_eliminado();

notify pgrst, 'reload schema';
commit;
