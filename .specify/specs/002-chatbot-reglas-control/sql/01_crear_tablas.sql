-- ============================================================
-- 01_crear_tablas.sql
-- Tablas nuevas para los controles del Chatbot (CB11–CB16)
-- Proyecto : SWGACSGYM — Silver Gym Surco
-- Versión  : 1.0  |  Fecha: 2026-11-08
-- Autor    : generado por el agente a partir del diseño aprobado
-- ============================================================
-- REGLAS DE EJECUCIÓN
--   · Ejecutable más de una vez: CREATE TABLE / INDEX IF NOT EXISTS.
--   · PROHIBIDO en este archivo: DROP, DELETE, TRUNCATE, ALTER sobre
--     tablas existentes, INSERT de datos reales o de prueba.
--   · Sin credenciales, claves ni URLs.
-- ============================================================
-- TABLAS EXISTENTES REFERENCIADAS (no se recrean aquí)
--   · public."CLIENTES"(id_cliente BIGINT)  — módulo de Clientes
--   · auth.users(id UUID)                  — Supabase Auth (implícito vía JWT)
-- ============================================================
-- ORDEN DE CREACIÓN (respeta dependencias de FK)
--   1. chatbot_conversaciones
--   2. chatbot_mensajes
--   3. chatbot_rate_limit_contadores
--   4. chatbot_uso_tokens
--   5. chatbot_eventos_seguridad
--   6. chatbot_alertas_enviadas
-- ============================================================

BEGIN;

-- ============================================================
-- TABLA 1: chatbot_conversaciones
-- Registra cada sesión de conversación, su estado, el timestamp
-- de inactividad y la acción pendiente de confirmación del usuario.
-- Fuentes: EX-14, EX-15, HU-CB16, RN-10, [?-S1 DOC+PROPUESTA],
--          [?-F2 PROPUESTA-ACEPTADA], [?-N1 DECIDIDO]
-- ============================================================
CREATE TABLE IF NOT EXISTS public.chatbot_conversaciones (

    -- Identificador único de la conversación. Generado por el backend.
    -- Fuente: diseño general del módulo Chatbot
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- ID del cliente registrado en CLIENTES, resuelto por el backend
    -- a partir del JWT. NULL si el usuario es visitante (sin sesión).
    -- Fuente: RN-01, HU-CB11, [?-N1 DECIDIDO: public."CLIENTES"(id_cliente)]
    -- NOTA: ON DELETE SET NULL preserva el historial si el cliente se elimina.
    cliente_id BIGINT NULL
        REFERENCES public."CLIENTES"(id_cliente)
        ON DELETE SET NULL,

    -- Tipo de sujeto: derivado del JWT por el backend al iniciar la sesión.
    -- 'visitante' → sin JWT   |   'cliente' → JWT válido de cliente registrado
    -- Explicitado para consultas sin JOIN. Fuente: RN-01, RN-02, RN-03, HU-CB11
    tipo_sujeto TEXT NOT NULL,
    CONSTRAINT chk_conv_tipo_sujeto
        CHECK (tipo_sujeto IN ('visitante', 'cliente')),

    -- ID de sesión del navegador (cookie o localStorage).
    -- Complemento para identificar visitantes junto con la IP.
    -- Fuente: RN-10, [?-F3 DOCUMENTOS + PROPUESTA-ACEPTADA]
    sesion_navegador_id TEXT NULL,

    -- IP del cliente/visitante almacenada como HMAC-SHA256(ip_real, secreto).
    -- El secreto se lee de la variable de entorno CHATBOT_IP_HMAC_SECRET.
    -- NUNCA se almacena la IP en texto claro.
    -- Fuente: RN-10, Ley 29733 (Perú), [?-N2 DECIDIDO: HMAC-SHA256]
    ip_hmac TEXT NULL,

    -- Estado del ciclo de vida de la conversación.
    -- Fuente: EX-14, HU-CB16
    estado TEXT NOT NULL DEFAULT 'activa',
    CONSTRAINT chk_conv_estado
        CHECK (estado IN ('activa', 'cerrada', 'expirada_inactividad')),

    -- Marca de tiempo del último mensaje procesado por el backend.
    -- Controla el cierre por inactividad de 30 minutos (EX-14).
    -- Valor configurado en variable de entorno CHATBOT_INACTIVIDAD_MIN (default 30).
    -- Fuente: EX-14, RNF-CB07
    ultimo_mensaje_en TIMESTAMPTZ NULL,

    -- Acción pendiente de confirmación explícita por el usuario.
    -- Estructura JSON mínima: {"tipo": "inscripcion|carrito", "params": {...}}
    -- Sin datos sensibles (DNI, correo, teléfono, contraseñas). Fuente: RN-07.
    -- Fuente del requisito: EX-15, RN-06, [?-F2 PROPUESTA-ACEPTADA: sin reserva previa]
    -- [CONTRADICCIÓN ABIERTA] EX-15 y HU-CB16 mencionan cupo/stock "reservado",
    -- pero el diagrama de secuencia no muestra reserva antes de la confirmación.
    -- Sin reserva previa, solo se re-verifica cupo/stock al confirmar.
    accion_pendiente JSONB NULL,

    -- Momento en que se presentó la acción pendiente al usuario.
    -- Se usa para calcular la expiración de 5 minutos (EX-15).
    -- Valor configurado en variable de entorno CHATBOT_EXPIRACION_PENDIENTE_MIN (default 5).
    -- Fuente: EX-15, RNF-CB07
    accion_pendiente_desde TIMESTAMPTZ NULL,

    -- Timestamps de auditoría
    creado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    cerrado_en TIMESTAMPTZ NULL         -- Se rellena al pasar a 'cerrada' o 'expirada_inactividad'
);

