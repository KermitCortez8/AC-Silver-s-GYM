-- Precondición: 004_membership_email_notifications.sql aplicada.
-- Aplicar después de 023, antes de habilitar los avisos de renovación del backend.
-- Recuperación: detener backend, borrar solo eventos expiring/expired y restaurar
-- el CHECK original ('payment', 'activation'); conservar los pagos y membresías.
BEGIN;
ALTER TABLE public.membership_email_notifications
    DROP CONSTRAINT IF EXISTS membership_email_notifications_event_type_check;
ALTER TABLE public.membership_email_notifications
    ADD CONSTRAINT membership_email_notifications_event_type_check
    CHECK (event_type IN ('payment', 'activation', 'expiring', 'expired'));
COMMIT;
NOTIFY pgrst, 'reload schema';
