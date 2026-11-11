# Controles transversales · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

4 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Actores: Sesiones y proveedores sintéticos; mantenedor para el control documental.

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-TR-01** · Integración HTTP / seguridad · Transversal | Roles/datos sintéticos y servicios de todos los módulos que lanzan error con centinela privada. | Invocar rutas parametrizadas con indisponibilidad, error de negocio y validación inválida. | Se conserva el estado HTTP previsto (400/403/404/409/422/503 según causa), mensajes legibles y ausencia de valores privados en respuesta. | [test_module_error_control.py](../../../../../backend/tests/transversales/integracion/test_module_error_control.py) |
| **CP-TR-02** · Integración frontend / resultado incierto · Transversal | Escritura cuyo encabezado llega pero cuerpo de confirmación queda bloqueado. | Esperar timeout y comprobar número de solicitudes y estado publicado. | No hay reintento automático ni éxito falso; se informa resultado no confirmado para reconciliar antes de repetir. | [http-error-control.test.js](../../../../../frontend/tests/transversales/integracion/http-error-control.test.js): `a write with stalled confirmation keeps the uncertain outcome and is not retried` |

## Pruebas PostgreSQL y concurrencia

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-TR-03** · PostgreSQL / rollback · Transversal | Instantánea válida y una operación compuesta; variante con snapshot obsoleto. | Inyectar fallo intermedio; después intentar commit obsoleto. | Ningún recurso queda parcialmente modificado y el conflicto no habilita escritura REST alternativa. | [test_atomic_transactions_postgres.py](../../../../../backend/tests/transversales/postgres/test_atomic_transactions_postgres.py): `test_transaction_rolls_back_deletes_details_and_updates_on_failure` |

## Pruebas de arquitectura y documentación

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-TR-04** · Documental / arquitectura · Transversal | Inventario, criterios y referencias de esta entrega. | Validar enlaces/estructura; contrastar archivos de pruebas y referencias; comprobar diff. | Los 99 archivos están catalogados, los criterios de once módulos tienen casos y el cambio se limita a documentación; controles estáticos no se presentan como aceptación funcional. | [test_integration.py](../../../../tests/test_integration.py) |
