# MOD-03 · Membresías y pagos

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Gestionar el ciclo de membresía separando registro, pago, activación y vencimiento,
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
   importe, metadatos y modo corresponden a esa membresía.
3. **CA-03.** Dada una membresía sin pago confirmado, al activarla se rechaza;
   activarla otra vez después de estar activa no extiende sus fechas.
4. **CA-04.** Dada una confirmación manual autorizada, al guardarla se registra
   el cobro sin activar la membresía ni reemplazar un Stripe ya verificado.
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
- UI: `/registro/pago/:idCliente`, `/admin/payments`, acciones de cliente en
  [useClientMembershipActions.js](../../../frontend/src/presentation/composables/clients/useClientMembershipActions.js).

## 5. Guardrails

No equiparar pago con activación. No confiar en el importe o estado enviados
por el navegador. No recalcular compras antiguas con el precio actual del plan.
No usar un valor por defecto cuando el precio guardado sea cero. No reactivar
una membresía vencida mediante edición o evento Stripe duplicado.

## 6. Edge Cases

- Webhook/retorno duplicados: conservar idempotencia y el estado ya activo.
- Membresía futura, impaga o cuenta sin activación: no conceder acceso por el
  mero flag de cuenta activa.
- Fallo de checkout: conservar alta para reintento cuando ya se guardó.
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
