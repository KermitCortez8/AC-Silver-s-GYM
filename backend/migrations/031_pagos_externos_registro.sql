-- Requiere 001_add_membership_payment_fields y 020_public_preregistrations.
-- Aplicar antes del backend de pagos externos. Para volver a la versión anterior,
-- conserva la columna y concilia las solicitudes abiertas antes de retroceder.
begin;

alter table public."PREREGISTROS_MEMBRESIA"
  add column if not exists medio_pago text check (medio_pago in ('yape_plin', 'mercado_pago'));

notify pgrst, 'reload schema';
commit;
