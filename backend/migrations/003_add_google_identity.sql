-- Ejecutar en el SQL Editor del proyecto Supabase antes de usar Google.
-- La identidad estable es el sub verificado por Google; el correo puede cambiar.
BEGIN;

ALTER TABLE public."CLIENTES" ADD COLUMN IF NOT EXISTS google_sub text;
ALTER TABLE public."USUARIO" ADD COLUMN IF NOT EXISTS google_sub text;

CREATE UNIQUE INDEX IF NOT EXISTS clientes_google_sub_unique
    ON public."CLIENTES" (google_sub) WHERE google_sub IS NOT NULL AND google_sub <> '';
CREATE UNIQUE INDEX IF NOT EXISTS usuario_google_sub_unique
    ON public."USUARIO" (google_sub) WHERE google_sub IS NOT NULL AND google_sub <> '';

COMMIT;
NOTIFY pgrst, 'reload schema';
