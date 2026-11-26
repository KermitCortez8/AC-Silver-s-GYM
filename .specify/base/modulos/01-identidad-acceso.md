# MOD-01 · Identidad y acceso

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Permitir que clientes y personal accedan a su área mediante una sesión validada,
conservando restricciones de cuenta, membresía y rol.

## 2. User Story

**P1.** Como persona registrada, quiero ingresar con contraseña o Google para
usar las funciones autorizadas para mi cuenta. Como personal administrativo,
quiero mantener usuarios internos sin perder su identidad al cambiar su rol.

Prueba independiente: autenticar cuentas sintéticas, consultar `/api/auth/me`,
desactivar una cuenta y comprobar que su sesión deja de dar acceso.

## 3. Acceptance Criteria

1. **CA-01.** Dadas credenciales correctas de una cuenta interna activa, al
   autenticarse se emite una sesión; una cuenta inactiva no puede iniciar sesión
   ni reutilizar un token anterior.
2. **CA-02.** Dado un cliente sin membresía pagada y vigente o sin activación,
   al solicitar acceso se aplica el bloqueo del servicio de autenticación.
3. **CA-03.** Dada una identidad Google verificada, al autenticar/vincular se
   respetan la cuenta existente y sus restricciones de estado.
4. **CA-04.** Dado un usuario interno existente, al cambiar su rol se conserva
   su código; al eliminar y crear usuarios no se reutiliza la identidad.
5. **CA-05.** Dado un cambio/cierre de sesión, al llegar respuestas antiguas del
   frontend no se publican datos de la sesión previa.
6. **CA-06.** Con o sin sesión, la landing `/` y sus anclas siguen siendo públicas.
   Volver desde el panel o recargar la landing no cierra la sesión ni redirige al
   panel/login. Acceder explícitamente a `/login` con sesión válida recupera el
   panel del rol. La caducidad bloquea las rutas privadas y conserva su motivo.
7. **CA-07.** Configuración abre la ficha de consulta de la cuenta, con datos
   personales, código, rol, estado y métodos de acceso. Para clientes incluye
   la fecha de registro y la membresía que habilita su sesión. El botón «Editar
   datos» abre un diálogo con los campos para cambiar nombre, teléfono, correo,
   DNI y contraseña. Los datos de consulta se muestran en la ficha. El
   formulario guarda los cambios con la sesión vigente. La ficha muestra
   puntos fijos cuando existe una contraseña y el diálogo ofrece un solo campo
   para escribir la nueva.
   El servidor identifica la cuenta por la sesión verificada y aplica únicamente
   los campos enviados. El rol se administra desde Usuarios.
8. **CA-08.** En Inicio de sesión, «¿Perdiste tu contraseña? Recupera tu cuenta»
   aparece debajo de «Regístrate aquí». El modal pide el correo registrado.
   Si identifica una cuenta, el sistema envía un enlace temporal al correo.
   Un enlace vigente permite guardar una contraseña nueva una vez y volver
   al inicio de sesión.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_review_regressions.py](../../../backend/tests/transversales/integracion/test_review_regressions.py): `test_disabling_an_internal_account_revokes_an_existing_session`. |
| CA-02 | [test_membership_expiration.py](../../../backend/tests/membresias_pagos/integracion/test_membership_expiration.py): `test_active_flag_alone_does_not_allow_missing_unpaid_or_future_membership`. |
| CA-03 | [test_review_regressions.py](../../../backend/tests/transversales/integracion/test_review_regressions.py): `test_google_cannot_authenticate_or_link_an_inactive_internal_account`. |
| CA-04 | [test_priority_fixes.py](../../../backend/tests/transversales/integracion/test_priority_fixes.py): `test_user_identity_is_unique_across_roles_and_stable_after_role_change`; concurrencia en [PostgreSQL](../../../backend/tests/transversales/postgres/test_atomic_transactions_postgres.py). |
| CA-05 | [session-validation.test.js](../../../frontend/tests/identidad_acceso/integracion/session-validation.test.js) y [application-context.test.js](../../../frontend/tests/paneles_configuracion/integracion/application-context.test.js). |
| CA-06 | [public-navigation.test.js](../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js), [module-navigation.test.js](../../../frontend/tests/paneles_configuracion/integracion/module-navigation.test.js) y [validación en navegador](../validaciones/navegacion-publica/validation.md). |
| CA-07 | [test_perfil_propio.py](../../../backend/tests/identidad_acceso/integracion/test_perfil_propio.py), [perfil-propio.test.js](../../../frontend/tests/identidad_acceso/integracion/perfil-propio.test.js) y [validación de Configuración](../validaciones/perfil-propio/validation.md). |
| CA-08 | [test_recuperar_password.py](../../../backend/tests/identidad_acceso/integracion/test_recuperar_password.py) y [validación de recuperación](../validaciones/recuperar-password/validation.md). |

