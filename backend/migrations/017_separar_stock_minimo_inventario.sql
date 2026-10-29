-- 017_separar_stock_minimo_inventario.sql
--
-- Desde ahora cada tabla usa su propio stock mínimo:
--   * INVENTARIO.stock_minimo: alerta y estado del ítem en el almacén.
--   * TIENDA_PRODUCTOS.stock_minimo: alerta del stock de la tienda.
-- Hasta ahora los ítems Tipo 'Tienda' usaban el mínimo de su producto. Esta migración copia
-- una sola vez ese valor a su ítem para que el estado de Inventario no cambie al separarlos.
-- Solo datos; se puede ejecutar más de una vez.

update public."INVENTARIO" i
set stock_minimo = p.stock_minimo
from public."TIENDA_PRODUCTOS" p
where p.id_item = i.id_item
  and p.stock_minimo is not null
  and i.stock_minimo is distinct from p.stock_minimo;
