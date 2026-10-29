# MOD-07 · Rutinas y progreso

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Permitir al personal de entrenamiento mantener rutinas, asignarlas a matrículas
y registrar progreso por ejercicio conservando el historial de sesiones.

## 2. User Story

**P1.** Como entrenador, quiero buscar un cliente por DNI, asignarle una rutina
compatible con su clase y registrar su progreso para dar seguimiento al trabajo.

Prueba independiente: crear una rutina con ejercicios, asignarla a una matrícula
activa compatible y consultar el progreso registrado por la sesión del entrenador.

## 3. Acceptance Criteria

1. **CA-01.** Dada una rutina con ejercicios, al guardarla y recargarla se
   conserva el catálogo y el detalle de ejercicios del historial de progreso.
2. **CA-02.** Dada una matrícula activa con horario activo y rutina del mismo
   servicio, la asignación se guarda; con matrícula/horario inactivo o servicio
   incompatible se rechaza.
3. **CA-03.** Dado un registro de progreso, al enviar un actor distinto el
   servidor guarda el usuario autenticado.
4. **CA-04.** Dados pesos negativos o datos anidados inválidos, se rechazan antes
   de mutar; un peso cero válido se conserva.
5. **CA-05.** Dado el monitor de rutinas, las acciones de asignación/progreso y
   las representaciones del descanso usan la coordinación de sus composables.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_trainer_exercises.py](../../../backend/tests/test_trainer_exercises.py): `test_trainer_api_preserves_exercises_in_catalog_and_session_history`, `test_supabase_exercise_data_survives_json_serialization_and_legacy_rows`. |
| CA-02 | [test_schedule_enrollment.py](../../../backend/tests/test_schedule_enrollment.py): pruebas `test_assigns_matching_routine_to_active_enrollment_and_schedule` y rechazos de asignación. |
| CA-03 | [test_review_regressions.py](../../../backend/tests/test_review_regressions.py): `test_progress_uses_the_authenticated_trainer_even_if_the_actor_is_spoofed_or_missing`. |
| CA-04 | [test_partial_smell_fixes.py](../../../backend/tests/test_partial_smell_fixes.py): `test_exercise_weights_reject_negatives_and_preserve_zero`, `test_nested_exercise_contracts_reject_missing_identity_and_invalid_weights`. |
| CA-05 | [29-view-flows.test.js](../../../frontend/tests/29-view-flows.test.js). |

## 4. Technical Constraints

- API: [trainer_routes.py](../../../backend/presentation/routes/trainer_routes.py),
  `/api/trainer/overview`, `/rutinas`, `/clientes-rutinas`,
  `/matriculas/{id}/rutina` y `/matriculas/{id}/progreso`, con prefijo `/api/trainer`.
  Acceso interno: `admin`, `staff`, `trainer`.
- Reglas: [schedules_rules.py](../../../backend/domain/services/schedules_rules.py).
  Entidades `CATALOGO_RUTINA`, `MATRICULAS_HORARIO`, `RUTINA_PROGRESO`.
  `012_trainer_exercises.sql` habilita los datos de ejercicios.
- UI: `/trainer/routines`, `/trainer/routine-monitor`,
  [TrainerRoutineMonitorView.vue](../../../frontend/src/presentation/views/TrainerRoutineMonitorView.vue)
  y componentes de `presentation/components/trainer/`.
- Reutilizar [useRoutineAssignments.js](../../../frontend/src/presentation/composables/trainer/useRoutineAssignments.js),
  [useRoutineProgress.js](../../../frontend/src/presentation/composables/trainer/useRoutineProgress.js)
  y [useRestTimer.js](../../../frontend/src/presentation/composables/trainer/useRestTimer.js).

## 5. Guardrails

No aceptar el actor del navegador. No perder ejercicios por un esquema antiguo
ni ocultar errores de base como asignaciones exitosas. No duplicar temporizadores
para las dos representaciones visuales. No mezclar selección de borradores y
confirmación de desvinculación.

## 6. Edge Cases

- Matrícula sin rutina: no registrar progreso como si existiera una asignación.
- Membresía no admitida para asignar/progresar: informar la restricción.
- Esquema sin campos de ejercicios: informar la migración requerida; no descartarlos.
- Rutinas históricas sin ejercicios: conservar compatibilidad de lectura.
- Error de una escritura de asistencia ajena: guardar catálogo solo debe leer
  los recursos que declaró, no toda la base.

## 7. Definition of Done

Verificar asignación, actor, validación anidada e historial afectados. Si cambia
el monitor, comprobar sus flujos y descanso, además de revisión visual.
Actualizar este contrato y cumplir el [DoD](../../docs/DoD.md).
