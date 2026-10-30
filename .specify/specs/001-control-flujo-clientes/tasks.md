# Tasks: Control del flujo de clientes

**Input:** [spec.md](spec.md), [plan.md](plan.md), [context.md](context.md).

## Preparación

- [x] T001 Leer contratos y fuentes en `.specify/specs/001-control-flujo-clientes/context.md` y preparar dependencias aisladas.
- [x] T002 Completar especificación, diseño y contratos en `.specify/specs/001-control-flujo-clientes/`; revisar constitución y CA-01…CA-07.

## Fundamentos

- [x] T003 Añadir regresiones que reproduzcan CA-02…CA-06 en `backend/tests/test_client_flow_control.py` antes de corregir.

## US1 · Registro y administración

- [x] T004 [US1] Propagar errores de borrado e importe cero en `backend/application/services/clients_service.py` (CA-02, CA-04).
- [x] T005 [US1] Proteger propietario y compras confirmadas en `backend/domain/services/memberships_rules.py`; conservar pendiente y fallback solo ausente/null (CA-03, CA-04).
- [x] T006 [US1] Verificar registro público repetido, identidad y activación en `backend/tests/test_client_flow_control.py` y `backend/tests/test_admin_client_payment.py` (CA-01, CA-07).

## US2 · Horarios y asistencia

- [x] T007 [US2] Validar días y horas completas, guardar HH:MM en `backend/domain/services/schedules_rules.py` (CA-05).
- [x] T008 [US2] Reutilizar vigencia compartida en `backend/application/services/attendance_service.py` (CA-06).
- [x] T009 [US2] Añadir recorrido integrado con cupo, matrícula, entrada/salida, cancelación y vencimiento en `backend/tests/test_client_flow_control.py` (CA-07).

## Cierre

- [x] T010 Ejecutar suites y build según `.specify/docs/DoD.md`; registrar en `.specify/specs/001-control-flujo-clientes/validation.md` (CA-01…CA-07).
- [x] T011 Actualizar contratos en `.specify/base/modulos/02-clientes.md`, `03-membresias-pagos.md`, `05-horarios-matriculas.md` y `06-asistencias.md`.
- [x] T012 Converger, auditar y ejecutar hooks de cierre y pruebas SDD; documentar en `.specify/specs/001-control-flujo-clientes/validation.md`.

## Dependencias y secuencia

T001 -> T002 -> T003 -> T004/T005 -> T006 -> T007/T008 -> T009 -> T010 -> T011 -> T012.
Ejecución en esta sesión sin agentes adicionales. Suites backend/frontend independientes;
no hay paralelismo de cambios en archivos compartidos. Entrega incremental US1 y luego US2.

## Evidencia de ejecución

La evidencia final se conserva en [validation.md](validation.md); las tareas se marcan
solo tras verificar su resultado. El análisis previo se comunica en esta sesión.

## Ampliación de frontend solicitada por el usuario

- [x] T013 [US1] Corregir estados y reintento en `frontend/src/presentation/views/PaymentView.vue`; validar respuesta y descartar rutas anteriores (CA-08).
- [x] T014 [US1] Bloquear pago manual repetido y sincronizar detalles al activar en `frontend/src/presentation/composables/clients/useClientMembershipActions.js`, `frontend/src/presentation/components/clients/ClientDetailsDialog.vue` y `frontend/src/presentation/views/ClientsView.vue` (CA-09).
- [x] T015 Añadir regresiones en `frontend/tests/36-client-flow-control.test.js`, ejecutar suites/build y verificar en navegador (CA-08, CA-09).
- [x] T016 Actualizar contratos y evidencia en `.specify/specs/001-control-flujo-clientes/validation.md`; repetir convergencia y hooks finales.