-- Índice para buscar conversaciones activas de un cliente
-- Fuente: HU-CB11, HU-CB16
CREATE INDEX IF NOT EXISTS idx_chatbot_conv_cliente_id
    ON public.chatbot_conversaciones (cliente_id)
    WHERE cliente_id IS NOT NULL;

-- Índice para detectar conversaciones inactivas (job periódico CB16)
-- Fuente: EX-14, RNF-CB07
CREATE INDEX IF NOT EXISTS idx_chatbot_conv_estado_inactividad
    ON public.chatbot_conversaciones (estado, ultimo_mensaje_en);

-- Índice para detectar acciones pendientes expiradas (job periódico CB16)
-- Fuente: EX-15, RNF-CB07
CREATE INDEX IF NOT EXISTS idx_chatbot_conv_accion_pendiente
    ON public.chatbot_conversaciones (accion_pendiente_desde)
    WHERE accion_pendiente IS NOT NULL;


-- ============================================================
-- TABLA 2: chatbot_mensajes
-- Historial de mensajes de cada conversación.
-- RESTRICCIÓN CRÍTICA: sin datos sensibles en texto plano.
-- El backend enmascara antes de persistir. Fuente: RN-07, RN-08.
-- Fuentes: CUS30 Paso 9, HU-CB12 Esc.4, RN-07, RN-08, RN-11, HU-CB15
-- ============================================================
CREATE TABLE IF NOT EXISTS public.chatbot_mensajes (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Conversación a la que pertenece. ON DELETE CASCADE: si se elimina
    -- la conversación (limpieza), se eliminan sus mensajes.
    -- Fuente: HU-CB16, HU-CB12
    conversacion_id UUID NOT NULL
        REFERENCES public.chatbot_conversaciones(id)
        ON DELETE CASCADE,

    -- Rol del emisor del mensaje en la conversación.
    -- Fuente: CUS30 §7 Flujo principal
    rol TEXT NOT NULL,
    CONSTRAINT chk_msg_rol
        CHECK (rol IN ('usuario', 'asistente', 'sistema')),

    -- Contenido del mensaje.
    -- PROHIBIDO almacenar en este campo: DNI, correo, teléfono,
    -- contraseñas, datos de pago, o cualquier identificador completo.
    -- El backend aplica enmascaramiento antes de insertar.
    -- Fuente: RN-07, HU-CB12 Esc.2 y Esc.4
    contenido TEXT NOT NULL,

    -- Tokens consumidos por esta respuesta del asistente.
    -- Se obtiene del campo usage.total_tokens de la respuesta de la API de Groq.
    -- NULL para rol 'usuario' o 'sistema'. Fuente: RN-11, HU-CB15
    tokens_consumidos INTEGER NULL,
    CONSTRAINT chk_msg_tokens_positivo
        CHECK (tokens_consumidos IS NULL OR tokens_consumidos >= 0),

    -- Acción identificada en el mensaje (de la lista cerrada de CB13).
    -- Ejemplos: 'consulta_informacion', 'inscripcion_actividad',
    --           'cancelacion_inscripcion', 'solicitud_compra', 'derivacion'.
    -- NULL si el mensaje no contiene una acción estructurada.
    -- Fuente: RN-04, HU-CB13
    accion_detectada TEXT NULL,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice para recuperar el hilo de mensajes de una conversación en orden
-- Fuente: CUS30 §7 Paso 4 y 9
CREATE INDEX IF NOT EXISTS idx_chatbot_mensajes_conv_id
    ON public.chatbot_mensajes (conversacion_id, creado_en);


-- ============================================================
-- TABLA 3: chatbot_rate_limit_contadores
-- Contadores de mensajes por usuario/IP para hacer cumplir
-- los límites de frecuencia de CB14 (rate limiting).
-- Fuentes: HU-CB14, CUS30 RN-10, EX-04, RNF-CB07
-- ============================================================
-- [DIFERIDO-3] Ventanas fijas vs. deslizantes: se usan ventanas fijas
-- (truncadas a minuto/día UTC). Decisión pendiente del equipo.
-- [DIFERIDO-4] Incremento atómico: el backend debe usar
--   INSERT ... ON CONFLICT DO UPDATE SET contador = chatbot_rate_limit_contadores.contador + 1
--   para garantizar atomicidad bajo carga concurrente (RNF-CB06).
-- ============================================================
CREATE TABLE IF NOT EXISTS public.chatbot_rate_limit_contadores (

    -- Clave del sujeto controlado:
    --   · cliente  → bigint del id_cliente convertido a TEXT (ej. '42')
    --   · visitante → HMAC-SHA256(ip_real, CHATBOT_IP_HMAC_SECRET)
    -- Fuente: RN-10, [?-F3 DOCUMENTOS], [?-N2 DECIDIDO: HMAC-SHA256]
    clave TEXT NOT NULL,

    -- Tipo de sujeto al que pertenece la clave.
    -- Fuente: RN-10, HU-CB11
    tipo_sujeto TEXT NOT NULL,
    CONSTRAINT chk_rl_tipo_sujeto
        CHECK (tipo_sujeto IN ('cliente', 'visitante')),

    -- Tipo de ventana temporal.
    -- 'minuto' → límite por minuto (clientes: 10, visitantes: 5)
    -- 'dia'    → límite por día    (clientes: 100, visitantes: 20)
    -- Fuente: RN-10, EX-04, RNF-CB07
    ventana_tipo TEXT NOT NULL,
    CONSTRAINT chk_rl_ventana_tipo
        CHECK (ventana_tipo IN ('minuto', 'dia')),

    -- Inicio de la ventana temporal, truncada a minuto o a día (UTC).
    -- [DIFERIDO-2] Zona horaria: UTC por defecto. Ajustar si el gimnasio
    -- prefiere medianoche en America/Lima (UTC-5).
    -- Fuente: RN-10, EX-04
    ventana_inicio TIMESTAMPTZ NOT NULL,

    -- Número de mensajes registrados en esta ventana.
    -- Fuente: RN-10, EX-04
    contador INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT chk_rl_contador_positivo
        CHECK (contador >= 0),

    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Clave primaria compuesta: una fila por sujeto + tipo de ventana + período
    PRIMARY KEY (clave, tipo_sujeto, ventana_tipo, ventana_inicio)
);

-- Índice para limpieza de filas antiguas (job periódico, ver DIFERIDO-1)
-- Fuente: RNF-CB06 (escalabilidad), [DIFERIDO-1]
CREATE INDEX IF NOT EXISTS idx_rate_limit_ventana_inicio
    ON public.chatbot_rate_limit_contadores (ventana_inicio);


-- ============================================================
-- TABLA 4: chatbot_uso_tokens
-- Seguimiento del consumo diario de tokens por usuario y de forma
-- global (organización), para los controles de presupuesto de CB15.
-- Fuentes: HU-CB15, CUS30 RN-11, [?-V2 PROPUESTA-ACEPTADA],
--          [?-P3 PROPUESTA-ACEPTADA]
-- ============================================================
-- LÍMITES DE GROQ (plan gratuito openai/gpt-oss-120b, A VERIFICAR
-- en la consola de Groq antes de poner en producción):
--   30 RPM | 1.000 RPD | 8.000 TPM | 200.000 TPD (por organización)
-- Presupuesto interno = 90% del TPD real (configurado en CHATBOT_PRESUPUESTO_TPD).
-- Alerta al 80% del presupuesto interno → correo vía Resend ([?-P2 DECIDIDO]).
-- [DIFERIDO-4] Incremento atómico: igual que en chatbot_rate_limit_contadores.
-- ============================================================
CREATE TABLE IF NOT EXISTS public.chatbot_uso_tokens (

    -- Clave del sujeto:
    --   · cliente    → bigint del id_cliente como TEXT (ej. '42')
    --   · visitante  → HMAC-SHA256(ip_real, CHATBOT_IP_HMAC_SECRET)
    --   · global     → '__sistema__' (literal reservado para el total de la organización)
    -- Fuente: RN-11, HU-CB15 Esc.4, [?-V2 PROPUESTA-ACEPTADA], [?-P3]
    clave TEXT NOT NULL,

    -- Tipo de sujeto al que pertenece la clave.
    -- 'global' solo se usa con clave = '__sistema__'.
    -- Fuente: RN-11, HU-CB15
    tipo_sujeto TEXT NOT NULL,
    CONSTRAINT chk_ut_tipo_sujeto
        CHECK (tipo_sujeto IN ('cliente', 'visitante', 'global')),

    -- Día de acumulación (UTC).
    -- [DIFERIDO-2] Zona horaria: UTC por defecto.
    -- Fuente: RN-11
    fecha DATE NOT NULL,

    -- Total de tokens consumidos en el día para esta clave.
    -- Se incrementa con cada respuesta del LLM (campo usage.total_tokens de Groq).
    -- Topes por usuario ([?-V2 PROPUESTA-ACEPTADA], configurables por .env):
    --   · clientes:   8.000 tokens/día  → CHATBOT_TOPE_TOKENS_CLIENTE
    --   · visitantes: 3.000 tokens/día  → CHATBOT_TOPE_TOKENS_VISITANTE
    -- Fuente: RN-11, HU-CB15 Esc.4
    tokens_consumidos INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT chk_ut_tokens_positivo
        CHECK (tokens_consumidos >= 0),

    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (clave, tipo_sujeto, fecha)
);

-- Índice para consultas del presupuesto global del día actual
-- Fuente: HU-CB15, [?-P3 PROPUESTA-ACEPTADA]
CREATE INDEX IF NOT EXISTS idx_uso_tokens_global_fecha
    ON public.chatbot_uso_tokens (fecha, tipo_sujeto);


-- ============================================================
-- TABLA 5: chatbot_eventos_seguridad
-- Registro de auditoría de eventos de seguridad del chatbot.
-- Fuentes: HU-CB11 Esc.3, EX-13, [?-S3 PROPUESTA-ACEPTADA], RN-07
-- ============================================================
-- RESTRICCIÓN CRÍTICA: NO guardar en detalle el texto que el usuario
-- escribió ni el dato ajeno que solicitó. Fuente: RN-07, [?-S3].
-- ============================================================
CREATE TABLE IF NOT EXISTS public.chatbot_eventos_seguridad (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Conversación en la que ocurrió el evento.
    -- NULL si el JWT es inválido y no existe conversación activa.
    -- ON DELETE SET NULL: el registro de auditoría se conserva aunque
    -- la conversación se elimine en una limpieza posterior.
    -- Fuente: HU-CB11, EX-01, EX-13
    conversacion_id UUID NULL
        REFERENCES public.chatbot_conversaciones(id)
        ON DELETE SET NULL,

    -- ID del cliente SOLICITANTE (del JWT válido).
    -- NO es el ID del cliente objetivo cuyo dato fue pedido.
    -- Sin FK deliberada: el log de seguridad debe persistir aunque
    -- el cliente sea eliminado de CLIENTES. Fuente: RN-01, [?-S3]
    cliente_id BIGINT NULL,

    -- Tipo de sujeto del solicitante. NULL si el JWT es inválido.
    -- Fuente: RN-10, HU-CB11
    tipo_sujeto TEXT NULL,
    CONSTRAINT chk_es_tipo_sujeto
        CHECK (tipo_sujeto IS NULL OR tipo_sujeto IN ('cliente', 'visitante')),

    -- IP del solicitante como HMAC-SHA256(ip_real, CHATBOT_IP_HMAC_SECRET).
    -- Fuente: RN-10, [?-N2 DECIDIDO: HMAC-SHA256]
    ip_hmac TEXT NULL,

    -- Tipo de evento de seguridad (lista cerrada).
    -- Fuentes por evento:
    --   acceso_datos_tercero     → EX-13, HU-CB11 Esc.3
    --   jwt_invalido             → EX-01 (JWT malformado o firma inválida)
    --   jwt_expirado             → EX-01 (JWT expirado durante la conversación)
    --   accion_no_permitida      → EX-10, HU-CB13 Esc.2
    --   datos_sensibles_entrada  → HU-CB12 Esc.2 (usuario escribe contraseña/pago)
    --   limite_mensajes_superado → EX-04, HU-CB14
    --   limite_tokens_superado   → HU-CB15 Esc.3 y Esc.4
    tipo_evento TEXT NOT NULL,
    CONSTRAINT chk_es_tipo_evento
        CHECK (tipo_evento IN (
            'acceso_datos_tercero',
            'jwt_invalido',
            'jwt_expirado',
            'accion_no_permitida',
            'datos_sensibles_entrada',
            'limite_mensajes_superado',
            'limite_tokens_superado'
        )),

    -- Detalle estructurado del evento en JSON.
    -- PROHIBIDO incluir: texto del usuario, dato ajeno solicitado, DNI,
    -- correo, teléfono o cualquier identificador completo. Fuente: RN-07.
    -- Ejemplo permitido: {"accion_pedida": "modificar_membresia", "en_lista_cerrada": false}
    detalle JSONB NULL,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice para consultas de auditoría por tipo de evento y fecha
-- Fuente: [?-S3 PROPUESTA-ACEPTADA]
CREATE INDEX IF NOT EXISTS idx_eventos_seg_tipo
    ON public.chatbot_eventos_seguridad (tipo_evento, creado_en);

-- Índice para relacionar eventos con su conversación
-- Fuente: HU-CB11, EX-13
CREATE INDEX IF NOT EXISTS idx_eventos_seg_conv
    ON public.chatbot_eventos_seguridad (conversacion_id)
    WHERE conversacion_id IS NOT NULL;


-- ============================================================
-- TABLA 6: chatbot_alertas_enviadas
-- Registro de alertas de presupuesto enviadas por correo (Resend).
-- Garantiza un solo envío por tipo de alerta y por día.
-- Fuentes: HU-CB15 Esc.2 y Esc.3, EX-03, [?-P2 DECIDIDO], [?-N3 DECIDIDO]
-- ============================================================
-- Configuración de Resend (variables de entorno, nunca en BD):
--   RESEND_API_KEY          → API key de Resend
--   CHATBOT_ALERT_EMAIL_TO  → destinatario/s de la alerta
--   CHATBOT_ALERT_EMAIL_FROM → remitente verificado en Resend
-- Si Resend falla, el chat NO se interrumpe y el error queda en logs.
-- Fuente: [?-P2 DECIDIDO]
-- ============================================================
CREATE TABLE IF NOT EXISTS public.chatbot_alertas_enviadas (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Tipo de alerta:
    --   'umbral_80' → se alcanzó el 80% del presupuesto interno diario (HU-CB15 Esc.2)
    --   'tope_100'  → se alcanzó el 100% → modo básico activado (EX-03, HU-CB15 Esc.3)
    -- Fuente: HU-CB15, [?-P2 DECIDIDO], [?-N3 DECIDIDO]
    tipo_alerta TEXT NOT NULL,
    CONSTRAINT chk_aa_tipo_alerta
        CHECK (tipo_alerta IN ('umbral_80', 'tope_100')),

    -- Día en que se registra la alerta (UTC).
    -- Junto con tipo_alerta forma la clave única: máximo un envío por tipo y por día.
    -- Fuente: [?-P2 DECIDIDO]
    fecha DATE NOT NULL,

    -- Indica si Resend procesó el envío correctamente.
    -- false → el chat no se interrumpe; el error queda en logs del backend.
    -- Fuente: [?-P2 DECIDIDO]
    exito BOOLEAN NOT NULL,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Un solo registro por tipo de alerta por día (deduplicación)
    CONSTRAINT uq_alerta_tipo_fecha UNIQUE (tipo_alerta, fecha)
);


-- ============================================================
-- SECCIÓN: Diferido / pendiente
-- Estos puntos quedan fuera del presente script DDL y deben
-- resolverse antes de poner el sistema en producción.
-- ============================================================
-- [DIFERIDO-1] Limpieza de filas antiguas en chatbot_rate_limit_contadores:
--   Implementar un job periódico (pg_cron, Supabase Edge Functions o tarea
--   del backend) que ejecute:
--     DELETE FROM public.chatbot_rate_limit_contadores
--      WHERE ventana_inicio < now() - interval '2 days';
--   No se incluye aquí para no ejecutar DELETE en el script de creación.
--
-- [DIFERIDO-2] Zona horaria de la ventana diaria:
--   Las columnas fecha (DATE) y ventana_inicio (TIMESTAMPTZ) se gestionan
--   en UTC por defecto. Si el gimnasio requiere que la ventana diaria
--   coincida con la medianoche en America/Lima (UTC-5), el backend debe
--   truncar con date_trunc('day', now() AT TIME ZONE 'America/Lima').
--   Decisión pendiente del equipo.
--
-- [DIFERIDO-3] Ventanas fijas vs. ventanas deslizantes:
--   El diseño actual usa ventanas fijas (truncadas a minuto/día UTC).
--   Una ventana deslizante ("últimos 60 segundos") requiere otro enfoque
--   de almacenamiento. Decisión pendiente si el equipo lo requiere.
--
-- [DIFERIDO-4] Incremento atómico de contadores:
--   Para chatbot_rate_limit_contadores y chatbot_uso_tokens, el backend
--   debe usar INSERT ... ON CONFLICT DO UPDATE SET contador = tabla.contador + 1
--   (o tokens_consumidos = tabla.tokens_consumidos + delta) para garantizar
--   atomicidad bajo carga concurrente (RNF-CB06). Esto es responsabilidad
--   del código FastAPI, no de este script DDL.
--
-- [DIFERIDO-5] Retención del historial:
--   Plazo propuesto: 30 días para chatbot_mensajes y chatbot_eventos_seguridad
--   ([?-S1 PROPUESTA provisional]). Valor final pendiente de decisión del equipo.
--   Implementar con job periódico (no incluido en este script).
--
-- [DIFERIDO-6] Rol del backend en Supabase [?]:
--   El rol con el que FastAPI se conecta a Supabase no está definido en los
--   documentos. Ver 03_rls_propuesta.sql para opciones y recomendaciones.
-- ============================================================

COMMIT;
