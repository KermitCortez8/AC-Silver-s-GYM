-- Revierte 027. Los traslados no tienen sentido sin su unidad: se eliminan antes de quitar la columna.
delete from public."MOV_INV" where tipo_movimiento = 'traslado';
drop index if exists public.mov_inv_unidad_idx;
alter table public."MOV_INV" drop column if exists id_unidad;
alter table public."MOV_INV" drop column if exists hora_movimiento;
