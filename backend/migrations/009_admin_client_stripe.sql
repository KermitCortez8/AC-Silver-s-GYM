-- Ejecutar en Supabase > SQL Editor antes de registrar clientes desde el panel.
-- Los registros anteriores conservan origen desconocido: no se infiere quién los creó.
begin;

alter table public."CLIENTES"
  add column if not exists origen_registro text
  check (origen_registro in ('ADMIN', 'PUBLICO'));

comment on column public."CLIENTES".origen_registro is
  'Origen asignado por el backend. Solo ADMIN permite iniciar cobros desde el panel.';

commit;
