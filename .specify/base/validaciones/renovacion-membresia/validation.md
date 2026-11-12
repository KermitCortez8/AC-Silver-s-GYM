# Validación de recompra de membresía

Fecha: 2026-11-09. Implementación directa por petición del usuario, sin activar
Spec Kit ni generar especificaciones, planes o tareas.

## Comportamiento comprobado

- Avisos de últimos tres días y vencimiento con fecha de Perú; se omiten membresías
  anteriores que ya tienen una renovación posterior pagada.
- Enlace personal firmado, ventana temporal, rechazo de alteraciones y detalle
  público sin información personal ni necesidad de sesión activa.
- Resumen previo al pago, precio actual del mismo plan sin promoción heredada,
  importe pendiente conservado, rechazo de precios discrepantes y reutilización
  transaccional de una membresía pendiente ante peticiones concurrentes.
- Sesión Stripe abierta reutilizable; otro intento solo si expiró; bloqueo de
  sesiones completas por conciliar y de renovaciones ya pagadas.
- El pago anticipado conserva el acceso de la membresía todavía vigente.
  La activación administrativa y las fechas anteriores se conservan.

## Ejecuciones

- Suite backend: `AUTH_SECRET_KEY=<valor sintético de más de 32 bytes> python -m
  pytest tests/ -q`, desde backend: **702 aprobadas, 44 omitidas**. Incluye las
  primeras cuatro regresiones de renovación. La primera ejecución sin configurar
  la clave falló en ocho pruebas de sesión; se repitió con una clave de prueba.
- Regresión backend final: `python -m pytest backend/tests/membresias_pagos/integracion/test_membership_renewal.py
  -q`: **7 aprobadas**, incluidas tres verificaciones adicionales de API pública,
  sesión Stripe previa y acceso durante renovación anticipada.
- PostgreSQL 16 Alpine desechable, contenedor `gym-renewal-sql-test`, base
  `gym_test`: `GYM_TEST_POSTGRES_CONTAINER=gym-renewal-sql-test python -m pytest
  backend/tests/notificaciones/postgres/test_membership_renewal_postgres.py -q`: **2 aprobadas**.
  Comprueba 004 + 024, repetición de 024, deduplicación y reclamación de avisos,
  tipos de evento y denegación a roles anon/authenticated. El contenedor se elimina
  al terminar; no se conecta a Supabase ni a una base compartida.
- `npm test`, desde frontend: **353 aprobadas** de la suite previa.
- Regresión frontend final: `node --test frontend/tests/clientes/interfaz/client-flow-control.test.js
  frontend/tests/membresias_pagos/interfaz/membership-renewal.test.js`: **15 aprobadas**, incluidas las
  cuatro nuevas de renovación. Comprueba detalle sin cobro, enlace ausente,
  precio desactualizado, renovación ya pagada y descarte de respuestas anteriores.
- `npm run build`, desde frontend: **correcto** después de los cambios finales.
- Flake8 E9/F63/F7/F82: **0 errores**.
- `python -B -m unittest discover -s .specify/tests -v`: **13 aprobadas**.
- Validador documental global y `git diff --check`: **correctos**.

## Evidencia visual

Revisión con Chromium/Playwright, API simulada y datos ficticios:
[escritorio](escritorio.png) de 1440 px y [móvil](movil.png) de 390 px.
Se revisaron jerarquía, legibilidad y ausencia de desbordamiento horizontal.
La automatización comprobó que no se inicia checkout al cargar, que el botón
redirige una sola vez y que el enlace incompleto presenta un error recuperable.
El retorno de cancelación está configurado en el adaptador Stripe para volver
al resumen personal; no se abrió ni se cobró una sesión real del proveedor.

## Límites y habilitación

La suite general omitió 44 pruebas PostgreSQL que exigen un entorno específico;
la migración nueva sí se probó por separado en PostgreSQL desechable. No se
realizaron envíos Resend, cobros Stripe ni despliegues reales. Los proveedores
se verificaron con dobles y se reutilizaron sus adaptadores actuales.

Para habilitar en un entorno desplegado: aplicar 024 después de 004, configurar
`AUTH_SECRET_KEY`, `FRONTEND_PUBLIC_URL`, Stripe, Supabase y Resend, y desplegar
frontend/backend. El proceso del backend debe permanecer ejecutándose para
preparar y enviar los avisos. Las compras requieren activación administrativa;
la fecha nueva comienza al activar, según el comportamiento existente.

## Prueba operativa posterior autorizada · 2026-11-09

