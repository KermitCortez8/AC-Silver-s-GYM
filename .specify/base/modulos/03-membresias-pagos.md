# MOD-03 · Membresías y pagos

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Gestionar registro, pago, activación inicial, renovación automática y vencimiento,
con trazabilidad del importe realmente contratado.

## 2. User Story

**P1.** Como cliente, quiero pagar la membresía que elegí y obtener acceso cuando
el personal la active. Como administrador o staff, quiero verificar pagos y
vigencia sin perder el historial ni cobrar o extender dos veces por reintentos.

Prueba independiente: crear una membresía en trámite, confirmar un pago de
prueba, activarla y avanzar un reloj controlado hasta después del vencimiento.

## 3. Acceptance Criteria

1. **CA-01.** Dado un registro nuevo, al recorrer pago, activación y expiración
   las escrituras de membresía usan `EN_TRAMITE`, `ACTIVO` y `VENCIDA`.
2. **CA-02.** Dada una confirmación Stripe, solo se guarda el pago si sesión,
   importe, metadatos y modo corresponden a esa membresía o solicitud pública.
   Para solicitudes nuevas, el pago crea cliente y membresía pagada en trámite
   de forma atómica, sin conceder acceso antes de la activación administrativa.
3. **CA-03.** Dada una membresía sin pago confirmado, al activarla se rechaza;
   activarla otra vez después de estar activa no extiende sus fechas.
4. **CA-04.** Dada una confirmación manual autorizada, al guardarla se registra
   el cobro sin reemplazar un Stripe ya verificado. Solo la primera membresía
   necesita activación administrativa; una renovación se activa con el pago.
5. **CA-05.** Dada una membresía vigente, el acceso incluye todo su último día
   en Perú; después vence sin borrar el pago ni bloquear una renovación vigente.
6. **CA-06.** Dado el historial administrativo, al consultarlo se conserva cada
   pago y su importe guardado, incluido descuento, sin duplicar confirmaciones.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_membership_states.py](../../../backend/tests/test_membership_states.py). |
| CA-02 | [test_stripe_confirmation.py](../../../backend/tests/test_stripe_confirmation.py) y [test_stripe_checkout.py](../../../backend/tests/test_stripe_checkout.py). |
| CA-03 | [test_stripe_confirmation.py](../../../backend/tests/test_stripe_confirmation.py): `test_membership_cannot_be_activated_before_payment`, `test_activating_an_active_membership_does_not_extend_its_dates`. |
| CA-04 | [test_admin_client_payment.py](../../../backend/tests/test_admin_client_payment.py): `test_manual_payment_endpoint_records_cash_without_activating_membership`, `test_repeated_manual_confirmation_preserves_verified_stripe_payment`. |
| CA-05 | [test_membership_expiration.py](../../../backend/tests/test_membership_expiration.py). |
| CA-06 | [test_membership_payments.py](../../../backend/tests/test_membership_payments.py). |

## 4. Technical Constraints

- API: [memberships_routes.py](../../../backend/presentation/routes/memberships_routes.py)
  y [clients_routes.py](../../../backend/presentation/routes/clients_routes.py).
  Incluye `/api/membresias`, `/api/pagos/membresias`, webhook y confirmación de
  retorno Stripe, confirmación manual y activación por cliente.
- Servicios: [client_payments_service.py](../../../backend/application/services/client_payments_service.py),
  [membership_checkout_service.py](../../../backend/application/services/membership_checkout_service.py).
- Reglas: [memberships_rules.py](../../../backend/domain/services/memberships_rules.py),
  [membership_lifecycle.py](../../../backend/domain/services/membership_lifecycle.py),
  [money.py](../../../backend/domain/money.py); proveedor
  [stripe_service.py](../../../backend/infrastructure/services/stripe_service.py).
- Datos: `MEMBRESIA`, `CLIENTES`, plan y promoción. Precondiciones SQL en
  `001`, `009_admin_client_stripe`, `010`, `011`, `014`, `015`, `016`, según esquema.
  El registro público separado añade `PREREGISTROS_MEMBRESIA` y
  [020_public_preregistrations.sql](../../../backend/migrations/020_public_preregistrations.sql).
- UI: `/registro/pago/:idCliente`, `/admin/payments`, acciones de cliente en
  [useClientMembershipActions.js](../../../frontend/src/presentation/composables/clients/useClientMembershipActions.js).

## 5. Guardrails

