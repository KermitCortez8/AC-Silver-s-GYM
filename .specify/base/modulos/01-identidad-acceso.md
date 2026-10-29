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

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_review_regressions.py](../../../backend/tests/test_review_regressions.py): `test_disabling_an_internal_account_revokes_an_existing_session`. |
| CA-02 | [test_membership_expiration.py](../../../backend/tests/test_membership_expiration.py): `test_active_flag_alone_does_not_allow_missing_unpaid_or_future_membership`. |
| CA-03 | [test_review_regressions.py](../../../backend/tests/test_review_regressions.py): `test_google_cannot_authenticate_or_link_an_inactive_internal_account`. |
| CA-04 | [test_priority_fixes.py](../../../backend/tests/test_priority_fixes.py): `test_user_identity_is_unique_across_roles_and_stable_after_role_change`; concurrencia en [PostgreSQL](../../../backend/tests/test_atomic_transactions_postgres.py). |
| CA-05 | [14-session-validation.test.js](../../../frontend/tests/14-session-validation.test.js) y [28-application-context.test.js](../../../frontend/tests/28-application-context.test.js). |

## 4. Technical Constraints

- API: [auth_routes.py](../../../backend/presentation/routes/auth_routes.py),
  [users_routes.py](../../../backend/presentation/routes/users_routes.py) y
  [dependencies.py](../../../backend/presentation/dependencies.py).
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

## 7. Definition of Done

Para cambios de este módulo, verificar los criterios afectados, permisos HTTP y
aislamiento de sesión; actualizar este contrato y cumplir el [DoD](../../docs/DoD.md).
La evidencia de la tabla identifica pruebas disponibles, no una ejecución nueva.
