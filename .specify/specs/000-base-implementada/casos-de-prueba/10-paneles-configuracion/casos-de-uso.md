# MOD-10 · Paneles y configuración · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

6 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-10](../../../../base/modulos/10-paneles-configuracion.md). Actores: Cada rol en su panel; admin/staff en resumen/configuración internos.

## Pruebas unitarias

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M10-01** · Unitaria / fechas · CA-02 | Reloj cerca de medianoche UTC que aún es día anterior en Lima y pagos en límite de mes. | Calcular resumen diario y serie de siete días. | Agrupación usa America/Lima y conserva exactamente las fechas de negocio esperadas. | [client-dashboard.test.js](../../../../../frontend/tests/paneles_configuracion/unitarias/client-dashboard.test.js): `daily dashboard and seven day chart use Peru time across UTC and month boundaries` |

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M10-02** · Integración / indicadores · CA-01 | Membresías activas pagadas, impagas, futuras y vencidas, incluidas etiquetas históricas. | Consultar resumen y contrastar contador con entidades fuente. | Solo las pagadas vigentes se cuentan activas; pendientes/activables/vencidas se distinguen. | [test_review_regressions.py](../../../../../backend/tests/transversales/integracion/test_review_regressions.py): `test_summary_counts_only_paid_current_memberships_with_canonical_and_legacy_states` |
| **CP-M10-03** · Integración / consultas acotadas · CA-03 | Transporte remoto simulado registra tablas consultadas y estados de otras secciones. | Abrir usuarios, pagos y asistencia; consultar health; provocar fallo de una lectura. | Cada sección lee sus dependencias, health no materializa historiales y el fallo conserva estado previo sin invalidar áreas ajenas. | [test_supabase_refresh.py](../../../../../backend/tests/paneles_configuracion/integracion/test_supabase_refresh.py): `test_sections_load_only_needed_tables_and_preserve_other_sections` |
| **CP-M10-04** · Integración frontend / aislamiento · CA-04 | Dos aplicaciones Pinia con adaptadores/sesiones independientes y consultas pendientes. | Configurar segunda app, cambiar sesión y resolver respuestas de la primera. | Los servicios/respuestas siguen su instancia; no se mezclan transportes ni datos de sesión. | [application-context.test.js](../../../../../frontend/tests/paneles_configuracion/integracion/application-context.test.js) |
| **CP-M10-05** · Integración HTTP / configuración · CA-01, CA-03 | Configuración válida guardada y sesión administrativa. | Intentar capacidad cero/inválida; recargar configuración. | Se informa error sin convertir cero en uno ni guardar una configuración parcial; permanece el último valor válido. | [test_module_error_control.py](../../../../../backend/tests/transversales/integracion/test_module_error_control.py): `test_invalid_capacity_does_not_silently_become_one_or_partially_change_settings` |

## Pruebas de interfaz y navegación

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M10-06** · Interfaz / navegación · CA-05 | Vista anterior con consulta lenta y transición nueva por módulo. | Cambiar de sección; resolver luego la transición anterior; desmontar. | La consulta ajena no bloquea el módulo; finalización vieja no cierra transición nueva y se limpian temporizadores. | [module-navigation.test.js](../../../../../frontend/tests/paneles_configuracion/integracion/module-navigation.test.js) |
