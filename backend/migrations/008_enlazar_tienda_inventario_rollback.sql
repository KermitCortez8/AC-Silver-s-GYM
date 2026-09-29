-- Deshace 008_enlazar_tienda_inventario.sql. Ejecutar en Supabase > SQL Editor.
-- Qué hace:
--   * Devuelve id_item, "Tipo" y el stock de la tienda a sus valores previos en las filas que existían antes.
--   * Borra los ítems que creó 008 solo si no tienen más movimientos que su saldo inicial.
-- Qué conserva a propósito:
--   * Los movimientos de MOV_INV registrados después de 008 (ventas, devoluciones, entradas).
--   * El stock de INVENTARIO actual (ya incluye las ventas posteriores).
--   * El esquema respaldo_008 (bórralo a mano cuando ya no lo necesites: drop schema respaldo_008 cascade;).
begin;

do $$
begin
  if to_regclass('respaldo_008.tienda_productos') is null then
    raise exception 'No existe el respaldo de 008; no hay nada que deshacer.';
  end if;
end
$$;

-- 1. TIENDA_PRODUCTOS: vínculo previo. El stock toma el de su ítem si sigue enlazado; si no, el del respaldo.
update public."TIENDA_PRODUCTOS" p
set id_item = r.id_item,
    cantidad_stock = coalesce(
      (select i."Cantidad_Stock_E" from public."INVENTARIO" i where i.id_item = p.id_item),
      r.cantidad_stock
    )
from respaldo_008.tienda_productos r
where p.id_producto = r.id_producto;

-- 2. INVENTARIO: "Tipo" original de los ítems que existían antes de 008.
update public."INVENTARIO" i
set "Tipo" = r."Tipo"
from respaldo_008.inventario r
where i.id_item = r.id_item
  and i."Tipo" is distinct from r."Tipo";

-- 3. Ítems creados por 008: se eliminan solo si nadie los usa y no tienen movimientos propios.
delete from public."MOV_INV" m
using respaldo_008.items_creados c
where m.id_item = c.id_item
  and m.descripcion = '[008] Saldo inicial al registrar el producto en Inventario'
  and not exists (
    select 1 from public."MOV_INV" otro
    where otro.id_item = c.id_item
      and otro.descripcion is distinct from '[008] Saldo inicial al registrar el producto en Inventario'
  )
  and not exists (select 1 from public."TIENDA_PRODUCTOS" p where p.id_item = c.id_item);

delete from public."INVENTARIO" i
using respaldo_008.items_creados c
where i.id_item = c.id_item
  and not exists (select 1 from public."MOV_INV" m where m.id_item = c.id_item)
  and not exists (select 1 from public."TIENDA_PRODUCTOS" p where p.id_item = c.id_item);

commit;
