-- ============================================================
-- 02_validar_tablas.sql
-- Validación de las 6 tablas chatbot_* creadas en 01_crear_tablas.sql
-- ============================================================
-- INSTRUCCIONES:
--   1. Ejecutar DESPUÉS de 01_crear_tablas.sql.
--   2. Ejecutar cada bloque numerado por separado (copiar y pegar
--      uno a la vez en el SQL Editor de Supabase).
--   3. Cada consulta devuelve una columna "ok" (true/false) por fila.
--   4. Si alguna devuelve ok = false, ver las instrucciones al pie.
-- ============================================================
-- Solo SELECT sobre information_schema y pg_catalog.
-- Sin modificaciones de datos ni estructura.
-- ============================================================


-- ============================================================
-- C01: Existencia de las 6 tablas chatbot_*
-- Esperado: 6 filas, todas con ok = true
-- ============================================================
SELECT
    t.tabla                                              AS tabla,
    EXISTS (
        SELECT 1
        FROM   information_schema.tables
        WHERE  table_schema = 'public'
          AND  table_name   = t.tabla
    )                                                    AS ok
FROM (VALUES
    ('chatbot_conversaciones'),
    ('chatbot_mensajes'),
    ('chatbot_rate_limit_contadores'),
    ('chatbot_uso_tokens'),
    ('chatbot_eventos_seguridad'),
    ('chatbot_alertas_enviadas')
) AS t(tabla)
ORDER BY tabla;


-- ============================================================
-- C02: Columnas de chatbot_conversaciones (tipo y nulabilidad)
-- Esperado: 11 filas, todas con ok = true
-- ============================================================
SELECT
    exp.columna                                          AS columna,
    exp.tipo_esperado                                    AS tipo_esperado,
    exp.nulable_esperado                                 AS nulable_esperado,
    c.data_type                                          AS tipo_encontrado,
    c.is_nullable                                        AS nulable_encontrado,
    (
        c.column_name    IS NOT NULL
        AND c.data_type  = exp.tipo_esperado
        AND c.is_nullable = exp.nulable_esperado
    )                                                    AS ok
FROM (VALUES
    ('id',                       'uuid',                       'NO'),
    ('cliente_id',               'bigint',                     'YES'),
    ('tipo_sujeto',              'text',                       'NO'),
    ('sesion_navegador_id',      'text',                       'YES'),
    ('ip_hmac',                  'text',                       'YES'),
    ('estado',                   'text',                       'NO'),
    ('ultimo_mensaje_en',        'timestamp with time zone',   'YES'),
    ('accion_pendiente',         'jsonb',                      'YES'),
    ('accion_pendiente_desde',   'timestamp with time zone',   'YES'),
    ('creado_en',                'timestamp with time zone',   'NO'),
    ('cerrado_en',               'timestamp with time zone',   'YES')
) AS exp(columna, tipo_esperado, nulable_esperado)
LEFT JOIN information_schema.columns c
    ON  c.table_schema = 'public'
    AND c.table_name   = 'chatbot_conversaciones'
    AND c.column_name  = exp.columna
ORDER BY exp.columna;


-- ============================================================
-- C03: Columnas de chatbot_mensajes (tipo y nulabilidad)
-- Esperado: 7 filas, todas con ok = true
-- ============================================================
SELECT
    exp.columna                                          AS columna,
    exp.tipo_esperado                                    AS tipo_esperado,
    exp.nulable_esperado                                 AS nulable_esperado,
    c.data_type                                          AS tipo_encontrado,
    c.is_nullable                                        AS nulable_encontrado,
    (
        c.column_name    IS NOT NULL
        AND c.data_type  = exp.tipo_esperado
        AND c.is_nullable = exp.nulable_esperado
    )                                                    AS ok
