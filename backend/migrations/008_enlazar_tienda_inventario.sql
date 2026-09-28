-- Ejecutar en Supabase > SQL Editor. Solo datos: no crea ni elimina columnas.
-- Enlaza cada producto de TIENDA_PRODUCTOS con su ítem de INVENTARIO (Tipo 'Tienda'), que pasa
-- a ser el dueño del stock. TIENDA_PRODUCTOS.cantidad_stock se conserva como copia.
-- Antes de cambiar nada guarda una copia de las tablas en el esquema respaldo_008 (no expuesto
-- por la API). Para deshacer: 008_enlazar_tienda_inventario_rollback.sql.
-- Puede ejecutarse más de una vez sin duplicar datos.
begin;

-- 0. Respaldo (solo la primera vez).
create schema if not exists respaldo_008;
revoke all on schema respaldo_008 from public;

do $$
begin
  if to_regclass('respaldo_008.inventario') is null then
    create table respaldo_008.inventario as table public."INVENTARIO";
    create table respaldo_008.tienda_productos as table public."TIENDA_PRODUCTOS";
    create table respaldo_008.mov_inv as table public."MOV_INV";
  end if;
end
$$;

create table if not exists respaldo_008.items_creados (
  id_item bigint primary key,
  id_producto bigint not null unique
);

-- 1. Enlaza por nombre los productos que ya tienen su ítem en INVENTARIO
--    (solo coincidencias exactas y únicas en ambos sentidos).
with candidatos as (
  select p.id_producto, i.id_item
  from public."TIENDA_PRODUCTOS" p
  join public."INVENTARIO" i
    on lower(btrim(i."Nombre_item")) = lower(btrim(p."nombre_Producto"))
  where p.id_item is null
    and not exists (select 1 from public."TIENDA_PRODUCTOS" p2 where p2.id_item = i.id_item)
),
unicos as (
  select id_producto, min(id_item) as id_item
  from candidatos
  group by id_producto
  having count(*) = 1
),
sin_repetir as (
  select id_producto, id_item
  from unicos
  where id_item in (select id_item from unicos group by id_item having count(*) = 1)
)
update public."TIENDA_PRODUCTOS" p
set id_item = s.id_item
from sin_repetir s
where p.id_producto = s.id_producto;

-- 2. Crea en INVENTARIO los productos que no tenían ítem (su stock actual es el saldo inicial).
with base as (
  select
    coalesce(max(id_item), 0) as max_id,
    coalesce(max("N_ACTIVO"), 0) as max_activo
  from public."INVENTARIO"
),
nuevos as (
  select
    p.id_producto,
    p."nombre_Producto" as nombre,
    greatest(coalesce(p.cantidad_stock, 0), 0) as stock,
    row_number() over (order by p.id_producto) as rn
  from public."TIENDA_PRODUCTOS" p
  where p.id_item is null
),
insertados as (
  insert into public."INVENTARIO" (id_item, "Nombre_item", "Tipo", "Cantidad_Stock_E", "Estado", "N_ACTIVO")
  select b.max_id + n.rn, n.nombre, 'Tienda', n.stock, 'Disponible', b.max_activo + n.rn
  from nuevos n
  cross join base b
  returning id_item
)
insert into respaldo_008.items_creados (id_item, id_producto)
select b.max_id + n.rn, n.id_producto
from nuevos n
cross join base b;

update public."TIENDA_PRODUCTOS" p
set id_item = c.id_item
from respaldo_008.items_creados c
where p.id_producto = c.id_producto
  and p.id_item is null;

-- Deja constancia del saldo inicial de los ítems creados.
insert into public."MOV_INV" (id_mov, id_item, id_usuario, tipo_movimiento, fecha_movimiento, descripcion, cantidad)
select
  (select coalesce(max(id_mov), 0) from public."MOV_INV") + row_number() over (order by c.id_item),
  c.id_item,
  null,
  'entrada',
  current_date,
  '[008] Saldo inicial al registrar el producto en Inventario',
  i."Cantidad_Stock_E"
from respaldo_008.items_creados c
join public."INVENTARIO" i using (id_item)
where i."Cantidad_Stock_E" > 0
  and not exists (select 1 from public."MOV_INV" m where m.id_item = c.id_item);

-- 3. Todo ítem con producto en tienda es Tipo 'Tienda' (la categoría sigue en TIENDA_PRODUCTOS).
update public."INVENTARIO" i
set "Tipo" = 'Tienda'
where i.id_item in (select id_item from public."TIENDA_PRODUCTOS" where id_item is not null)
  and i."Tipo" is distinct from 'Tienda';

-- 4. Manda el stock de INVENTARIO: la copia de la tienda muestra la misma cantidad.
update public."TIENDA_PRODUCTOS" p
set cantidad_stock = i."Cantidad_Stock_E"
from public."INVENTARIO" i
where p.id_item = i.id_item
  and p.cantidad_stock is distinct from i."Cantidad_Stock_E";

-- 5. Alinea las secuencias (si existen) con los IDs explícitos que usa el backend.
do $$
declare
  secuencia text;
begin
  secuencia := pg_get_serial_sequence('public."INVENTARIO"', 'id_item');
  if secuencia is not null then
    perform setval(secuencia, (select greatest(coalesce(max(id_item), 0), 1) from public."INVENTARIO"));
  end if;

  secuencia := pg_get_serial_sequence('public."MOV_INV"', 'id_mov');
  if secuencia is not null then
    perform setval(secuencia, (select greatest(coalesce(max(id_mov), 0), 1) from public."MOV_INV"));
  end if;
end
$$;

commit;

-- Verificación (solo lectura):
--   select p.id_producto, p."nombre_Producto", p.categoria, i.id_item, i."Nombre_item", i."Tipo",
--          i."Cantidad_Stock_E" as stock_inventario, p.cantidad_stock as copia_tienda
--   from public."TIENDA_PRODUCTOS" p
--   join public."INVENTARIO" i using (id_item)
--   order by p.id_producto;
