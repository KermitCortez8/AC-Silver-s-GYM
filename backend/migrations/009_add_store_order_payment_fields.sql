-- 009_add_store_order_payment_fields.sql
--
-- Agrega la referencia de pago a los pedidos de tienda (tabla VENTAS).
--   * Pago con tarjeta: guarda el session_id de Stripe.
--   * Yape, Plin y transferencia: guarda la referencia que escribe el cliente.
--
-- Es segura: no modifica filas existentes (quedan con referencia vacía) y se
-- puede ejecutar más de una vez. La columna estado_pago ya existe en VENTAS.

ALTER TABLE "VENTAS"
  ADD COLUMN IF NOT EXISTS referencia_pago text NOT NULL DEFAULT '';

-- Pide a PostgREST (API de Supabase) que recargue su caché de columnas.
NOTIFY pgrst, 'reload schema';