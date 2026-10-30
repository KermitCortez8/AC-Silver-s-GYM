# Validación del preregistro público separado

Fecha: 2026-10-30.

## Alcance implementado

El registro público crea una fila privada en `PREREGISTROS_MEMBRESIA`, con
hash de contraseña mediante el hasher existente, identidad Google verificada,
plan e importe reservados, identificador opaco y plazo de 24 horas. No crea
`CLIENTES` ni `MEMBRESIA` hasta verificar un pago completo con importe, moneda,
modo, sesión, referencia y metadatos correctos.

La conversión utiliza los comandos tipados y la misma `commit_gym_transaction`:
cliente, membresía pagada en trámite y solicitud convertida se confirman juntos.
No concede acceso sin la activación administrativa posterior. Un webhook puede
completar el alta sin retorno del navegador; los duplicados y la carrera entre
webhook y retorno no crean otra cuenta ni alteran fechas de una membresía activa.
Tras convertir se retiran de la solicitud nombre, correo, DNI, teléfono,
identidad Google y hash; se conserva el comprobante para reconocer repeticiones.
Eliminar al cliente después no permite recrearlo con un webhook antiguo.

Los reintentos requieren las mismas credenciales y DNI y conservan el importe,
incluso si el catálogo cambia. Las promociones se reservan sin crear membresía y
se liberan una sola vez al archivar. Un plan asociado a solicitudes puede
desactivarse, pero no eliminarse mientras se conserva esa referencia.

El mantenimiento del backend revisa solicitudes vencidas cada minuto en lotes
de hasta 50. Verifica/cierra sesiones abiertas antes de archivar. Si hay pago
confirmado, convierte; si está en proceso o Stripe no responde, conserva la
solicitud para reconciliación. Una creación de checkout cuya respuesta se perdió
se recupera por idempotencia. Pasadas 24 horas, se busca por referencia e intento
en todas las páginas de Stripe dentro de su ventana de creación, sin reutilizar
una clave caducada para crear una sesión adicional. Solo una búsqueda exitosa
sin resultados permite archivar un intento sin identificador guardado.

La expiración archiva; no existe un borrado automático de datos de un pago
incierto. Las solicitudes expiradas pueden retomarse con otro intento y una
nueva cotización. Las altas administrativas siguen permitiendo clientes impagos.
Los clientes históricos y sus referencias Stripe conservan compatibilidad; no
se migran ni eliminan automáticamente porque podrían tener pagos en curso.

## Esquema y aplicación

[020_public_preregistrations.sql](../../../../backend/migrations/020_public_preregistrations.sql)
depende del esquema base y de `001_add_membership_payment_fields.sql`,
`003_add_google_identity.sql`, `009_admin_client_stripe.sql`, `011_membership_states.sql`,
`014_preserve_business_fields.sql`, `015_atomic_gym_transactions.sql` y
`016_transaction_sequence_permissions.sql`. Añade la tabla con RLS, índices de
identidad/sesión y permiso exclusivo de backend, y amplía las listas permitidas
de las RPC de 015. No depende de 019 (sesiones de horarios).

Aplicar 020 como propietario de tablas y secuencias **antes de actualizar el
backend y el frontend**. Si falta la tabla, las escrituras del registro fallan con
503 y el nombre de la migración; no se guardan registros en otro lugar ni se usa
un fallback REST. Reaplicar la migración es idempotente y se comprueba en SQL.

Para recuperar una versión anterior, restaurar su backend/frontend conservando
tabla y RPC ampliadas. No eliminar solicitudes ni revertir sus datos mientras
existan checkouts pendientes de reconciliación. El backend anterior desconoce
estas solicitudes; su recuperación requiere volver a ejecutar el mantenimiento
compatible. No aplicar todos los SQL indiscriminadamente.

