-- ============================================================
-- 03_rls_propuesta.sql
-- PROPUESTA de Row Level Security (RLS) para las tablas chatbot_*
-- ============================================================
-- ESTADO   : PROPUESTA — no ejecutar mezclado con 01_crear_tablas.sql.
--            Leer completo, decidir y ejecutar por separado.
-- VERSIÓN  : 1.0  |  Fecha: 2026-11-08
-- ============================================================
-- CRITERIO GENERAL
--   Las 6 tablas chatbot_* solo las usa el backend FastAPI.
--   El acceso directo desde el navegador usando la clave pública
--   (anon key) de Supabase debe quedar completamente cerrado.
--   El cliente autenticado (authenticated role) tampoco debe poder
--   leer ni escribir estas tablas directamente: toda interacción
--   pasa por el backend, que aplica los controles CB11–CB16 antes
--   de cualquier lectura o escritura.
-- ============================================================
-- ROL DEL BACKEND [?-DIFERIDO-6]
--   No está definido en los documentos. Dos opciones principales:
--
--   OPCIÓN A — service_role (recomendada para empezar):
--     · El backend FastAPI se conecta con la SUPABASE_SERVICE_ROLE_KEY.
--     · En Supabase, el service_role BYPASA el RLS por diseño.
--     · Efecto: habilitar RLS + denegar anon/authenticated es suficiente
--       para bloquear el navegador. El backend accede sin restricción.
--     · Ventaja: simple de implementar; sin código adicional en FastAPI.
--     · Riesgo: una filtración de la SUPABASE_SERVICE_ROLE_KEY da acceso
--       total a toda la base de datos.
--
--   OPCIÓN B — rol personalizado (más seguro a largo plazo):
--     · Crear un rol PostgreSQL específico para el backend chatbot.
--     · Dar GRANT SELECT/INSERT/UPDATE solo sobre las tablas chatbot_*.
--     · Escribir políticas RLS que validen ese rol.
--     · Requiere configuración adicional en Supabase y en FastAPI.
--     · Recomendado si el equipo decide separar permisos por módulo.
--
--   DECISIÓN PENDIENTE: indicar con cuál opción proceder.
--   Esta propuesta protege contra el navegador en ambos casos.
-- ============================================================
-- CÓMO EJECUTAR ESTE SCRIPT
--   1. Leer y aprobar cada sección con el equipo.
--   2. Ejecutar el bloque "HABILITAR RLS" primero.
--   3. Ejecutar los bloques de POLÍTICAS después.
--   4. Verificar con las consultas de comprobación al pie.
--   5. NO revertir sin un script de desactivación explícito.
-- ============================================================


-- ============================================================
-- SECCIÓN 1: HABILITAR RLS EN LAS 6 TABLAS
-- ============================================================
-- Habilitar RLS no bloquea nada por sí solo: solo activa el motor
-- de evaluación de políticas. Sin políticas, el comportamiento por
-- defecto es DENEGAR TODO para los roles que no son el propietario.
-- Fuente del requisito: RNF-CB03, RNF-CB04, CUS30 §2 (Backend FastAPI
-- como único actor que modifica datos).
-- ============================================================

ALTER TABLE public.chatbot_conversaciones        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatbot_mensajes              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatbot_rate_limit_contadores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatbot_uso_tokens            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatbot_eventos_seguridad     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatbot_alertas_enviadas      ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- SECCIÓN 2: POLÍTICAS DE DENEGACIÓN TOTAL PARA EL ROL anon
-- ============================================================
-- El rol anon es el que usa el navegador con la clave pública de
-- Supabase. No debe tener ningún acceso a las tablas del chatbot.
-- La política USING (false) bloquea SELECT, UPDATE y DELETE.
-- La cláusula WITH CHECK (false) bloquea INSERT y UPDATE.
-- ============================================================

-- chatbot_conversaciones — denegar anon
DROP POLICY IF EXISTS deny_anon_chatbot_conversaciones ON public.chatbot_conversaciones;
CREATE POLICY deny_anon_chatbot_conversaciones
    ON public.chatbot_conversaciones
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