FROM (VALUES
    ('id',                 'uuid',                      'NO'),
    ('conversacion_id',    'uuid',                      'NO'),
    ('rol',                'text',                      'NO'),
    ('contenido',          'text',                      'NO'),
    ('tokens_consumidos',  'integer',                   'YES'),
    ('accion_detectada',   'text',                      'YES'),
    ('creado_en',          'timestamp with time zone',  'NO')
) AS exp(columna, tipo_esperado, nulable_esperado)
LEFT JOIN information_schema.columns c
    ON  c.table_schema = 'public'
    AND c.table_name   = 'chatbot_mensajes'
    AND c.column_name  = exp.columna
ORDER BY exp.columna;


-- ============================================================
-- C04: Columnas de chatbot_rate_limit_contadores (tipo y nulabilidad)
-- Esperado: 6 filas, todas con ok = true
-- ============================================================
SELECT
    exp.columna                                          AS columna,
    exp.tipo_esperado                                    AS tipo_esperado,
    exp.nulable_esperado                                 AS nulable_esperado,
    c.data_type                                          AS tipo_encontrado,
    c.is_nullable                                        AS nulable_encontrado,
    (
        c.column_name    IS NOT NULL
        AND c.data_type  = exp.tipo_esperado
        AND c.is_nullable = exp.nulable_esperado
    )                                                    AS ok
FROM (VALUES
    ('clave',          'text',                      'NO'),
    ('tipo_sujeto',    'text',                      'NO'),
    ('ventana_tipo',   'text',                      'NO'),
    ('ventana_inicio', 'timestamp with time zone',  'NO'),
    ('contador',       'integer',                   'NO'),
    ('actualizado_en', 'timestamp with time zone',  'NO')
) AS exp(columna, tipo_esperado, nulable_esperado)
LEFT JOIN information_schema.columns c
    ON  c.table_schema = 'public'
    AND c.table_name   = 'chatbot_rate_limit_contadores'
    AND c.column_name  = exp.columna
ORDER BY exp.columna;


-- ============================================================
-- C05: Columnas de chatbot_uso_tokens (tipo y nulabilidad)
-- Esperado: 5 filas, todas con ok = true
-- ============================================================
SELECT
    exp.columna                                          AS columna,
    exp.tipo_esperado                                    AS tipo_esperado,
    exp.nulable_esperado                                 AS nulable_esperado,
    c.data_type                                          AS tipo_encontrado,
    c.is_nullable                                        AS nulable_encontrado,
    (
        c.column_name    IS NOT NULL
        AND c.data_type  = exp.tipo_esperado
        AND c.is_nullable = exp.nulable_esperado
    )                                                    AS ok
FROM (VALUES
    ('clave',              'text',                      'NO'),
    ('tipo_sujeto',        'text',                      'NO'),
    ('fecha',              'date',                      'NO'),
    ('tokens_consumidos',  'integer',                   'NO'),
    ('actualizado_en',     'timestamp with time zone',  'NO')
) AS exp(columna, tipo_esperado, nulable_esperado)
LEFT JOIN information_schema.columns c
    ON  c.table_schema = 'public'
    AND c.table_name   = 'chatbot_uso_tokens'
    AND c.column_name  = exp.columna
ORDER BY exp.columna;


-- ============================================================
-- C06: Columnas de chatbot_eventos_seguridad (tipo y nulabilidad)
-- Esperado: 8 filas, todas con ok = true
-- ============================================================
SELECT
    exp.columna                                          AS columna,
    exp.tipo_esperado                                    AS tipo_esperado,
    exp.nulable_esperado                                 AS nulable_esperado,
    c.data_type                                          AS tipo_encontrado,
    c.is_nullable                                        AS nulable_encontrado,
    (
        c.column_name    IS NOT NULL
        AND c.data_type  = exp.tipo_esperado
        AND c.is_nullable = exp.nulable_esperado
    )                                                    AS ok
