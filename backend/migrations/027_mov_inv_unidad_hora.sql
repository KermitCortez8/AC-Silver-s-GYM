-- 027: MOV_INV registra la unidad afectada y la hora del movimiento.
--   * id_unidad: unidad de INVENTARIO_UNIDADES a la que se refiere el movimiento
--     (traslado de ubicación, baja o restablecimiento). Vacío en los movimientos de cantidad.
--   * hora_movimiento: hora local de Lima en que se registró el movimiento.
--     Las filas existentes la toman de created_at.
--   * tipo_movimiento admite 'traslado': cambio de ubicación de una unidad; no altera el stock.
-- El RPC commit_gym_transaction ya inserta INVENTARIO_UNIDADES antes que MOV_INV (026),
-- así que no necesita redefinirse.

alter table public."MOV_INV"
  add column if not exists id_unidad bigint
    references public."INVENTARIO_UNIDADES"(id_unidad) on delete set null;

alter table public."MOV_INV"
  add column if not exists hora_movimiento time;

-- Instalaciones sin created_at en MOV_INV dejan la hora vacía en las filas antiguas.
do $$
begin
  if exists (select 1 from information_schema.columns
             where table_schema = 'public' and table_name = 'MOV_INV' and column_name = 'created_at') then
    update public."MOV_INV"
    set hora_movimiento = (created_at at time zone 'America/Lima')::time(0)
    where hora_movimiento is null;
  end if;
end $$;

alter table public."MOV_INV"
  alter column hora_movimiento set default (now() at time zone 'America/Lima')::time(0);

create index if not exists mov_inv_unidad_idx on public."MOV_INV" (id_unidad);

-- Las bajas registradas con 026 nombran una sola unidad en su descripción: se enlazan a ella.
update public."MOV_INV" m
set id_unidad = u.id_unidad
from public."INVENTARIO_UNIDADES" u
where m.id_unidad is null
  and m.tipo_movimiento = 'salida'
  and u.id_item = m.id_item
  and m.descripcion ~ ('Unidades: ' || u.codigo || '$');
