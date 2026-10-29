# MOD-02 · Clientes

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Mantener el directorio de clientes y su registro público o administrativo,
conservando identidad, origen e historial asociado.

## 2. User Story

**P1.** Como administrador o staff, quiero registrar, buscar y editar clientes
para gestionar su relación con el gimnasio. Como visitante, quiero registrarme
en un plan y continuar el flujo de pago sin duplicar mi alta al reintentarlo.

Prueba independiente: registrar una cuenta sintética, localizarla por su
identificador/DNI, editarla y comprobar que conserva origen y fecha de alta.

## 3. Acceptance Criteria

1. **CA-01.** Dado un registro administrativo sin pago, al guardarlo quedan
   cliente y membresía en trámite, pendientes de pago y activación.
2. **CA-02.** Dado un cliente registrado, al editarlo se conservan identidad,
   origen y fecha de registro.
3. **CA-03.** Dada una búsqueda por identificadores, al resolver al cliente se
   respeta la prioridad de identidad y no se devuelve uno ajeno.
4. **CA-04.** Dado un registro guardado cuyo checkout falla, al reintentarlo se
   reutiliza el alta y el importe guardados.
5. **CA-05.** Dado un cliente con matrículas y progreso, al borrarlo se eliminan
   sus dependencias contempladas por el comando y se libera el cupo dentro de
   una operación atómica.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_admin_client_payment.py](../../../backend/tests/test_admin_client_payment.py): `test_register_without_payment_creates_pending_admin_membership`. |
| CA-02 | [test_review_regressions.py](../../../backend/tests/test_review_regressions.py): `test_client_edit_preserves_registration_date_across_normalization_and_mapping`. |
| CA-03 | [test_clients_lookup.py](../../../backend/tests/test_clients_lookup.py). |
| CA-04 | [test_admin_client_payment.py](../../../backend/tests/test_admin_client_payment.py): `test_retry_checkout_uses_saved_amount_and_does_not_duplicate_registration`. |
| CA-05 | [test_review_regressions.py](../../../backend/tests/test_review_regressions.py): `test_client_deletion_removes_enrollments_progress_and_releases_capacity`; [test_scoped_operations.py](../../../backend/tests/test_scoped_operations.py): `test_client_deletion_keeps_the_whole_cascade_inside_one_command`. |

## 4. Technical Constraints

- API: [clients_routes.py](../../../backend/presentation/routes/clients_routes.py).
  `/api/clientes`, `/api/clientes/me`, `/api/registro-publico` y
  `/api/clientes/registro-admin`.
- Aplicación: [clients_service.py](../../../backend/application/services/clients_service.py)
  y [client_payments_service.py](../../../backend/application/services/client_payments_service.py).
  Reglas de identidad/directorio en
  [accounts_rules.py](../../../backend/domain/services/accounts_rules.py).
- Entidades: `CLIENTES`, `MEMBRESIA` y dependencias declaradas en
  [accounts.py](../../../backend/application/operations/accounts.py).
- UI: `/registro`, `/admin/clients`,
  [ClientsView.vue](../../../frontend/src/presentation/views/ClientsView.vue),
  componentes de clientes y [clients.js](../../../frontend/src/application/modules/clients.js).

## 5. Guardrails

No activar ni marcar pagado por campos enviados desde el registro público.
No tomar una edición como renovación. No perder `origen_registro` o
`fecha_registro` al mapear y recargar. No ejecutar borrados parciales fuera del
comando de eliminación. Listado y escritura administrativa exigen `admin/staff`.

## 6. Edge Cases

- Promoción inválida en el alta administrativa: rechazar antes de crear al cliente.
- Checkout indisponible después del alta: conservar el registro para reintento;
  no informar un cobro confirmado.
- Identificador que no corresponde al cliente: no resolver mediante coincidencia
  parcial con otro cliente.
- Cliente histórico con campos opcionales ausentes: aplicar normalización de
  compatibilidad sin inventar un pago u origen confirmado.

## 7. Definition of Done

Verificar los criterios afectados, la conservación de campos tras recarga y
los flujos del directorio. Si cambia el borrado, comprobar su atomicidad en
PostgreSQL aislado. Actualizar este contrato y el [DoD](../../docs/DoD.md) aplicable.
