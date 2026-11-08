-- 019_papelera_tienda.sql
--
-- Papelera de Tienda. Eliminar un producto lo archiva (archivado = true, migración 018) junto
-- con su artículo de INVENTARIO, y desde la papelera se restaura o se elimina.
-- Al eliminar desde la papelera, lo que no tiene historial se borra de verdad. Un producto con
-- ventas (DETALLE_VENTA, ON DELETE RESTRICT) o un artículo con movimientos (MOV_INV, que se
-- borraría en cascada) se marca eliminado = true: deja de mostrarse en todas partes y su
-- historial se conserva.
-- Solo añade columnas; se puede ejecutar más de una vez.
--
-- Reversión: alter table public."INVENTARIO" drop column if exists eliminado;
--            alter table public."TIENDA_PRODUCTOS" drop column if exists eliminado;

alter table public."INVENTARIO"
  add column if not exists eliminado boolean not null default false;

alter table public."TIENDA_PRODUCTOS"
  add column if not exists eliminado boolean not null default false;
