-- Revierte 032. Los pedidos confirmados no vuelven a PENDIENTE: no se puede distinguir cuáles
-- confirmó la migración y cuáles confirmó el administrador.
alter table public."INVENTARIO" drop column if exists fecha_baja;