La migración se probó en un PostgreSQL desechable `gym-prereg-postgres`, base
`gym_test`, aislado de red y con datos sintéticos. No se aplicó sobre Supabase:
esta sesión dispone de su acceso REST, pero no de conexión SQL ni herramientas
de administración. Tampoco se actualizaron los contenedores de la plataforma ni
se hicieron cobros o envíos de correo reales.

## Pruebas y evidencia

Comprobaciones ejecutadas:

- Backend completo: 658 pruebas correctas y 33 SQL omitidas en esa ejecución
  sin la variable de contenedor. Las 33 SQL se ejecutaron separadamente sobre
  PostgreSQL desechable: 27 correctas en transacciones/preregistros/sesiones y
  11 correctas en preregistros/límite de asistencia (cinco repetidas).
- Frontend completo: 293 pruebas correctas; `npm run build` correcto.
- Control `flake8` de E9/F63/F7/F82: cero errores.
- Validador documental correcto y 13 pruebas de `.specify/tests` correctas.
- `git diff --check` sin errores. Las vistas se mantienen bajo 500 líneas.
- CI incorpora la nueva suite SQL al job que crea PostgreSQL desechable.

- [test_public_preregistrations.py](../../../../backend/tests/test_public_preregistrations.py):
  solicitud privada, reintentos, credenciales/DNI, Google, importe guardado,
  checkout fallido, verificación, duplicados, caducidad, pago en proceso,
  respuesta incierta, reserva de promoción, recuperación y cliente eliminado.
- [test_preregistration_gateway.py](../../../../backend/tests/test_preregistration_gateway.py):
  parámetros y claves estables, metadatos sin datos personales y recuperación
  paginada por referencia e intento, sin interpretar errores como ausencia de pago.
- [test_public_preregistrations_postgres.py](../../../../backend/tests/test_public_preregistrations_postgres.py):
  privacidad/RLS, rollback completo ante fallo de membresía, confirmación desde
  dos servidores, alta concurrente de la misma identidad y reconciliación pagada.
- [36-client-flow-control.test.js](../../../../frontend/tests/36-client-flow-control.test.js)
  y [38-client-catalog.test.js](../../../../frontend/tests/38-client-catalog.test.js):
  no agregar solicitudes al directorio ni inventar un código de cliente,
  conservación del borrador y retorno identificado por token, con rechazo de
  una confirmación ajena. Se conserva el retorno numérico de sesiones anteriores.

El [recorrido en Chromium](evidence/browser-review.cjs) usa el frontend real y una
[API FastAPI aislada](evidence/server-review.py) con los servicios reales,
persistencia en memoria y gateway/avisos simulados. Bloquea dominios externos.
Verifica checkout fallido, abandono, reintento de la misma sesión, webhook antes
del retorno, creación de un único cliente pagado y archivo de otra solicitud
impaga sin afectar al cliente. [Resultados](evidence/browser-results.json): cuatro
escenarios correctos, un cliente, una membresía, una solicitud archivada y ningún
error de página. El directorio administrativo solo muestra al cliente pagado.

Capturas revisadas: [solicitud temporal](evidence/solicitud-temporal.png),
[checkout interrumpido](evidence/checkout-interrumpido.png),
[pago confirmado](evidence/pago-confirmado.png) y
[directorio tras el pago](evidence/directorio-tras-pago.png).

Para repetir, con dependencias del backend y Playwright/Chromium instalados,
arrancar desde la raíz en dos terminales:

```bash
node .specify/base/validaciones/views-modulares/evidence/serve-review.mjs
python .specify/base/validaciones/preregistros-separados/evidence/server-review.py
```

En otra terminal:

```bash
GYM_PLAYWRIGHT_MODULE=/ruta/a/playwright node .specify/base/validaciones/preregistros-separados/evidence/browser-review.cjs
```

Referencias del proveedor consultadas: [idempotencia de Stripe](https://docs.stripe.com/api/idempotent_requests)
(las claves pueden retirarse tras 24 horas) y [consulta paginada de sesiones](https://docs.stripe.com/api/checkout/sessions/list).