Por petición explícita del usuario se creó una cuenta de prueba en la base
configurada, con datos de nombre/DNI/teléfono ficticios y el destinatario indicado
por el usuario. No se incorporan el correo, contraseña ni enlaces personales a
este documento. Se comprobó Stripe en modo test y el dominio remitente verificado.

El navegador recorrió registro público, Stripe Checkout con tarjeta oficial de
prueba y retorno a «Pago confirmado» del plan mensual por S/ 80. El servicio de
aplicación activó la membresía y se comprobó el acceso real al panel de usuario.
Se simularon fechas pasadas solo para esa membresía mediante un comando atómico
y la regla de vencimiento existente, conservando el pago. El acceso posterior
respondió `403 membership_expired`; el enlace personal abrió el resumen de recompra
sin sesión. No se inició una segunda compra; la cuenta queda vencida para que el
usuario pruebe la renovación.

Resend devolvió ID para pago, activación y vencimiento; la consulta posterior de
los tres mensajes devolvió `last_event=delivered`. Esto acredita entrega según
el proveedor, sin afirmar lectura ni ubicación en la bandeja principal. Los correos
sí fueron reales en esta prueba posterior; el pago fue exclusivamente de prueba,
sin movimiento de dinero real. El enlace enviado utiliza la URL frontend configurada
para este entorno local. No se ejecutaron cambios de despliegue ni de configuración.

## Corrección de regla y directorio · 2026-11-09

El usuario precisó que la activación administrativa corresponde únicamente a la
primera membresía. Esta regla sustituye las menciones de activación manual de
renovaciones en las comprobaciones iniciales de este documento.

- Al confirmar Stripe o caja, el dominio busca una membresía anterior pagada y
  activada (activa o vencida con fechas). Una simple compra pendiente o pagada
  sin activación inicial no permite eludir la primera activación.
- El pago y la activación de una renovación se guardan en la misma transacción.
  Una renovación vencida empieza hoy; una anticipada empieza al día siguiente
  del último día inclusivo anterior. Se mantiene el cálculo existente del fin
  como inicio más duración. No cambia las fechas ni el pago anteriores.
- La confirmación repetida conserva las fechas; no vuelve a activar una membresía
  vencida. Una renovación pagada en trámite de la versión anterior puede
  conciliarse revalidando su sesión Stripe, sin crear otro checkout o cobro.
- El retorno y el correo de pago informan la activación automática según el
  estado confirmado por el servidor. El registro inicial conserva la aprobación.
- Clientes fuerza la consulta al abrirse y usa el refresco visible existente cada
  treinta segundos y al recuperar foco, sin interrumpir editores o detalles abiertos.

Se detectó en la cuenta de prueba una renovación posterior ya pagada en trámite.
Se revalidó su sesión Stripe de prueba existente, sin otro cobro ni activación
manual. El servicio del listado devolvió la cuenta activa/pagada y se comprobó
el acceso real al panel con su contraseña. Las fechas resultantes fueron
2026-11-09 a 2026-12-09. La representación de ese registro en Clientes se comprobó
con API y sesión administrativa simuladas en navegador; no se fabricó una sesión
administrativa válida del backend. No se publica información personal de la prueba.

El retorno real de la sesión muestra «Pago confirmado; renovación activa». El
enlace anterior muestra que la recompra ya está pagada y oculta otro checkout.
La cuenta de prueba queda ahora activa por su pago posterior; esto sustituye el
estado vencido que se dejó al terminar la primera prueba operativa.

Comprobaciones finales:

- Suite backend con clave de sesión sintética: **709 aprobadas, 46 omitidas**
  por no configurar PostgreSQL desechable para esa ejecución.
- Suite frontend: **359 aprobadas**.
- Docker Compose construyó frontend/backend correctamente y recreó solamente
  los contenedores locales, conservando los volúmenes. Ambos quedaron saludables.
- Flake8 E9/F63/F7/F82: **0 errores**; `git diff --check`: correcto.
- Pruebas documentales aisladas: **13 aprobadas**; validador global: correcto.
- Se renovaron las capturas de escritorio/móvil para reflejar la nueva regla y
  se añadió [recompra ya pagada](renovada.png). El navegador verificó la revisión
  previa al pago, ausencia de desbordamiento móvil y bloqueo de otro checkout.

## Renovación administrativa desde Clientes · 2026-11-09

Se añadió **Renovar** en la tabla y **Renovar membresía** en los detalles, con
resumen del mismo plan/importe y selección de efectivo o Stripe. El servidor
protege resumen y confirmación con `admin`/`staff`, igual que activación.
La renovación administrativa no necesita el enlace del correo ni su ventana
limitada y acepta clientes de registro público o administrativo.