No conceder la primera activación mediante un pago. Las renovaciones de una
cuenta previamente activada se habilitan al confirmar su pago. No confiar en el importe o estado enviados
por el navegador. No recalcular compras antiguas con el precio actual del plan.
No usar un valor por defecto cuando el precio guardado sea cero. No reactivar
una membresía vencida mediante edición o evento Stripe duplicado.

## 6. Edge Cases

- Webhook/retorno duplicados: conservar idempotencia y el estado ya activo.
- Membresía futura, impaga o cuenta sin activación: no conceder acceso por el
  mero flag de cuenta activa.
- Fallo de checkout: conservar alta para reintento cuando ya se guardó.
  En el registro público nuevo se conserva únicamente una solicitud privada.
  Reintentos usan la misma sesión; una sesión expirada permite otro intento
  después de verificar su estado. Una creación incierta de más de 24 horas se
  busca en Stripe, sin crear otra sesión con una clave de idempotencia caducada.
- Caducidad: el proceso del backend revisa solicitudes vencidas cada minuto;
  cierra sesiones abiertas antes de archivar, reconcilia las pagadas y conserva
  las completas sin pago definitivo o aquellas cuyo estado no se puede verificar.
  Las promociones se reservan al solicitar y liberan una sola vez al archivar.
- Pago correcto con correo fallido: conservar el pago; informar el resultado
  de notificación por separado.
- Estados históricos: normalizar lectura; un pendiente antiguo no se vuelve pagado.

## 7. Definition of Done

Verificar criterios económicos y temporales afectados, idempotencia, permisos e
historial. Usar servicios de prueba sin cobrar cuentas reales; registrar por
separado cualquier comprobación de proveedor. Cumplir el [DoD](../../docs/DoD.md).

### Protección de compras y edición (feature 001)

La edición genérica rechaza membresías pagadas, activas o vencidas y nunca transfiere
una membresía a otro cliente. Las pendientes editadas conservan EN_TRAMITE/PENDIENTE
y fechas vacías: el pago y la activación siguen sus comandos específicos.
La confirmación conserva el importe contratado cero y rechaza un cobro positivo que
intente reemplazarlo; el fallback al plan solo se conserva para importe ausente/null
histórico. No se incorpora una pasarela de compras gratuitas.
Regresiones en [test_client_flow_control.py](../../../backend/tests/test_client_flow_control.py).

El retorno de pago distingue comprobación en curso, pendiente, error y confirmado.
Permite volver a verificar la misma sesión sin iniciar otro cobro, rechaza una
confirmación de otro cliente y descarta respuestas de rutas anteriores. Regresiones
en [36-client-flow-control.test.js](../../../frontend/tests/36-client-flow-control.test.js).

### Límites de formularios

La búsqueda general del historial de pagos admite hasta 50 caracteres y bloquea
la entrada adicional sin avisos de longitud. Los límites de edición de planes
se describen en [MOD-04](04-planes-promociones.md).

Evidencia: [validación de límites](../validaciones/limites-formularios/validation.md).

### Recompra desde el correo de vencimiento

La ruta pública `/renovar-membresia` recibe un enlace personal firmado en el
fragmento `#token=…`; permite revisar plan, descripción, duración, fin anterior y
total antes de abrir Stripe. No requiere sesión vigente. La API valida la firma,
la membresía pagada de origen y una ventana de siete días antes a treinta días
después del vencimiento, con fecha de Perú. No devuelve datos personales.

`GET /api/renovacion?token=…` devuelve los detalles y
`POST /api/renovacion/checkout` recibe `token` y `monto_pago` como importe esperado:
el servidor calcula el precio y rechaza discrepancias. La recompra utiliza el
mismo plan al precio actual, sin trasladar promociones anteriores. Una compra
pendiente posterior se reutiliza con su importe contratado y su promoción.
El comando transaccional evita crear otra membresía ante peticiones concurrentes;
una renovación posterior pagada impide iniciar otro cobro desde el enlace anterior.