-- chatbot_mensajes — denegar anon
DROP POLICY IF EXISTS deny_anon_chatbot_mensajes ON public.chatbot_mensajes;
CREATE POLICY deny_anon_chatbot_mensajes
    ON public.chatbot_mensajes
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

-- chatbot_rate_limit_contadores — denegar anon
DROP POLICY IF EXISTS deny_anon_chatbot_rate_limit ON public.chatbot_rate_limit_contadores;
CREATE POLICY deny_anon_chatbot_rate_limit
    ON public.chatbot_rate_limit_contadores
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

-- chatbot_uso_tokens — denegar anon
DROP POLICY IF EXISTS deny_anon_chatbot_uso_tokens ON public.chatbot_uso_tokens;
CREATE POLICY deny_anon_chatbot_uso_tokens
    ON public.chatbot_uso_tokens
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

-- chatbot_eventos_seguridad — denegar anon
DROP POLICY IF EXISTS deny_anon_chatbot_eventos ON public.chatbot_eventos_seguridad;
CREATE POLICY deny_anon_chatbot_eventos
    ON public.chatbot_eventos_seguridad
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

-- chatbot_alertas_enviadas — denegar anon
DROP POLICY IF EXISTS deny_anon_chatbot_alertas ON public.chatbot_alertas_enviadas;
CREATE POLICY deny_anon_chatbot_alertas
    ON public.chatbot_alertas_enviadas
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);


-- ============================================================
-- SECCIÓN 3: POLÍTICAS DE DENEGACIÓN TOTAL PARA EL ROL authenticated
-- ============================================================
-- El rol authenticated corresponde a los usuarios con sesión iniciada
-- en Supabase Auth (clientes del gimnasio). Aunque el widget adjunta
-- el JWT en cada petición, NO debe acceder a las tablas del chatbot
-- directamente: solo el backend FastAPI lo hace.
-- Esto evita que un cliente pueda leer el historial de otras
-- conversaciones, manipular contadores de rate limiting o insertar
-- eventos de seguridad falsos desde el navegador.
-- Fuente: RN-01, RN-04, RNF-CB03, HU-CB11, HU-CB12
-- ============================================================

-- chatbot_conversaciones — denegar authenticated
DROP POLICY IF EXISTS deny_auth_chatbot_conversaciones ON public.chatbot_conversaciones;
CREATE POLICY deny_auth_chatbot_conversaciones
    ON public.chatbot_conversaciones
    FOR ALL
    TO authenticated
    USING (false)
    WITH CHECK (false);

-- chatbot_mensajes — denegar authenticated
DROP POLICY IF EXISTS deny_auth_chatbot_mensajes ON public.chatbot_mensajes;
CREATE POLICY deny_auth_chatbot_mensajes
    ON public.chatbot_mensajes
    FOR ALL
    TO authenticated
    USING (false)
    WITH CHECK (false);

-- chatbot_rate_limit_contadores — denegar authenticated
DROP POLICY IF EXISTS deny_auth_chatbot_rate_limit ON public.chatbot_rate_limit_contadores;
CREATE POLICY deny_auth_chatbot_rate_limit
    ON public.chatbot_rate_limit_contadores
    FOR ALL
    TO authenticated
    USING (false)
    WITH CHECK (false);

-- chatbot_uso_tokens — denegar authenticated
DROP POLICY IF EXISTS deny_auth_chatbot_uso_tokens ON public.chatbot_uso_tokens;
CREATE POLICY deny_auth_chatbot_uso_tokens
    ON public.chatbot_uso_tokens
    FOR ALL
    TO authenticated
    USING (false)
    WITH CHECK (false);

-- chatbot_eventos_seguridad — denegar authenticated
DROP POLICY IF EXISTS deny_auth_chatbot_eventos ON public.chatbot_eventos_seguridad;
CREATE POLICY deny_auth_chatbot_eventos
    ON public.chatbot_eventos_seguridad
    FOR ALL
    TO authenticated
    USING (false)
    WITH CHECK (false);

-- chatbot_alertas_enviadas — denegar authenticated
DROP POLICY IF EXISTS deny_auth_chatbot_alertas ON public.chatbot_alertas_enviadas;
CREATE POLICY deny_auth_chatbot_alertas
    ON public.chatbot_alertas_enviadas
    FOR ALL
    TO authenticated
    USING (false)
    WITH CHECK (false);