FROM (VALUES
    ('id',               'uuid',                      'NO'),
    ('conversacion_id',  'uuid',                      'YES'),
    ('cliente_id',       'bigint',                    'YES'),
    ('tipo_sujeto',      'text',                      'YES'),
    ('ip_hmac',          'text',                      'YES'),
    ('tipo_evento',      'text',                      'NO'),
    ('detalle',          'jsonb',                     'YES'),
    ('creado_en',        'timestamp with time zone',  'NO')
) AS exp(columna, tipo_esperado, nulable_esperado)
LEFT JOIN information_schema.columns c
    ON  c.table_schema = 'public'
    AND c.table_name   = 'chatbot_eventos_seguridad'
    AND c.column_name  = exp.columna
ORDER BY exp.columna;


-- ============================================================
-- C07: Columnas de chatbot_alertas_enviadas (tipo y nulabilidad)
-- Esperado: 5 filas, todas con ok = true
-- ============================================================
SELECT
    exp.columna                                          AS columna,
    exp.tipo_esperado                                    AS tipo_esperado,
    exp.nulable_esperado                                 AS nulable_esperado,
    c.data_type                                          AS tipo_encontrado,
    c.is_nullable                                        AS nulable_encontrado,
    (
        c.column_name    IS NOT NULL
        AND c.data_type  = exp.tipo_esperado
        AND c.is_nullable = exp.nulable_esperado
    )                                                    AS ok
FROM (VALUES
    ('id',          'uuid',                      'NO'),
    ('tipo_alerta', 'text',                      'NO'),
    ('fecha',       'date',                      'NO'),
    ('exito',       'boolean',                   'NO'),
    ('creado_en',   'timestamp with time zone',  'NO')
) AS exp(columna, tipo_esperado, nulable_esperado)
LEFT JOIN information_schema.columns c
    ON  c.table_schema = 'public'
    AND c.table_name   = 'chatbot_alertas_enviadas'
    AND c.column_name  = exp.columna
ORDER BY exp.columna;


-- ============================================================
-- C08: Claves primarias de las 6 tablas (incluidas las compuestas)
-- Esperado: 6 filas, todas con ok = true
-- La columna columnas_pk muestra las columnas que forman la PK,
-- separadas por coma, en orden de posición.
-- ============================================================
SELECT
    exp.tabla                                            AS tabla,
    exp.pk_esperada                                      AS pk_esperada,
    string_agg(kcu.column_name, ', '
               ORDER BY kcu.ordinal_position)            AS pk_encontrada,
    string_agg(kcu.column_name, ', '
               ORDER BY kcu.ordinal_position)
        = exp.pk_esperada                                AS ok
FROM (VALUES
    ('chatbot_conversaciones',          'id'),
    ('chatbot_mensajes',                'id'),
    ('chatbot_rate_limit_contadores',   'clave, tipo_sujeto, ventana_tipo, ventana_inicio'),
    ('chatbot_uso_tokens',              'clave, tipo_sujeto, fecha'),
    ('chatbot_eventos_seguridad',       'id'),
    ('chatbot_alertas_enviadas',        'id')
) AS exp(tabla, pk_esperada)
LEFT JOIN information_schema.table_constraints tc
    ON  tc.table_schema    = 'public'
    AND tc.table_name      = exp.tabla
    AND tc.constraint_type = 'PRIMARY KEY'
LEFT JOIN information_schema.key_column_usage kcu
    ON  kcu.constraint_schema = tc.constraint_schema
    AND kcu.constraint_name   = tc.constraint_name
GROUP BY exp.tabla, exp.pk_esperada
ORDER BY exp.tabla;


-- ============================================================
-- C09: Claves foráneas y sus tablas de destino
-- Esperado: 3 filas, todas con ok = true
-- ============================================================
SELECT
    kcu.table_name                                       AS tabla_origen,
    kcu.column_name                                      AS columna_origen,
    ccu.table_name                                       AS tabla_destino,
    ccu.column_name                                      AS columna_destino,
    (
           kcu.table_name   = exp.tabla_origen
       AND kcu.column_name  = exp.columna_origen
       AND ccu.table_name   = exp.tabla_destino
       AND ccu.column_name  = exp.columna_destino
    )                                                    AS ok
