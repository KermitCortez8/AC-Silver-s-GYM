# MOD-07 · Rutinas y progreso · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

5 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-07](../../../../base/modulos/07-rutinas-progreso.md). Actores: Admin, staff y trainer; actor resuelto por la sesión.

## Pruebas unitarias

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M07-01** · Unitaria e integración / fronteras · CA-04 | Ejercicios con peso cero, negativo y datos anidados sin identidad. | Validar esquema y ejecutar comandos directos. | Cero se conserva; negativos y estructuras inválidas fallan antes de mutar catálogo/historial. | [test_partial_smell_fixes.py](../../../../../backend/tests/transversales/integracion/test_partial_smell_fixes.py): `test_exercise_weights_reject_negatives_and_preserve_zero` |

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M07-02** · Integración HTTP / catálogo e historial · CA-01 | Trainer autorizado, rutina con ejercicios y registro de progreso detallado. | Guardar rutina, asignar y guardar progreso; volver a consultar catálogo e historial. | Ejercicios y sus detalles sobreviven serialización/recarga; esquema ausente no se oculta descartando datos. | [test_trainer_exercises.py](../../../../../backend/tests/rutinas_progreso/integracion/test_trainer_exercises.py) |
| **CP-M07-03** · Integración / asignación · CA-02 | Matrícula/horario activos y rutina del mismo servicio; variantes de matrícula inactiva, horario inactivo o servicio distinto. | Intentar asignar rutina en cada variante. | Solo se guarda la combinación compatible; los rechazos no dejan asignación parcial. | [test_schedule_enrollment.py](../../../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_assigns_matching_routine_to_active_enrollment_and_schedule` |
| **CP-M07-04** · Integración HTTP / actor · CA-03 | Sesión trainer T1 y payload de progreso con actor T2 o actor ausente. | Guardar ambos casos y consultar actor persistido. | Se registra T1, resuelto desde la sesión, sin aceptar suplantación del payload. | [test_review_regressions.py](../../../../../backend/tests/transversales/integracion/test_review_regressions.py): `test_progress_uses_the_authenticated_trainer_even_if_the_actor_is_spoofed_or_missing` |

## Pruebas de interfaz y navegación

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M07-05** · Interfaz / borrador y descanso · CA-05 | Monitor con ejercicio en edición, progreso fallido y temporizador activo. | Reintentar progreso; asignar/desasignar; pausar, reanudar y desmontar temporizador. | El error conserva borrador; solo se limpia al confirmar; un refresco posterior fallido no ofrece guardar otra vez lo ya guardado; al desmontar no quedan intervalos. | [rutinas_progreso · flujos.test.js](../../../../../frontend/tests/rutinas_progreso/interfaz/flujos.test.js); [trainer-refresh-errors.test.js](../../../../../frontend/tests/rutinas_progreso/integracion/trainer-refresh-errors.test.js) |
