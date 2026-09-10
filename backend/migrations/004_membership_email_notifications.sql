-- Cola privada de correos transaccionales. Ejecutar en el SQL Editor de Supabase.
BEGIN;

CREATE TABLE IF NOT EXISTS public.membership_email_notifications (
    event_key text PRIMARY KEY,
    id_membresia bigint NOT NULL REFERENCES public."MEMBRESIA" (id_membresia) ON DELETE CASCADE,
    event_type text NOT NULL CHECK (event_type IN ('payment', 'activation')),
    payload jsonb NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'sent')),
    attempts integer NOT NULL DEFAULT 0,
    available_at timestamptz NOT NULL DEFAULT now(),
    locked_until timestamptz,
    claim_token text,
    resend_id text, -- Nombre conservado por compatibilidad; Gmail guarda aquí el Message-ID.
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    sent_at timestamptz,
    UNIQUE (id_membresia, event_type)
);

CREATE INDEX IF NOT EXISTS membership_email_notifications_pending
    ON public.membership_email_notifications (available_at, created_at) WHERE status <> 'sent';

ALTER TABLE public.membership_email_notifications ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.membership_email_notifications FROM anon, authenticated;
GRANT ALL ON public.membership_email_notifications TO service_role;

CREATE OR REPLACE FUNCTION public.enqueue_membership_email(
    p_event_key text, p_id_membresia bigint, p_event_type text, p_payload jsonb
) RETURNS SETOF public.membership_email_notifications
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.membership_email_notifications (event_key, id_membresia, event_type, payload)
    VALUES (p_event_key, p_id_membresia, p_event_type, p_payload)
    ON CONFLICT DO NOTHING;
    RETURN QUERY SELECT * FROM public.membership_email_notifications
    WHERE event_key = p_event_key;
END;
$$;

-- Una sola instancia reclama cada correo. La reserva caduca si el proceso se interrumpe.
CREATE OR REPLACE FUNCTION public.claim_membership_email(p_claim_token text, p_event_key text DEFAULT NULL)
RETURNS SETOF public.membership_email_notifications
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
    UPDATE public.membership_email_notifications AS job
    SET status = 'processing', claim_token = p_claim_token,
        locked_until = now() + interval '5 minutes', attempts = attempts + 1
    WHERE job.event_key = (
        SELECT candidate.event_key FROM public.membership_email_notifications AS candidate
        WHERE (p_event_key IS NULL OR candidate.event_key = p_event_key)
          AND ((candidate.status = 'pending' AND candidate.available_at <= now())
            OR (candidate.status = 'processing' AND candidate.locked_until < now()))
        ORDER BY candidate.created_at, candidate.event_key
        FOR UPDATE SKIP LOCKED LIMIT 1
    )
    RETURNING job.*;
$$;

REVOKE ALL ON FUNCTION public.enqueue_membership_email(text, bigint, text, jsonb) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.claim_membership_email(text, text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.enqueue_membership_email(text, bigint, text, jsonb) TO service_role;
GRANT EXECUTE ON FUNCTION public.claim_membership_email(text, text) TO service_role;

COMMIT;
NOTIFY pgrst, 'reload schema';
