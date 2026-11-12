# MOD-03 · Membresías y pagos · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

9 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-03](../../../../base/modulos/03-membresias-pagos.md). Actores: Cliente, administrador y personal autorizado para cobros.

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M03-01** · Integración / estados · CA-01 | Primera membresía nueva y reloj D controlado. | Recorrer registro, pago, activación y vencimiento; intentar escribir un cuarto estado. | Las escrituras solo usan EN_TRAMITE, ACTIVO y VENCIDA; un estado adicional es rechazado sin mutación. | [test_membership_states.py](../../../../../backend/tests/membresias_pagos/integracion/test_membership_states.py): `test_registration_payment_activation_and_expiry_use_only_three_states` |
| **CP-M03-02** · Integración / pago verificado · CA-02 | Membresía con importe guardado S/90 y checkout vinculado. | Confirmar sesión pagada válida; repetir con importe, metadatos, titular o modo alterados y con sesión impaga. | Solo el caso válido guarda pago; las variantes rechazadas conservan estado previo sin acreditar importes del navegador. | [test_stripe_confirmation.py](../../../../../backend/tests/membresias_pagos/integracion/test_stripe_confirmation.py) |
| **CP-M03-03** · Integración / activación · CA-03 | Primera membresía impaga; otra pagada aún sin activar. | Intentar activar la impaga; activar la pagada; repetir activación y comparar fechas. | La impaga se rechaza; la pagada se activa con su duración; repetir no extiende el período. | [test_stripe_confirmation.py](../../../../../backend/tests/membresias_pagos/integracion/test_stripe_confirmation.py): `test_activating_an_active_membership_does_not_extend_its_dates` |
| **CP-M03-04** · Integración HTTP / caja · CA-04 | Personal autorizado y primera membresía pendiente; variante con Stripe verificado. | Confirmar efectivo; repetir la confirmación manual sobre la variante Stripe. | La primera queda pagada sin activación automática; un pago Stripe existente conserva su método/referencia. | [test_admin_client_payment.py](../../../../../backend/tests/clientes/integracion/test_admin_client_payment.py): `test_repeated_manual_confirmation_preserves_verified_stripe_payment` |
| **CP-M03-05** · Integración / frontera temporal · CA-05 | Membresía pagada activada que termina D y reloj Lima controlado. | Consultar acceso al final de D y al comenzar D+1; repetir con renovación vigente. | D es inclusivo; luego vence sin borrar historial; una renovación vigente conserva/restaura el acceso. | [test_membership_expiration.py](../../../../../backend/tests/membresias_pagos/integracion/test_membership_expiration.py): `test_access_includes_last_day_and_expiration_preserves_payment_history` |
| **CP-M03-06** · Integración HTTP / historial · CA-06 | Dos compras con descuentos/precios distintos y una confirmación duplicada. | Confirmar y consultar historial como personal y luego como cliente sin permiso. | Cada pago aparece una vez con su importe original, incluso cero; el historial administrativo no se entrega al rol no autorizado. | [test_membership_payments.py](../../../../../backend/tests/membresias_pagos/integracion/test_membership_payments.py); [test_admin_client_payment.py](../../../../../backend/tests/clientes/integracion/test_admin_client_payment.py) |
| **CP-M03-07** · Integración / renovación · CA-04, CA-05 | C1 tuvo un período activado y recompra dentro de últimos siete días o después de vencer. | Pagar renovación verificada; repetir confirmación; probar compra inicial sin activación como variante. | La renovación se activa sin otra aprobación; anticipada comienza tras el último día inclusivo anterior; reintentar no amplía fechas; la compra inicial no elude su aprobación. | [test_membership_renewal.py](../../../../../backend/tests/membresias_pagos/integracion/test_membership_renewal.py): `test_early_renewal_starts_after_inclusive_last_day_and_is_not_activated_twice` |
| **CP-M03-08** · Integración HTTP / ventana · CA-04, CA-05 | Período activado con fin F; personal autorizado; F−8, F−7 y vencida. | Solicitar resumen y confirmar recompra; intentar eludir ventana con Stripe/alta genérica; en caja omitir confirmación de recibo. | F−8 se rechaza; F−7 y vencida son elegibles; ninguna ruta elude la ventana ni guarda cobro de caja sin confirmación requerida. | [test_admin_membership_renewal.py](../../../../../backend/tests/membresias_pagos/integracion/test_admin_membership_renewal.py) |

## Pruebas de interfaz y navegación

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M03-09** · Interfaz SSR / renovación · CA-04 | Compra Stripe pendiente y resumen de renovación abierto. | Confirmar dos veces en curso; cerrar/cambiar sesión antes de resolver; simular precio desactualizado. | No se duplican envíos; se reutiliza la compra pendiente y no se ofrece caja; una respuesta obsoleta se descarta y el error permite revisar otra vez. | [admin-membership-renewal.test.js](../../../../../frontend/tests/membresias_pagos/interfaz/admin-membership-renewal.test.js) |