En caja se exige confirmar la recepción del importe; crear, pagar y activar la
nueva membresía forman una sola transacción. Una compra pendiente se retoma
mediante Stripe: este diálogo no permite cobrarla también en efectivo mientras
el checkout siga pendiente. Los reintentos usan el origen del resumen y se
rechazan si el cliente ya tiene una nueva compra pagada o cambió el importe.
Se mantienen historial, primera activación y días vigentes anteriores.

Evidencias finales:

- `AUTH_SECRET_KEY=<clave sintética> python -m pytest tests/ -q` desde backend:
  **719 aprobadas, 46 omitidas** por requerir PostgreSQL desechable explícito.
  Incluye diez casos nuevos de renovación administrativa: caja, recibo obligatorio,
  precio, duplicados concurrentes, Stripe reutilizable, permisos, activación inicial,
  renovación antigua y ambos orígenes de registro. No se añadió SQL.
- `npm test` desde frontend: **365 aprobadas**, con seis nuevas pruebas del diálogo
  y su coordinación: revisión previa, efectivo, doble clic, actualización de ficha,
  Stripe pendiente, errores y respuestas obsoletas/cambio de sesión.
- `npm run build`: correcto; construcción Compose de frontend/backend: correcta.
- Flake8 E9/F63/F7/F82: **0 errores**; `git diff --check`: correcto.
- Validador global: correcto. Pruebas documentales: **13 aprobadas**.
- Chromium/Playwright con API, sesión administrativa y datos ficticios: botón en
  tabla y detalles; apertura del resumen sin compra; confirmación de efectivo
  obligatoria; una sola petición por confirmación; ficha activa al guardar;
  compra pendiente selecciona Stripe y bloquea caja; navegación al checkout simulado.
  Se revisaron [escritorio](admin-renovar-escritorio.png) y
  [móvil](admin-renovar-movil.png), sin desbordamiento del diálogo.
- Se actualizaron los contenedores locales conservando los volúmenes. No se
  renovó ninguna cuenta real, no se registró efectivo real ni se enviaron nuevos
  correos o cobros de proveedor como parte de esta validación administrativa.

## Restricción a última semana o membresía vencida · 2026-11-09

El usuario limitó la renovación a membresías vencidas o a siete días o menos del
vencimiento, incluidos tres días y el último día. Se añadió una regla de dominio
compartida con fecha de Perú, pago/activación previos y período ya comenzado.
Se valida en el enlace público, resumen administrativo y dentro de los comandos
transaccionales; la creación genérica tampoco permite iniciar una renovación
anticipada fuera de esa ventana. Las confirmaciones de pagos ya realizados
conservan su idempotencia y no se descartan por esta restricción nueva.

El listado devuelve `renewal_allowed` usando la última membresía activada/pagada,
incluso si la fila más reciente corresponde a una compra pendiente. El frontend
conserva ese dato y oculta el botón cuando el servidor lo deniega. Su fallback de
fechas también utiliza el día de Perú. No se alteraron fechas ni pagos guardados.

El enlace firmado admite ahora los siete días previos; conserva su caducidad a
treinta días del vencimiento. Los avisos se mantienen a tres días y al vencer,
y se omiten períodos futuros o registros todavía pendientes de activación.

Validación final:

- Backend: **731 aprobadas, 46 omitidas** (PostgreSQL desechable no configurado
  para esta ejecución). Las nuevas regresiones verifican 8/7/3/0/-1 días, caja,
  Stripe, enlace firmado, campo del directorio y rechazo de creación genérica.
- Frontend: **367 aprobadas**. Se verificaron visibilidad, fecha de Perú,
  fechas inválidas/períodos futuros y preferencia por la elegibilidad del servidor.
- Compose construyó frontend/backend y recreó los contenedores locales;
  ambos saludables. Flake8 crítico: **0 errores**; diff sin errores de espacios.
- Validador documental: correcto; pruebas documentales aisladas: **13 aprobadas**.
- Playwright con datos ficticios y sesión/API simuladas: botón ausente a ocho
  días y presente a siete, tres, cero y vencida. Evidencia:
  [ventana de renovación](ventana-renovacion.png). Sin compras ni envíos reales.
- Comprobación de solo lectura en la cuenta de prueba previamente renovada:
  el listado niega renovar mientras su vigencia supera la última semana y el
  servicio administrativo rechaza el resumen por la misma condición.
