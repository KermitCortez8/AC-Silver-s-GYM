-- Deshace 026_inventario_unidades.sql. Borra las unidades y el prefijo; el stock de INVENTARIO no cambia.
-- Las RPC quedan con INVENTARIO_UNIDADES en su lista: sin la tabla no la usan.
begin;
drop table if exists public."INVENTARIO_UNIDADES";
alter table public."INVENTARIO" drop column if exists prefijo_activo;
drop function if exists public.gym_prefijo_activo(text);
notify pgrst, 'reload schema';
commit;