FROM (VALUES
    ('chatbot_conversaciones', 'cliente_id',    'CLIENTES',               'id_cliente'),
    ('chatbot_mensajes',       'conversacion_id','chatbot_conversaciones', 'id'),
    ('chatbot_eventos_seguridad','conversacion_id','chatbot_conversaciones','id')
) AS exp(tabla_origen, columna_origen, tabla_destino, columna_destino)
LEFT JOIN information_schema.referential_constraints rc
    ON rc.constraint_schema = 'public'
LEFT JOIN information_schema.key_column_usage kcu
    ON  kcu.constraint_schema = rc.constraint_schema
    AND kcu.constraint_name   = rc.constraint_name
    AND kcu.table_name        = exp.tabla_origen
    AND kcu.column_name       = exp.columna_origen
LEFT JOIN information_schema.constraint_column_usage ccu
    ON  ccu.constraint_schema = rc.unique_constraint_schema
    AND ccu.constraint_name   = rc.unique_constraint_name
    AND ccu.table_name        = exp.tabla_destino
    AND ccu.column_name       = exp.columna_destino
ORDER BY exp.tabla_origen;


-- ============================================================
-- C10: Restricciones CHECK nombradas (12 en total)
-- Esperado: 12 filas, todas con ok = true
-- ============================================================
SELECT
    exp.nombre                                           AS constraint_esperado,
    EXISTS (
        SELECT 1
        FROM   pg_catalog.pg_constraint pc
        JOIN   pg_catalog.pg_class      cl ON cl.oid = pc.conrelid
        JOIN   pg_catalog.pg_namespace  ns ON ns.oid = cl.relnamespace
        WHERE  ns.nspname = 'public'
          AND  cl.relname LIKE 'chatbot_%'
          AND  pc.contype = 'c'
          AND  pc.conname = exp.nombre
    )                                                    AS ok
FROM (VALUES
    ('chk_conv_tipo_sujeto'),
    ('chk_conv_estado'),
    ('chk_msg_rol'),
    ('chk_msg_tokens_positivo'),
    ('chk_rl_tipo_sujeto'),
    ('chk_rl_ventana_tipo'),
    ('chk_rl_contador_positivo'),
    ('chk_ut_tipo_sujeto'),
    ('chk_ut_tokens_positivo'),
    ('chk_es_tipo_sujeto'),
    ('chk_es_tipo_evento'),
    ('chk_aa_tipo_alerta')
) AS exp(nombre)
ORDER BY exp.nombre;


-- ============================================================
-- C11: Restricción UNIQUE en chatbot_alertas_enviadas
-- Esperado: 1 fila con ok = true
-- ============================================================
SELECT
    'uq_alerta_tipo_fecha'                               AS constraint_esperado,
    EXISTS (
        SELECT 1
        FROM   information_schema.table_constraints
        WHERE  table_schema     = 'public'
          AND  table_name       = 'chatbot_alertas_enviadas'
          AND  constraint_name  = 'uq_alerta_tipo_fecha'
          AND  constraint_type  = 'UNIQUE'
    )                                                    AS ok;


-- ============================================================
-- C12: Índices nombrados explícitamente (8 en total)
-- Esperado: 8 filas, todas con ok = true
-- ============================================================
SELECT
    exp.indice                                           AS indice_esperado,
    EXISTS (
        SELECT 1
        FROM   pg_catalog.pg_indexes
        WHERE  schemaname = 'public'
          AND  indexname  = exp.indice
    )                                                    AS ok