## 4. Technical Constraints

- API: [auth_routes.py](../../../backend/presentation/routes/auth_routes.py),
  [users_routes.py](../../../backend/presentation/routes/users_routes.py) y
  [dependencies.py](../../../backend/presentation/dependencies.py).
  `GET /api/auth/me` obtiene el perfil verificado y resume la membresía vigente
  del cliente usando la misma comprobación de acceso. `PATCH /api/auth/me` acepta
  `nombre`, `telefono`, `correo`, `dni` y `password_nueva` y devuelve el perfil
  actualizado. El servidor autoriza el cambio con la sesión firmada vigente.
  Las solicitudes que incluyen `password_actual` o `google_credential` usan la
  comprobación de esa credencial. La transacción comprueba correo y DNI frente
  a las cuentas internas, clientes y preregistros pendientes.
- Recuperación usa `POST /api/auth/recuperar-contrasena` y
  `POST /api/auth/restablecer-contrasena`. El enlace usa una firma y vigencia
  propias. Al guardar, la transacción comprueba el estado de la cuenta antes
  de actualizar el hash. Se reutiliza la persistencia existente.
- Casos de uso: [auth_service.py](../../../backend/application/services/auth_service.py),
  [identity_service.py](../../../backend/application/services/identity_service.py),
  [users_service.py](../../../backend/application/services/users_service.py).
- Reglas: [accounts_rules.py](../../../backend/domain/services/accounts_rules.py).
  Datos de personal en `USUARIO`; clientes en `CLIENTES`. Roles internos
  `admin`, `staff`, `trainer`; el cliente se presenta con rol `user`.
- UI: [router](../../../frontend/src/presentation/router/index.js),
  [authStore.js](../../../frontend/src/application/stores/authStore.js) y
  [sessionStore.js](../../../frontend/src/application/stores/sessionStore.js).
  Rutas `/login`, `/auth/callback`, `/admin/users` y paneles por rol.

## 5. Guardrails

No deducir permisos solamente del correo o del menú. No exponer hashes ni
secretos. No confiar en un JWT decodificado sin verificación. No exigir membresía
al personal interno. No regenerar códigos por cambio de rol.

## 6. Edge Cases

- Token ausente, mal formado o vencido: rechazar acceso; cuenta interna
  desactivada: resolver otra vez su estado y denegarla.
- Google requiere vinculación: informar el conflicto específico; no crear
  silenciosamente una identidad alternativa.
- Cliente vencido: conservar historial de pago y denegar acceso; una renovación
  pagada y activada puede restaurarlo.
- Sesión sustituida durante una carga: descartar la respuesta anterior y vaciar
  estado/cachés de negocio según el límite de sesión.
- La sesión vence mientras se consulta una página pública: revocar la sesión sin
  sacar al visitante de esa página. Solicitar login al intentar una ruta privada.

## 7. Definition of Done

Para cambios de este módulo, verificar los criterios afectados, permisos HTTP y
aislamiento de sesión; actualizar este contrato y cumplir el [DoD](../../docs/DoD.md).
La evidencia de la tabla identifica pruebas disponibles, no una ejecución nueva.

### Límites de formularios

Los formularios de usuarios internos limitan nombre y correo a 50 caracteres,
DNI a 8 dígitos y teléfono a 9. Los datos de identidad opcionales admiten vacío;
si se completan deben tener su longitud exacta. La búsqueda general admite 50
caracteres. El navegador bloquea el exceso sin avisos ni contadores de longitud.

Evidencia: [validación de límites](../validaciones/limites-formularios/validation.md).
