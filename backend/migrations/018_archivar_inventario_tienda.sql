-- 018_archivar_inventario_tienda.sql
--
-- Archivado (soft delete) de artículos de INVENTARIO y productos de TIENDA_PRODUCTOS.
-- Un producto con ventas en DETALLE_VENTA no se puede borrar (ON DELETE RESTRICT), y un
-- artículo enlazado a un producto tampoco. En esos casos el backend marca archivado = true:
-- deja de mostrarse y de venderse, pero sus ventas, movimientos y reportes se conservan.
-- Los registros sin historial se siguen borrando de verdad.
-- Solo añade columnas; se puede ejecutar más de una vez.
--
-- Reversión: alter table public."INVENTARIO" drop column if exists archivado;
--            alter table public."TIENDA_PRODUCTOS" drop column if exists archivado;

alter table public."INVENTARIO"
  add column if not exists archivado boolean not null default false;

alter table public."TIENDA_PRODUCTOS"
  add column if not exists archivado boolean not null default false;
