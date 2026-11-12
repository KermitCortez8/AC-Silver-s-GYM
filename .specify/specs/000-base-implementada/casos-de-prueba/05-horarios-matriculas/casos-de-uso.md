# MOD-05 · Horarios y matrículas · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

8 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-05](../../../../base/modulos/05-horarios-matriculas.md). Actores: Cliente propio, administrador y personal autorizado.

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M05-01** · Integración / catálogo · CA-01 | Horario activo de servicio, rutina y cupo conocidos. | Consultar catálogo y comparar sus datos con el horario guardado. | Se exponen servicio/ejercicio, horas y plazas disponibles coherentes. | [test_schedule_enrollment.py](../../../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_schedule_catalog_includes_exercise_and_available_slots` |
| **CP-M05-02** · Integración HTTP / identidad · CA-03 | Sesión user de C1 y payload con id_cliente de C2. | Solicitar matrícula desde autoservicio y consultar quién quedó inscrito. | El servidor usa C1; el ID enviado no suplanta a C2. | [test_schedule_enrollment.py](../../../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_user_routes_always_use_client_from_authenticated_session` |
| **CP-M05-03** · Integración HTTP / cancelación · CA-04 | C1 y C2 con matrículas propias. | Como C1 intentar cancelar la de C2; cancelar después la propia. | La ajena se conserva; la propia se cancela y libera únicamente su plaza. | [test_schedule_enrollment.py](../../../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_client_can_only_cancel_own_enrollment` |
| **CP-M05-04** · Integración / RPC ausente · CA-05 | Repositorio simulado sin RPC especializada y ninguna matrícula previa. | Intentar matricular y revisar llamadas remotas/estado. | Se informa el fallo de persistencia; no se usa INSERT REST parcial ni se añade matrícula local. | [test_schedule_enrollment.py](../../../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_enrollment_requires_atomic_rpc_before_writing` |
| **CP-M05-05** · Integración / fechas inválidas · CA-08 | Horario de lunes; membresía cubre D; datos de fecha imposible, pasada, otro día y fuera de vigencia. | Intentar una matrícula por cada variante y contar inscripciones antes/después. | Todas se rechazan sin insertar ni consumir cupos; una fecha de otra semana válida sigue siendo reservable. | [test_schedule_sessions.py](../../../../../backend/tests/horarios_matriculas/integracion/test_schedule_sessions.py) |

## Pruebas PostgreSQL y concurrencia

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M05-06** · PostgreSQL / concurrencia · CA-02 | Sesión D con un cupo y C1/C2 habilitados. | Enviar ambas matrículas en paralelo y repetir la del ganador. | Solo una matrícula ocupa la plaza; duplicar la misma sesión se rechaza sin superar cupo. | [test_schedule_sessions_postgres.py](../../../../../backend/tests/horarios_matriculas/postgres/test_schedule_sessions_postgres.py): `test_rpc_concurrencia_no_sobrepasa_cupo_de_la_sesion` |
| **CP-M05-07** · PostgreSQL / sesiones · CA-07 | Mismo horario con sesiones D y D+7, cada una de un cupo. | Matricular C1 en ambas; cancelar solo D; consultar listas/cupos en ambas fechas. | Las sesiones no heredan clientes ni cancelaciones; D libera cupo y D+7 conserva su reserva. | [test_schedule_sessions_postgres.py](../../../../../backend/tests/horarios_matriculas/postgres/test_schedule_sessions_postgres.py): `test_rpc_aisla_duplicados_cupos_y_cancelaciones_por_fecha` |

## Pruebas de interfaz y navegación

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M05-08** · Interfaz / respuesta obsoleta · CA-06 | Lectura A iniciada antes de guardar/cancelar; lectura B posterior al cambio. | Confirmar mutación; resolver primero B y luego A; volver a la pestaña visible. | La respuesta antigua no repone ni elimina matrículas confirmadas; el portal vuelve a consultar y conserva el último estado válido ante fallo. | [module-error-control.test.js](../../../../../frontend/tests/transversales/integracion/module-error-control.test.js) |