Se reutiliza Stripe Checkout y la confirmación existente mediante webhook/retorno.
La referencia de la membresía pendiente conserva la sesión para retomarla; solo
una sesión verificada como expirada permite otro intento. Cancelar vuelve al
resumen. Una sesión completa pendiente de conciliación bloquea un nuevo pago.
El pago anticipado conserva el acceso de la membresía anterior todavía vigente.
La primera membresía requiere activación administrativa. Las renovaciones de una
cuenta con historial de membresía pagada y activada se activan al confirmar Stripe
o el pago en caja, dentro de la misma transacción, sin una segunda aprobación.
El servidor identifica ese historial; el navegador no decide si es renovación.
Si la membresía anterior venció, la nueva empieza el día del pago confirmado;
si sigue vigente, empieza al día siguiente de su último día inclusivo, conservando
las fechas anteriores. Se mantiene el cálculo actual del fin como inicio más la
duración del plan. Un reintento del mismo pago no extiende fechas ni reactiva una
membresía ya vencida. Una renovación pagada en trámite de la implementación
anterior se concilia al verificar otra vez su sesión, sin efectuar un nuevo cobro.

La vista de retorno y el correo de pago muestran la activación automática y las
fechas; el registro inicial mantiene su mensaje de activación pendiente. El
directorio fuerza una actualización al abrir y se refresca cada treinta segundos
y al recuperar foco, sin interrumpir formularios ni detalles abiertos.

Fuentes: [servicio de renovación](../../../backend/application/services/membership_renewal_service.py),
[vista](../../../frontend/src/presentation/views/MembershipRenewalView.vue),
[regresiones backend](../../../backend/tests/test_membership_renewal.py),
[regresiones frontend](../../../frontend/tests/40-membership-renewal.test.js) y
[validación](../validaciones/renovacion-membresia/validation.md).

### Renovación desde Clientes

El personal autorizado de Clientes (`admin` o `staff`, igual que la activación)
puede usar **Renovar** en la tabla o **Renovar membresía** en los detalles. El
diálogo presenta el plan actual, duración, fin anterior e importe. La operación
no modifica la compra anterior ni crea una cuenta nueva.

`GET /api/clientes/{id_cliente}/renovacion` obtiene el resumen sin el enlace del
correo ni su ventana de caducidad. El servidor exige una membresía anterior
pagada y activada que esté vencida o en sus últimos siete días de vigencia. `POST /api/clientes/{id_cliente}/renovar-membresia` recibe el ID
de origen del resumen, importe esperado, método `efectivo`/`stripe` y confirmación
de recepción de efectivo. Se rechazan una membresía de origen desactualizada,
importe discrepante y el intento de eludir la activación inicial.

En caja, el administrador debe confirmar que recibió el importe. La creación,
el pago y la activación de la nueva membresía se guardan en una sola transacción.
El evento de correo usa la cola de pago existente. En Stripe se reutilizan
checkout, referencia, verificación y activación automática; las sesiones nuevas
retornan al directorio administrativo. Se permiten clientes de origen público o
administrativo. Los reintentos concurrentes de la misma compra no crean otro cobro.

Una renovación pendiente se retoma con Stripe. No se permite iniciar desde este
diálogo otro cobro en efectivo mientras exista esa compra pendiente, para evitar
mezclar caja con un checkout aún pagable o en preparación. El diálogo muestra
carga, error recuperable y bloqueo durante la confirmación; descarta respuestas
al cerrar o cambiar de sesión.

Evidencia: [regresión backend](../../../backend/tests/test_admin_membership_renewal.py),
[regresión frontend](../../../frontend/tests/41-admin-membership-renewal.test.js),
[diálogo](../../../frontend/src/presentation/components/clients/ClientRenewalDialog.vue)
y [validación](../validaciones/renovacion-membresia/validation.md).


### Ventana de renovación: última semana o vencimiento

La renovación administrativa y pública se inicia únicamente cuando la membresía
activada y pagada ya venció o faltan **siete días o menos** para su fecha final.
El límite es inclusivo: siete, tres y cero días son válidos; ocho días no.
Se usa el día civil de Perú y se excluyen períodos futuros que todavía no comienzan.

La restricción se comprueba en el resumen administrativo, el enlace firmado y
los comandos transaccionales de renovación y creación genérica de membresías.
El listado publica `renewal_allowed`, calculado sobre la última membresía pagada
y activada, para mostrar **Renovar** con la misma regla aunque exista una compra
pendiente. Un enlace anterior no evita el rechazo de una renovación ya pagada.
No se rechaza la confirmación de un pago Stripe ya realizado por el mero cambio
de esta regla; se conserva su verificación e idempotencia.

Los avisos por correo mantienen su programación de los últimos tres días y
vencimiento; no se añaden envíos a siete días por ampliar la ventana de compra.
Tampoco se preparan recordatorios de vencimiento de un registro inicial pagado
que todavía no fue activado ni de un período futuro que no ha comenzado.
