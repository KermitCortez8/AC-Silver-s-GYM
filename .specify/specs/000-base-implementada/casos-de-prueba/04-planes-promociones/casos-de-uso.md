# MOD-04 · Planes y promociones · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

6 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-04](../../../../base/modulos/04-planes-promociones.md). Actores: Visitante para consulta, admin/staff para planes y admin para promociones.

## Pruebas unitarias

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M04-01** · Unitaria / vigencia · CA-01 | Promociones actual, futura, vencida e incompatible con el plan. | Consultar promociones públicas y cotizar un plan para D. | Se publican/aplican únicamente las promociones elegibles por plan y fecha. | [test_promocion_navidad.py](../../../../../backend/tests/planes_promociones/unitarias/test_promocion_navidad.py): `test_promociones_vigentes_publicas_and_autoapply` |
| **CP-M04-02** · Unitaria / cupos · CA-02 | Promoción con límite de un uso y dos solicitudes válidas. | Consumir último cupo; intentar otra compra promocional. | No se concede un cupo adicional ni se deja un descuento no autorizado. | [test_promocion_cupos.py](../../../../../backend/tests/planes_promociones/unitarias/test_promocion_cupos.py): `test_promocion_limite_cupos_exhaustion` |
| **CP-M04-03** · Unitaria / conflicto · CA-03 | Promoción vigente y segunda promoción incompatible en fechas solapadas. | Guardar la segunda y consultar el catálogo resultante. | Se rechaza el conflicto y se conserva la promoción inicial sin cambios parciales. | [test_promocion_navidad.py](../../../../../backend/tests/planes_promociones/unitarias/test_promocion_navidad.py): `test_prevent_promocion_overlap` |
| **CP-M04-04** · Unitaria / formulario · CA-01, CA-05 | Plan nuevo y plan histórico con precio cero y duración guardada. | Elegir duración predefinida; validar campos requeridos; editar sin perder duración; intentar una duración inválida. | Se aceptan duraciones válidas y precio cero explícito, se conserva la duración histórica y se rechaza una inválida con mensaje de campo. | [membership-plan-form.test.js](../../../../../frontend/tests/planes_promociones/unitarias/membership-plan-form.test.js); [plan-directory.test.js](../../../../../frontend/tests/planes_promociones/integracion/plan-directory.test.js) |

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M04-05** · Integración / promoción administrativa · CA-04 | Alta administrativa con plan de S/100, sin promoción seleccionada; variante con promoción inválida. | Enviar ambas variantes. | La primera cobra precio sin descuento automático; la inválida impide crear cliente/membresía. | [test_admin_client_payment.py](../../../../../backend/tests/clientes/integracion/test_admin_client_payment.py): `test_admin_does_not_apply_unselected_promotion` |

## Pruebas PostgreSQL y concurrencia

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M04-06** · PostgreSQL / recarga · CA-05 | Promoción aplicada y membresía guardada con importe descontado. | Guardar, recargar desde base y modificar después el precio del plan. | Se preservan campos y asociación de promoción; el importe contratado no se recalcula. | [test_atomic_transactions_postgres.py](../../../../../backend/tests/transversales/postgres/test_atomic_transactions_postgres.py): `test_promotions_and_membership_association_survive_database_reload` |