-- ============================================================
-- SECCIÓN 4: REVOCACIÓN EXPLÍCITA DE PERMISOS (OPCIONAL)
-- ============================================================
-- En Supabase, el schema public puede tener DEFAULT PRIVILEGES que
-- otorgan permisos a anon y authenticated automáticamente en tablas
-- nuevas. Ejecutar este bloque para revocar explícitamente esos permisos
-- sobre las tablas chatbot_*.
--
-- CUÁNDO EJECUTAR: si las comprobaciones de la Sección 5 muestran
-- que anon o authenticated tienen grants sobre estas tablas.
-- CUÁNDO OMITIR: si las políticas de Sección 2 y 3 son suficientes
-- (con RLS habilitado y política DENY, los grants no llegan a ejecutarse).
-- ============================================================

REVOKE ALL ON public.chatbot_conversaciones
    FROM anon, authenticated;

REVOKE ALL ON public.chatbot_mensajes
    FROM anon, authenticated;

REVOKE ALL ON public.chatbot_rate_limit_contadores
    FROM anon, authenticated;

REVOKE ALL ON public.chatbot_uso_tokens
    FROM anon, authenticated;

REVOKE ALL ON public.chatbot_eventos_seguridad
    FROM anon, authenticated;

REVOKE ALL ON public.chatbot_alertas_enviadas
    FROM anon, authenticated;


-- ============================================================
-- SECCIÓN 5: COMPROBACIONES DE RLS
-- ============================================================
-- Ejecutar DESPUÉS de aplicar este script.
-- Cada consulta devuelve ok = true si la protección está activa.
-- ============================================================

-- Comprobar que RLS está habilitado en las 6 tablas
SELECT
    t.tabla                                         AS tabla,
    EXISTS (
        SELECT 1
        FROM   pg_catalog.pg_class      cl
        JOIN   pg_catalog.pg_namespace  ns ON ns.oid = cl.relnamespace
        WHERE  ns.nspname   = 'public'
          AND  cl.relname   = t.tabla
          AND  cl.relrowsecurity = true
    )                                               AS rls_habilitado
FROM (VALUES
    ('chatbot_conversaciones'),
    ('chatbot_mensajes'),
    ('chatbot_rate_limit_contadores'),
    ('chatbot_uso_tokens'),
    ('chatbot_eventos_seguridad'),
    ('chatbot_alertas_enviadas')
) AS t(tabla)
ORDER BY tabla;


-- Comprobar que existen políticas DENY para anon y authenticated
-- Esperado: 12 filas (6 tablas × 2 roles)
SELECT
    pol.tablename                                   AS tabla,
    pol.roles                                       AS roles,
    pol.policyname                                  AS politica,
    pol.cmd                                         AS operacion,
    (pol.qual = 'false' OR pol.with_check = 'false') AS ok_es_deny
FROM pg_policies pol
WHERE pol.schemaname = 'public'
  AND pol.tablename LIKE 'chatbot_%'
  AND (pol.roles @> ARRAY['anon'] OR pol.roles @> ARRAY['authenticated'])
ORDER BY pol.tablename, pol.roles;


-- ============================================================
-- SECCIÓN 6: NOTAS PARA EL EQUIPO
-- ============================================================
-- · Si el backend usa SUPABASE_SERVICE_ROLE_KEY (Opción A), no necesita
--   ninguna política adicional: el service_role bypasa RLS.
--   En FastAPI, usar supabase-py con la service_role key:
--     supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
--
-- · Si en el futuro el backend usa un rol personalizado (Opción B),
--   agregar GRANT SELECT, INSERT, UPDATE ON TABLE public.chatbot_* TO <rol>;
--   y crear políticas USING (true) solo para ese rol. Avisar para entregar
--   ese script como ajuste separado.
--
-- · Las políticas DROP IF EXISTS + CREATE se pueden re-ejecutar sin
--   dañar las existentes, siempre que el nombre de la política no cambie.
--
-- · La Sección 4 (REVOKE) es idempotente: revocar un permiso que no existe
--   no produce error en PostgreSQL (con IF EXISTS implícito en REVOKE).
-- ============================================================