FROM (VALUES
    ('idx_chatbot_conv_cliente_id'),
    ('idx_chatbot_conv_estado_inactividad'),
    ('idx_chatbot_conv_accion_pendiente'),
    ('idx_chatbot_mensajes_conv_id'),
    ('idx_rate_limit_ventana_inicio'),
    ('idx_uso_tokens_global_fecha'),
    ('idx_eventos_seg_tipo'),
    ('idx_eventos_seg_conv')
) AS exp(indice)
ORDER BY exp.indice;


-- ============================================================
-- C13: Resumen final — recuento de objetos creados
-- Esperado: todas las columnas ok_* = true y fallos = 0
-- ============================================================
SELECT
    -- Tablas
    (SELECT COUNT(*) FROM information_schema.tables
     WHERE  table_schema = 'public'
       AND  table_name IN (
            'chatbot_conversaciones','chatbot_mensajes',
            'chatbot_rate_limit_contadores','chatbot_uso_tokens',
            'chatbot_eventos_seguridad','chatbot_alertas_enviadas'
       ))                                                AS tablas_encontradas,
    6                                                    AS tablas_esperadas,
    (SELECT COUNT(*) FROM information_schema.tables
     WHERE  table_schema = 'public'
       AND  table_name IN (
            'chatbot_conversaciones','chatbot_mensajes',
            'chatbot_rate_limit_contadores','chatbot_uso_tokens',
            'chatbot_eventos_seguridad','chatbot_alertas_enviadas'
       )) = 6                                            AS ok_tablas,

    -- Índices nombrados
    (SELECT COUNT(*) FROM pg_catalog.pg_indexes
     WHERE  schemaname = 'public'
       AND  indexname IN (
            'idx_chatbot_conv_cliente_id',
            'idx_chatbot_conv_estado_inactividad',
            'idx_chatbot_conv_accion_pendiente',
            'idx_chatbot_mensajes_conv_id',
            'idx_rate_limit_ventana_inicio',
            'idx_uso_tokens_global_fecha',
            'idx_eventos_seg_tipo',
            'idx_eventos_seg_conv'
       ))                                                AS indices_encontrados,
    8                                                    AS indices_esperados,
    (SELECT COUNT(*) FROM pg_catalog.pg_indexes
     WHERE  schemaname = 'public'
       AND  indexname IN (
            'idx_chatbot_conv_cliente_id',
            'idx_chatbot_conv_estado_inactividad',
            'idx_chatbot_conv_accion_pendiente',
            'idx_chatbot_mensajes_conv_id',
            'idx_rate_limit_ventana_inicio',
            'idx_uso_tokens_global_fecha',
            'idx_eventos_seg_tipo',
            'idx_eventos_seg_conv'
       )) = 8                                            AS ok_indices,

    -- CHECK constraints nombrados
    (SELECT COUNT(*)
     FROM   pg_catalog.pg_constraint pc
     JOIN   pg_catalog.pg_class      cl ON cl.oid = pc.conrelid
     JOIN   pg_catalog.pg_namespace  ns ON ns.oid = cl.relnamespace
     WHERE  ns.nspname = 'public'
       AND  cl.relname LIKE 'chatbot_%'
       AND  pc.contype = 'c'
       AND  pc.conname IN (
            'chk_conv_tipo_sujeto','chk_conv_estado',
            'chk_msg_rol','chk_msg_tokens_positivo',
            'chk_rl_tipo_sujeto','chk_rl_ventana_tipo','chk_rl_contador_positivo',
            'chk_ut_tipo_sujeto','chk_ut_tokens_positivo',
            'chk_es_tipo_sujeto','chk_es_tipo_evento',
            'chk_aa_tipo_alerta'
       ))                                                AS checks_encontrados,
    12                                                   AS checks_esperados,
    (SELECT COUNT(*)
     FROM   pg_catalog.pg_constraint pc
     JOIN   pg_catalog.pg_class      cl ON cl.oid = pc.conrelid
     JOIN   pg_catalog.pg_namespace  ns ON ns.oid = cl.relnamespace
     WHERE  ns.nspname = 'public'
       AND  cl.relname LIKE 'chatbot_%'
       AND  pc.contype = 'c'
       AND  pc.conname IN (
            'chk_conv_tipo_sujeto','chk_conv_estado',
            'chk_msg_rol','chk_msg_tokens_positivo',
            'chk_rl_tipo_sujeto','chk_rl_ventana_tipo','chk_rl_contador_positivo',
            'chk_ut_tipo_sujeto','chk_ut_tokens_positivo',
            'chk_es_tipo_sujeto','chk_es_tipo_evento',
            'chk_aa_tipo_alerta'
       )) = 12                                           AS ok_checks,

    -- Número total de fallos (columnas ok_* = false)
    (
        CASE WHEN (SELECT COUNT(*) FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name IN (
                         'chatbot_conversaciones','chatbot_mensajes',
                         'chatbot_rate_limit_contadores','chatbot_uso_tokens',
                         'chatbot_eventos_seguridad','chatbot_alertas_enviadas'
                     )) <> 6 THEN 1 ELSE 0 END
      + CASE WHEN (SELECT COUNT(*) FROM pg_catalog.pg_indexes
                   WHERE schemaname='public'
                     AND indexname IN (
                         'idx_chatbot_conv_cliente_id','idx_chatbot_conv_estado_inactividad',
                         'idx_chatbot_conv_accion_pendiente','idx_chatbot_mensajes_conv_id',
                         'idx_rate_limit_ventana_inicio','idx_uso_tokens_global_fecha',
                         'idx_eventos_seg_tipo','idx_eventos_seg_conv'
                     )) <> 8 THEN 1 ELSE 0 END
      + CASE WHEN (SELECT COUNT(*)
                   FROM pg_catalog.pg_constraint pc
                   JOIN pg_catalog.pg_class cl ON cl.oid = pc.conrelid
                   JOIN pg_catalog.pg_namespace ns ON ns.oid = cl.relnamespace
                   WHERE ns.nspname='public' AND cl.relname LIKE 'chatbot_%'
                     AND pc.contype = 'c'
                     AND pc.conname IN (
                         'chk_conv_tipo_sujeto','chk_conv_estado',
                         'chk_msg_rol','chk_msg_tokens_positivo',
                         'chk_rl_tipo_sujeto','chk_rl_ventana_tipo','chk_rl_contador_positivo',
                         'chk_ut_tipo_sujeto','chk_ut_tokens_positivo',
                         'chk_es_tipo_sujeto','chk_es_tipo_evento','chk_aa_tipo_alerta'
                     )) <> 12 THEN 1 ELSE 0 END
    )                                                    AS fallos_totales;


-- ============================================================
-- QUÉ HACER SI ALGUNA COMPROBACIÓN DEVUELVE ok = false
-- ============================================================
-- 1. Identifica qué fila falló (columna "tabla", "columna" o "indice").
-- 2. Verifica que ejecutaste 01_crear_tablas.sql completo y que
--    el bloque BEGIN/COMMIT finalizó sin errores.
-- 3. Si el error es de tipo o nulabilidad, revisa si Supabase aplicó
--    alguna transformación automática de tipos (raro, pero posible con UUID).
-- 4. Si falla C09 (FK a "CLIENTES"), confirma que la tabla public."CLIENTES"
--    existe y que id_cliente es BIGINT con restricción PK o UNIQUE.
-- 5. Si falla C10 (CHECK constraints), el nombre del constraint puede no
--    coincidir si PostgreSQL lo renombró. Ejecuta:
--      SELECT conname, conrelid::regclass
--      FROM   pg_catalog.pg_constraint
--      WHERE  contype = 'c'
--        AND  conrelid::regclass::text LIKE 'chatbot_%';
--    para ver los nombres reales, y avisame.
-- 6. No modifiques nada por tu cuenta: comparte el resultado con ok = false
--    y yo entrego un script de ajuste puntual.
-- ============================================================
