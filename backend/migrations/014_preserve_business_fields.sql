-- Aplicar antes de desplegar el backend que usa commit_gym_transaction.
-- Conserva campos del contrato que anteriormente no se escribían o leían.
begin;

alter table public."USUARIO" add column if not exists codigo_usuario text;
update public."USUARIO" set codigo_usuario =
  'SG' || case lower(coalesce(nullif(btrim("Rol"::text), ''), 'staff')) when 'admin' then 'ADM' when 'trainer' then 'TRA'
    when 'staff' then 'STA' else 'USR' end || lpad(id_usuario::text, greatest(3, length(id_usuario::text)), '0')
where codigo_usuario is null or btrim(codigo_usuario) = '';
create unique index if not exists usuario_codigo_estable_unique on public."USUARIO" (codigo_usuario);

alter table if exists public."PROMOCIONES"
  add column if not exists limite_cupos integer check (limite_cupos > 0),
  add column if not exists usos_actuales integer not null default 0 check (usos_actuales >= 0),
  add column if not exists icono_etiqueta text not null default '🏷️',
  add column if not exists palabra_clave text not null default '';
alter table public."MEMBRESIA" add column if not exists id_promocion bigint;
alter table public."INVENTARIO"
  add column if not exists unidad_venta text not null default 'unidad',
  add column if not exists precio_venta numeric(14,2) not null default 0,
  add column if not exists stock_minimo integer not null default 1,
  add column if not exists ubicacion text not null default 'Almacén',
  add column if not exists observaciones text not null default '';
alter table public."TIENDA_PRODUCTOS"
  add column if not exists descripcion text not null default '',
  add column if not exists unidad_venta text not null default 'unidad';

notify pgrst, 'reload schema';
commit;
