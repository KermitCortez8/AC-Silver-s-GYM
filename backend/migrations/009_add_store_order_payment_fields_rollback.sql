-- 009_add_store_order_payment_fields_rollback.sql
--
-- Revierte la migración 009.
-- ATENCIÓN: borra la columna y TODAS las referencias de pago guardadas en ella
-- (session_id de Stripe y referencias de Yape, Plin y transferencia).

ALTER TABLE "VENTAS"
  DROP COLUMN IF EXISTS referencia_pago;

NOTIFY pgrst, 'reload schema';