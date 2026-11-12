# MOD-02 · Clientes · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

9 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-02](../../../../base/modulos/02-clientes.md). Actores: Administrador/personal autorizado y visitante en el alta pública.

## Pruebas unitarias

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M02-01** · Unitaria / identidad · CA-03 | C1 y C2 con identificadores distintos y coincidencias secundarias controladas. | Buscar por ID explícito y después por identidad inexistente. | Se respeta la prioridad de identificación y nunca se devuelve C2 por una coincidencia ajena. | [test_clients_lookup.py](../../../../../backend/tests/clientes/unitarias/test_clients_lookup.py): `test_client_lookup_preserves_identity_priority` |

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M02-02** · Integración HTTP / alta · CA-01 | Admin con plan activo de S/100 y opción de registrar sin cobrar. | Enviar alta válida; consultar cliente y membresía. | Se crea un cliente administrativo y una membresía EN_TRAMITE/PENDIENTE, sin activación ni pago inventado. | [test_admin_client_payment.py](../../../../../backend/tests/clientes/integracion/test_admin_client_payment.py): `test_register_without_payment_creates_pending_admin_membership` |
| **CP-M02-03** · Integración / persistencia con doble · CA-02 | C1 existente con fecha de registro, código y origen guardados. | Editar nombre/teléfono; normalizar, mapear y volver a consultar. | Solo cambian campos personales; se conservan código, origen y fecha de registro. | [test_review_regressions.py](../../../../../backend/tests/transversales/integracion/test_review_regressions.py): `test_client_edit_preserves_registration_date_across_normalization_and_mapping` |
| **CP-M02-04** · Integración / recuperación · CA-04 | Alta guardada con promoción y precio contratado; Stripe simulado falla al abrir checkout. | Reintentar el cobro después de cambiar el precio del catálogo. | Se reutilizan alta e importe guardados; no aparece un segundo cliente ni una segunda membresía. | [test_admin_client_payment.py](../../../../../backend/tests/clientes/integracion/test_admin_client_payment.py): `test_retry_checkout_uses_saved_amount_and_does_not_duplicate_registration` |
| **CP-M02-05** · Integración HTTP / preregistro · CA-07 | Visitante con identidad nueva y gateway simulado. | Preregistrar; abandonar checkout; inspeccionar repositorio y directorio antes de pagar. | Existe únicamente solicitud temporal privada; no se crean cliente/membresía ni se publica una identidad temporal como cliente. | [test_public_preregistrations.py](../../../../../backend/tests/clientes/integracion/test_public_preregistrations.py): `test_public_http_stores_only_a_private_temporary_request` |
| **CP-M02-06** · Integración / caducidad · CA-07 | Solicitud de más de 24 horas con cupo promocional y pago pendiente, en proceso o incierto. | Reconciliar con el gateway antes de archivar; repetir la reconciliación. | Se archiva/libera cupo una sola vez solo cuando corresponde; el pago incierto o en proceso conserva la solicitud y nunca elimina un cliente pagado. | [test_public_preregistrations.py](../../../../../backend/tests/clientes/integracion/test_public_preregistrations.py): `test_periodic_reconciliation_preserves_uncertain_payment_and_confirms_late_paid_session` |

## Pruebas PostgreSQL y concurrencia

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M02-07** · PostgreSQL / borrado · CA-05 | C1 con dependencias y venta pagada con líneas; C2 ajeno; migración 025 en base desechable. | Borrar C1 y recargar; repetir con fallo de transacción inyectado. | En éxito se retira la cuenta y sus dependencias aplicables, conservando venta/comprador/líneas/stock; ante fallo se revierte todo; C2 permanece. | [test_client_deletion_postgres.py](../../../../../backend/tests/clientes/postgres/test_client_deletion_postgres.py); [test_review_regressions.py](../../../../../backend/tests/transversales/integracion/test_review_regressions.py); [test_scoped_operations.py](../../../../../backend/tests/transversales/integracion/test_scoped_operations.py) |
| **CP-M02-08** · PostgreSQL / concurrencia · CA-07 | Solicitud temporal y misma sesión pagada verificada en dos instancias. | Confirmar simultáneamente; repetir webhook/retorno; inyectar fallo al crear membresía en variante separada. | Se convierte una sola vez; no duplica cliente/pago; una transacción fallida no deja entidades parciales y puede reintentarse. | [test_public_preregistrations_postgres.py](../../../../../backend/tests/clientes/postgres/test_public_preregistrations_postgres.py) |

## Pruebas de interfaz y navegación

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M02-09** · Interfaz SSR / catálogo · CA-06 | Editor con borrador y catálogo remoto con plan personalizado y promoción aplicable. | Abrir alta, cambiar de plan; provocar fallo de catálogo y reintentar; editar compra histórica de importe cero. | Solo se ofrecen opciones válidas; no hay precios locales de reemplazo; se conserva el borrador y el contrato histórico al editar. | [client-catalog.test.js](../../../../../frontend/tests/clientes/interfaz/client-catalog.test.js) |
