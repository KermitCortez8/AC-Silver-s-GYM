# MOD-07 · Rutinas y progreso · Casos individuales

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

15 casos individuales: 15 aprobados y 0 omitidos
registrados en la revisión del 2026-11-10. [Índice de módulos](../indice.md).
[Preparación, ejecución y lectura de resultados](../indice.md#cómo-leer-y-repetir-cada-caso).
[Escenarios de uso del módulo](casos-de-uso.md) y
[selectores/comandos estructurados](catalogo-pruebas.json).

## Pruebas de integración

### Backend

#### test_trainer_exercises.py

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M07-I-BE-001** | <code>test_upsert_rutina_with_ejercicios</code> · [test_trainer_exercises.py:20](../../../../../backend/tests/rutinas_progreso/integracion/test_trainer_exercises.py#L20) | Preparación local de la función. | <code>self.assertIsNotNone(created.get("id_rutina"))</code>; <code>self.assertEqual(len(created.get("ejercicios", &#91;&#93;)), 2)</code>; <code>self.assertEqual(created&#91;"ejercicios"&#93;&#91;0&#93;&#91;"nombre_ejercicio"&#93;, "Press de Banca Plano")</code> (4 en fuente). | Aprobado |
| **CT-M07-I-BE-002** | <code>test_registrar_progreso_rutina_with_ejercicios_detalle</code> · [test_trainer_exercises.py:51](../../../../../backend/tests/rutinas_progreso/integracion/test_trainer_exercises.py#L51) | Preparación local de la función. | <code>self.assertEqual(res&#91;"id_matricula"&#93;, 10)</code>; <code>self.assertEqual(len(res.get("ejercicios_detalle", &#91;&#93;)), 1)</code>; <code>self.assertEqual(res&#91;"ejercicios_detalle"&#93;&#91;0&#93;&#91;"nombre_ejercicio"&#93;, "Sentadillas")</code> (4 en fuente). | Aprobado |
| **CT-M07-I-BE-003** | <code>test_trainer_api_preserves_exercises_in_catalog_and_session_history</code> · [test_trainer_exercises.py:94](../../../../../backend/tests/rutinas_progreso/integracion/test_trainer_exercises.py#L94) | Preparación local de la función. | <code>response.status_code == 200</code>; <code>routine&#91;"ejercicios"&#93;&#91;0&#93;&#91;"id_ejercicio"&#93; == "press"</code>; <code>routine&#91;"ejercicios"&#93;&#91;0&#93;&#91;"series"&#93; == 4</code> (8 en fuente). | Aprobado |
| **CT-M07-I-BE-004** | <code>test_supabase_exercise_data_survives_json_serialization_and_legacy_rows</code> · [test_trainer_exercises.py:135](../../../../../backend/tests/rutinas_progreso/integracion/test_trainer_exercises.py#L135) | Preparación local de la función. | <code>service._map_routine(remote)&#91;"ejercicios"&#93; == routine&#91;"ejercicios"&#93;</code>; <code>service._map_routine_progress(remote)&#91;"ejercicios_detalle"&#93; == progress&#91;"ejercicios_detalle"&#93;</code>; <code>service._map_routine({"id_rutina": 1})&#91;"ejercicios"&#93; == &#91;&#93;</code> (4 en fuente). | Aprobado |
| **CT-M07-I-BE-005** | <code>test_missing_exercise_migration_does_not_silently_discard_data&#91;CATALOGO_RUTINA-ejercicios&#93;</code> · [test_trainer_exercises.py:159](../../../../../backend/tests/rutinas_progreso/integracion/test_trainer_exercises.py#L159) | Preparación local de la función.; parámetros: <code>table</code>, <code>column</code> | <code>pytest.raises(RuntimeError, match="012_trainer_exercises.sql")</code> (1 en fuente). | Aprobado |
| **CT-M07-I-BE-006** | <code>test_missing_exercise_migration_does_not_silently_discard_data&#91;RUTINA_PROGRESO-ejercicios_detalle&#93;</code> · [test_trainer_exercises.py:159](../../../../../backend/tests/rutinas_progreso/integracion/test_trainer_exercises.py#L159) | Preparación local de la función.; parámetros: <code>table</code>, <code>column</code> | <code>pytest.raises(RuntimeError, match="012_trainer_exercises.sql")</code> (1 en fuente). | Aprobado |
| **CT-M07-I-BE-007** | <code>test_assignment_does_not_swallow_unknown_database_errors</code> · [test_trainer_exercises.py:166](../../../../../backend/tests/rutinas_progreso/integracion/test_trainer_exercises.py#L166) | Fixtures: <code>monkeypatch</code> | <code>pytest.raises(RuntimeError, match="database unavailable")</code> (1 en fuente). | Aprobado |

### Frontend

#### trainer-refresh-errors.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M07-I-FE-001** | <code>a confirmed assignment closes its dialog and reports a subsequent refresh failure separately</code> · [trainer-refresh-errors.test.js:11](../../../../../frontend/tests/rutinas_progreso/integracion/trainer-refresh-errors.test.js#L11) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(saves, 1)</code>; <code>assert.equal(assignments.showAssignModal.value, false)</code>; <code>assert.equal(assignments.assigningId.value, 0)</code> (5 en fuente). | Aprobado |
| **CT-M07-I-FE-002** | <code>a confirmed unassignment closes its confirmation even when reloading fails</code> · [trainer-refresh-errors.test.js:26](../../../../../frontend/tests/rutinas_progreso/integracion/trainer-refresh-errors.test.js#L26) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(saves, 1)</code>; <code>assert.equal(assignments.showConfirmModal.value, false)</code>; <code>assert.equal(notices&#91;0&#93;&#91;1&#93;, 'info')</code> (3 en fuente). | Aprobado |
| **CT-M07-I-FE-003** | <code>confirmed progress clears its saved draft and reports refresh failure without offering a duplicate save</code> · [trainer-refresh-errors.test.js:38](../../../../../frontend/tests/rutinas_progreso/integracion/trainer-refresh-errors.test.js#L38) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(saves, 1)</code>; <code>assert.equal(progress.showExercisesModal.value, false)</code>; <code>assert.equal(progress.observationsMap&#91;1&#93;, undefined)</code> (7 en fuente). | Aprobado |

## Pruebas de interfaz

### Frontend

#### flujos.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M07-F-FE-001** | <code>direct assignment and assignment dialog use the same validated save flow</code> · [flujos.test.js:6](../../../../../frontend/tests/rutinas_progreso/interfaz/flujos.test.js#L6) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(calls.length, 0)</code>; <code>assert.match(s.feedback, /no corresponde/)</code>; <code>assert.deepEqual(calls, &#91;&#91;7, 2&#93;&#93;)</code> (10 en fuente). | Aprobado |
| **CT-M07-F-FE-002** | <code>progress keeps its draft on failure and clears it only after a confirmed save</code> · [flujos.test.js:49](../../../../../frontend/tests/rutinas_progreso/interfaz/flujos.test.js#L49) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(s.showExercisesModal, true)</code>; <code>assert.equal(s.getTracker(7, 1)&#91;0&#93;.series_completadas, 3)</code>; <code>assert.equal(s.observationsMap&#91;7&#93;, 'Buena técnica')</code> (8 en fuente). | Aprobado |
| **CT-M07-F-FE-003** | <code>trainer renders extracted dialogs, exercises and progress history with working form models</code> · [flujos.test.js:85](../../../../../frontend/tests/rutinas_progreso/interfaz/flujos.test.js#L85) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.match(harness.html, /Avance guardado/)</code>; <code>assert.match(harness.dialogs, /Sentadilla/)</code>; <code>assert.match(harness.dialogs, /Guardar Progreso de Sesión/)</code> (13 en fuente). | Aprobado |
| **CT-M07-F-FE-004** | <code>unassigning another enrollment keeps the exercise draft and preserves confirmation on failure</code> · [flujos.test.js:135](../../../../../frontend/tests/rutinas_progreso/interfaz/flujos.test.js#L135) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(s.selectedMatriculaItem.id_matricula, 7)</code>; <code>assert.deepEqual(calls, &#91;&#91;8, 0&#93;&#93;)</code>; <code>assert.equal(s.showConfirmModal, true)</code> (6 en fuente). | Aprobado |
| **CT-M07-F-FE-005** | <code>one rest timer supports pause, resume, completion and disposal without leaked intervals</code> · [flujos.test.js:167](../../../../../frontend/tests/rutinas_progreso/interfaz/flujos.test.js#L167) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(timer.seconds, 2)</code>; <code>assert.equal(timer.seconds, 2)</code>; <code>assert.equal(timer.seconds, 0)</code> (8 en fuente). | Aprobado |
