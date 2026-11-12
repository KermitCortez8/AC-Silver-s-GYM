# MOD-01 · Identidad y acceso · Casos de uso

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

6 escenarios agrupados de recorridos y reglas, ordenados por tipo de prueba.
La preparación y los criterios comunes están en el
[índice](../indice.md#preparación-y-registro-de-los-escenarios-agrupados).
Consultar también los [casos individuales](casos-de-prueba.md) de este módulo.
Los escenarios se conservan como batería de aceptación agrupada pendiente;
los resultados individuales tienen su propio registro de ejecución.

Contrato y criterios: [MOD-01](../../../../base/modulos/01-identidad-acceso.md). Actores: Personal interno, cliente y visitante.

## Pruebas de integración

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M01-01** · Integración HTTP / seguridad · CA-01 | Personal activo con contraseña válida y token emitido. | Ingresar; desactivar la cuenta; repetir login y petición protegida con el token anterior. | Antes de desactivar hay sesión; después se deniegan ambos accesos sin publicar datos. | [test_review_regressions.py](../../../../../backend/tests/transversales/integracion/test_review_regressions.py): `test_disabling_an_internal_account_revokes_an_existing_session` |
| **CP-M01-02** · Integración / regla de acceso · CA-02 | C1 con cuenta marcada activa; variantes: sin membresía, impaga, futura o primera compra sin activación. | Solicitar acceso con contraseña en cada variante. | Ninguna variante concede sesión privada solo por tener el indicador de cuenta activo. | [test_membership_expiration.py](../../../../../backend/tests/membresias_pagos/integracion/test_membership_expiration.py): `test_active_flag_alone_does_not_allow_missing_unpaid_or_future_membership` |
| **CP-M01-03** · Integración / Google simulado · CA-03 | Identidad Google verificada por doble y cuenta interna inactiva vinculada o por vincular. | Autenticar e intentar vincular esa identidad. | Ambos intentos respetan la desactivación; Google no restablece el acceso. | [test_review_regressions.py](../../../../../backend/tests/transversales/integracion/test_review_regressions.py): `test_google_cannot_authenticate_or_link_an_inactive_internal_account` |
| **CP-M01-04** · Integración frontend / sesión · CA-05 | Consulta de C1 pendiente y sesión siguiente C2 preparada. | Cerrar/cambiar sesión antes de resolver la consulta de C1; después resolverla. | Se vacían datos/colas de C1 y su respuesta tardía no modifica la sesión de C2. | [navigation-stores.test.js](../../../../../frontend/tests/transversales/integracion/navigation-stores.test.js): `logout clears all business state and pending old-session loads cannot restore it` |

## Pruebas PostgreSQL y concurrencia

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M01-05** · PostgreSQL / identidad · CA-04 | Usuario interno existente y permisos de servicio en base desechable. | Cambiar su rol; borrar; crear otro; recargar desde PostgreSQL. | El cambio de rol conserva el ID y el alta posterior no reutiliza el ID eliminado. | [test_atomic_transactions_postgres.py](../../../../../backend/tests/transversales/postgres/test_atomic_transactions_postgres.py): `test_user_ids_survive_role_change_and_are_not_reused_after_delete` |

## Pruebas de interfaz y navegación

| Caso · tipo · criterio | Dado: preparación | Cuando: pasos | Entonces: resultado esperado | Referencia disponible |
| --- | --- | --- | --- | --- |
| **CP-M01-06** · Router / navegador · CA-06 | Variantes admin, staff, trainer, user y sesión vencida. | Volver del panel a / y sus anclas; abrir panel de otro rol; con token vencido intentar ruta privada. | La landing sigue accesible; no cambia el rol ni concede panel ajeno; la caducidad conserva el motivo en login. | [public-navigation.test.js](../../../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js); [validation.md](../../../../base/validaciones/navegacion-publica/validation.md) |
