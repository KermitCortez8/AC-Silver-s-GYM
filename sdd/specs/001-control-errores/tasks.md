# Tasks: Control de errores y conservación de estado

**Input**: [spec.md](spec.md), [plan.md](plan.md), investigación y contratos locales.
**Estado**: integración SDD instalada; el piloto funcional conserva tareas abiertas.
**Tests**: se requiere evidencia por criterio; reutilizar tests y añadir solo
regresiones que falten. Un test nuevo debe fallar antes de la corrección.

## Phase 1 — Instalación y principios

- [x] T001 Instalar Spec Kit 1.2.3 aislado y fijar su fuente en `sdd/requirements.txt`; añadir `sdd/scripts/setup-spec-kit.sh` y `sdd/scripts/specify`.
- [x] T002 Inicializar scripts, plantillas y skills oficiales en `sdd/.specify/` y `sdd/.agents/skills/`, conservando la rama y el trabajo local.
- [x] T003 Definir los principios del proyecto en `sdd/.specify/memory/constitution.md` y el punto de entrada en `AGENTS.md`.
- [x] T004 Adaptar `sdd/specs/001-control-errores/spec.md` y completar `plan.md`, `research.md`, `data-model.md`, `contracts/errors.md` y `quickstart.md`.

## Phase 2 — US1: conservar datos (P1)

Prueba independiente: comparar estado y borrador antes y después de una lectura,
un guardado o un borrado rechazado.

- [x] T005 [US1] Ejecutar los escenarios existentes de lecturas/escrituras rechazadas en `frontend/tests/31-module-error-control.test.js` y formularios en `26-stock-edit-forms.test.js` (ERR-001/002/003).
- [x] T006 [US1] Ejecutar identidades y catálogo preservado en `frontend/tests/35-response-identifiers.test.js`, y respuesta completa/204 en `32-http-error-control.test.js` (ERR-001).
- [ ] T007 [US1] Verificar con un escenario de presentación que una respuesta de escritura malformada comunica resultado sin confirmar y conserva el borrador; localizar el flujo en `frontend/src/presentation/` y reutilizar o ampliar `frontend/tests/26-stock-edit-forms.test.js` (ERR-003).

## Phase 3 — US2: mensajes, estados y privacidad (P1)

Prueba independiente: provocar validación y errores de proveedor con datos
sintéticos; comprobar estado, campos y ausencia de secretos.

- [x] T008 [US2] Ejecutar `backend/tests/test_module_error_control.py`, `test_basic_form_validation.py` y los escenarios HTTP/formulario de `frontend/tests/32-http-error-control.test.js` y `34-form-validation.test.js` (ERR-006/007/008).
- [ ] T009 [US2] Identificar y ejecutar evidencia de sesión ausente/inválida 401 y permisos reales en las rutas del piloto; ampliar `backend/tests/test_module_error_control.py` si falta, sin sustituir autenticación en esos casos (ERR-006).
- [ ] T010 [US2] Verificar en navegador los formularios del piloto: borrador, error por campo, `aria-invalid` y `aria-describedby`; registrar alcance y evidencia en `sdd/specs/001-control-errores/verification.md` (ERR-008).

## Phase 4 — US3: resultado incierto y cancelación (P1)

Prueba independiente: tiempo agotado o cancelación de una escritura, un solo
envío y aviso que permita consultar antes de repetir.

- [x] T011 [US3] Ejecutar timeout antes de cabeceras y durante el cuerpo, sin reintentos, en `frontend/tests/32-http-error-control.test.js` (ERR-004).
- [x] T012 [US3] Resolver D-01 como ERR-009 y documentar la semántica deseada en `sdd/specs/001-control-errores/research.md` y `contracts/errors.md`.
- [ ] T013 [US3] Añadir primero regresiones en `frontend/tests/32-http-error-control.test.js`: señal ya cancelada sin envío, escritura cancelada después del envío con resultado incierto y lectura cancelada sin resultado incierto; comprobar el fallo esperado de los nuevos casos (ERR-009).
- [ ] T014 [US3] Ajustar `frontend/src/infrastructure/services/httpTransport.js` a ERR-009, conservar el código de cancelación y el control del cuerpo completo, y volver a ejecutar los escenarios T011/T013.

## Phase 5 — US4: guardado confirmado y recarga fallida (P2)

- [x] T015 [US4] Ejecutar asignación, desvinculación y progreso confirmado con recarga fallida en `frontend/tests/33-trainer-refresh-errors.test.js`; comprobar mensaje, cierre y liberación de carga (ERR-005).

## Phase 6 — Evidencia e integración

- [x] T016 Registrar la base de frontend, compilación, backend y lint con sus comandos, resultados y limitaciones en `sdd/specs/001-control-errores/verification.md`.
- [x] T017 Validar artefactos con `sdd/.specify/scripts/bash/check-prerequisites.sh`, comprobar instalación e integridad, y añadir la comprobación estructural en `.github/workflows/pr-validation.yml`.
- [ ] T018 Reconciliar matriz de criterios y tareas, ejecutar análisis/convergencia y cerrar la aceptación del piloto solo cuando T007, T009, T010, T013 y T014 tengan evidencia suficiente.

## Dependencies & Execution Order

T001 → T002 → T003 → T004. Cada historia usa T004 como base y puede comprobarse
por separado. T014 depende de T013; T018 depende de todas las tareas de aceptación.
T016 y T017 verifican la adopción y no convierten las tareas pendientes en completas.
No hay migraciones ni una entrega de despliegue asociada a esta instalación.

## Implementation Strategy

Primero completar la adopción del proceso. Para el siguiente cambio funcional,
leer la matriz de `verification.md`, ejecutar la evidencia existente y continuar
con una tarea abierta acotada. No reimplementar comportamientos que ya están
demostrados. Los IDs de tareas son estables y se conservan al actualizar el plan.
