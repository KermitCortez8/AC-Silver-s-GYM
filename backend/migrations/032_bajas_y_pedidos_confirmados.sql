-- 032: fecha de baja de los artículos y pedidos pagados confirmados.
--   * INVENTARIO.fecha_baja: día en que el artículo se archivó (pestaña Bajas de Inventario).
--     Se borra al restaurarlo. Los artículos archivados antes de esta migración quedan sin fecha.
--   * VENTAS: un pedido pagado nace CONFIRMADO; los pagados que seguían PENDIENTE pasan a CONFIRMADO.

alter table public."INVENTARIO"
  add column if not exists fecha_baja date;

update public."VENTAS"
set estado_pedido = 'CONFIRMADO'
where upper(coalesce(estado_pago, '')) = 'PAGADO'
  and upper(coalesce(estado_pedido, '')) = 'PENDIENTE';
