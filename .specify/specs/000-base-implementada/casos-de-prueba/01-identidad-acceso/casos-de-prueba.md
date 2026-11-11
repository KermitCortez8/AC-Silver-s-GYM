# MOD-01 · Identidad y acceso · Casos individuales

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

29 casos individuales: 29 aprobados y 0 omitidos
registrados en la revisión del 2026-11-10. [Índice de módulos](../indice.md).
[Preparación, ejecución y lectura de resultados](../indice.md#cómo-leer-y-repetir-cada-caso).
[Escenarios de uso del módulo](casos-de-uso.md) y
[selectores/comandos estructurados](catalogo-pruebas.json).

## Pruebas unitarias

### Backend

#### test_security_utils.py

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-U-BE-001** | <code>test_get_user_role_returns_user_without_email</code> · [test_security_utils.py:24](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L24) | Preparación local de la función. | <code>get_user_role(None) == "user"</code> (1 en fuente). | Aprobado |
| **CT-M01-U-BE-002** | <code>test_get_user_role_marks_urp_email_as_admin</code> · [test_security_utils.py:28](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L28) | Preparación local de la función. | <code>get_user_role("persona@urp.edu.pe") == "admin"</code> (1 en fuente). | Aprobado |
| **CT-M01-U-BE-003** | <code>test_decode_token_payload_reads_jwt_payload</code> · [test_security_utils.py:32](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L32) | Preparación local de la función. | <code>decode_token_payload(_jwt_with_payload({"email": "a@b.com"})) == {"email": "a@b.com"}</code> (1 en fuente). | Aprobado |
| **CT-M01-U-BE-004** | <code>test_decode_token_payload_returns_none_for_invalid_token</code> · [test_security_utils.py:36](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L36) | Preparación local de la función. | <code>decode_token_payload("token-invalido") is None</code> (1 en fuente). | Aprobado |
| **CT-M01-U-BE-005** | <code>test_normalize_profile_uses_email_prefix_as_name_fallback</code> · [test_security_utils.py:40](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L40) | Preparación local de la función. | <code>profile&#91;"name"&#93; == "cliente"</code> (1 en fuente). | Aprobado |
| **CT-M01-U-BE-006** | <code>test_get_expiry_seconds_uses_default_for_token_without_exp</code> · [test_security_utils.py:45](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L45) | Preparación local de la función. | <code>get_expiry_seconds(_jwt_with_payload({"sub": "abc"}), default_seconds=120) == 120</code> (1 en fuente). | Aprobado |
| **CT-M01-U-BE-007** | <code>test_hash_password_can_be_verified</code> · [test_security_utils.py:49](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L49) | Preparación local de la función. | <code>verify_password("secreto", stored) is True</code> (1 en fuente). | Aprobado |
| **CT-M01-U-BE-008** | <code>test_verify_password_rejects_wrong_password</code> · [test_security_utils.py:54](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L54) | Preparación local de la función. | <code>verify_password("otro", stored) is False</code> (1 en fuente). | Aprobado |
| **CT-M01-U-BE-009** | <code>test_create_local_token_contains_expected_profile_data</code> · [test_security_utils.py:59](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L59) | Preparación local de la función. | <code>payload&#91;"email"&#93; == "u1@example.com"</code>; <code>payload&#91;"exp"&#93; &gt;= int(time.time()) + 80</code> (2 en fuente). | Aprobado |
| **CT-M01-U-BE-010** | <code>test_normalize_profile_can_use_token_payload_when_profile_is_missing</code> · [test_security_utils.py:66](../../../../../backend/tests/identidad_acceso/unitarias/test_security_utils.py#L66) | Preparación local de la función. | <code>profile&#91;"id"&#93; == "abc"</code>; <code>profile&#91;"email"&#93; == "token@example.com"</code> (2 en fuente). | Aprobado |

### Frontend

#### decode-jwt.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-U-FE-001** | <code>tests/identidad_acceso/unitarias/decode-jwt.test.js</code> · [decode-jwt.test.js:1](../../../../../frontend/tests/identidad_acceso/unitarias/decode-jwt.test.js#L1) | Fixtures: <code>Aserciones de módulo</code> | <code>assert.deepEqual(decodeJWT(`header.${encodedPayload}.signature`), { email: 'cliente@example.com' })</code> (1 en fuente). | Aprobado |

#### default-membership.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-U-FE-002** | <code>tests/identidad_acceso/unitarias/default-membership.test.js</code> · [default-membership.test.js:1](../../../../../frontend/tests/identidad_acceso/unitarias/default-membership.test.js#L1) | Fixtures: <code>Aserciones de módulo</code> | <code>assert.equal(createDefaultMembership({ role: 'admin' }).plan, 'Acceso total')</code> (1 en fuente). | Aprobado |

#### format-user-data.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-U-FE-003** | <code>tests/identidad_acceso/unitarias/format-user-data.test.js</code> · [format-user-data.test.js:1](../../../../../frontend/tests/identidad_acceso/unitarias/format-user-data.test.js#L1) | Fixtures: <code>Aserciones de módulo</code> | <code>assert.equal(user.id, 'SGCLI001')</code>; <code>assert.equal(user.email, 'cliente@example.com')</code> (2 en fuente). | Aprobado |

#### invalid-email.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-U-FE-004** | <code>tests/identidad_acceso/unitarias/invalid-email.test.js</code> · [invalid-email.test.js:1](../../../../../frontend/tests/identidad_acceso/unitarias/invalid-email.test.js#L1) | Fixtures: <code>Aserciones de módulo</code> | <code>assert.equal(isValidEmail('cliente.example.com'), false)</code> (1 en fuente). | Aprobado |

#### user-role.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-U-FE-005** | <code>tests/identidad_acceso/unitarias/user-role.test.js</code> · [user-role.test.js:1](../../../../../frontend/tests/identidad_acceso/unitarias/user-role.test.js#L1) | Fixtures: <code>Aserciones de módulo</code> | <code>assert.equal(getUserRole('admin@urp.edu.pe'), 'admin')</code> (1 en fuente). | Aprobado |

#### valid-email.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-U-FE-006** | <code>tests/identidad_acceso/unitarias/valid-email.test.js</code> · [valid-email.test.js:1](../../../../../frontend/tests/identidad_acceso/unitarias/valid-email.test.js#L1) | Fixtures: <code>Aserciones de módulo</code> | <code>assert.equal(isValidEmail('cliente@example.com'), true)</code> (1 en fuente). | Aprobado |

#### valid-user.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-U-FE-007** | <code>tests/identidad_acceso/unitarias/valid-user.test.js</code> · [valid-user.test.js:1](../../../../../frontend/tests/identidad_acceso/unitarias/valid-user.test.js#L1) | Fixtures: <code>Aserciones de módulo</code> | <code>assert.equal(isValidUser({ id_usuario: 'SGCLI002', correo: 'cliente2@example.com' }), true)</code> (1 en fuente). | Aprobado |

## Pruebas de integración

### Frontend

#### public-navigation.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-I-FE-001** | <code>admin puede regresar del panel a la landing y sus secciones sin cerrar sesión</code> · [public-navigation.test.js:36](../../../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js#L36) | Fixtures: <code>Preparación y dobles del archivo fuente</code>; variante: <code>admin puede regresar del panel a la landing y sus secciones sin cerrar sesión</code> | <code>assert.equal(router.currentRoute.value.fullPath, '/')</code>; <code>assert.equal(router.currentRoute.value.fullPath, '/#membresias')</code>; <code>assert.equal(router.currentRoute.value.fullPath, '/#servicios')</code> (5 en fuente). | Aprobado |
| **CT-M01-I-FE-002** | <code>staff puede regresar del panel a la landing y sus secciones sin cerrar sesión</code> · [public-navigation.test.js:36](../../../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js#L36) | Fixtures: <code>Preparación y dobles del archivo fuente</code>; variante: <code>staff puede regresar del panel a la landing y sus secciones sin cerrar sesión</code> | <code>assert.equal(router.currentRoute.value.fullPath, '/')</code>; <code>assert.equal(router.currentRoute.value.fullPath, '/#membresias')</code>; <code>assert.equal(router.currentRoute.value.fullPath, '/#servicios')</code> (5 en fuente). | Aprobado |
| **CT-M01-I-FE-003** | <code>trainer puede regresar del panel a la landing y sus secciones sin cerrar sesión</code> · [public-navigation.test.js:36](../../../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js#L36) | Fixtures: <code>Preparación y dobles del archivo fuente</code>; variante: <code>trainer puede regresar del panel a la landing y sus secciones sin cerrar sesión</code> | <code>assert.equal(router.currentRoute.value.fullPath, '/')</code>; <code>assert.equal(router.currentRoute.value.fullPath, '/#membresias')</code>; <code>assert.equal(router.currentRoute.value.fullPath, '/#servicios')</code> (5 en fuente). | Aprobado |
| **CT-M01-I-FE-004** | <code>user puede regresar del panel a la landing y sus secciones sin cerrar sesión</code> · [public-navigation.test.js:36](../../../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js#L36) | Fixtures: <code>Preparación y dobles del archivo fuente</code>; variante: <code>user puede regresar del panel a la landing y sus secciones sin cerrar sesión</code> | <code>assert.equal(router.currentRoute.value.fullPath, '/')</code>; <code>assert.equal(router.currentRoute.value.fullPath, '/#membresias')</code>; <code>assert.equal(router.currentRoute.value.fullPath, '/#servicios')</code> (5 en fuente). | Aprobado |
| **CT-M01-I-FE-005** | <code>la landing también permite entrada directa con una sesión restaurada</code> · [public-navigation.test.js:53](../../../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js#L53) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(checks, 1)</code>; <code>assert.equal(router.currentRoute.value.path, '/')</code>; <code>assert.equal(auth.isAuthenticated, true)</code> (3 en fuente). | Aprobado |
| **CT-M01-I-FE-006** | <code>sin sesión se conserva el acceso público y se bloquean los paneles</code> · [public-navigation.test.js:63](../../../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js#L63) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(router.currentRoute.value.path, '/')</code>; <code>assert.equal(router.currentRoute.value.path, '/login')</code> (2 en fuente). | Aprobado |
| **CT-M01-I-FE-007** | <code>una membresía vencida mantiene el motivo en login al intentar abrir el panel</code> · [public-navigation.test.js:71](../../../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js#L71) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(router.currentRoute.value.fullPath, '/login?reason=membership_expired')</code>; <code>assert.equal(router.currentRoute.value.path, '/')</code> (2 en fuente). | Aprobado |
| **CT-M01-I-FE-008** | <code>visitar la landing no concede acceso a otros roles</code> · [public-navigation.test.js:82](../../../../../frontend/tests/identidad_acceso/integracion/public-navigation.test.js#L82) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(router.currentRoute.value.path, '/')</code>; <code>assert.equal(router.currentRoute.value.path, '/')</code>; <code>assert.equal(staffRouter.currentRoute.value.path, '/admin/dashboard')</code> (3 en fuente). | Aprobado |

#### session-validation.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M01-I-FE-009** | <code>navigation shares pending validation and reuses a recent server response</code> · [session-validation.test.js:5](../../../../../frontend/tests/identidad_acceso/integracion/session-validation.test.js#L5) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(first, second)</code>; <code>assert.equal(calls, 1)</code>; <code>assert.deepEqual(await validator.validate('session-a'), { role: 'admin' })</code> (6 en fuente). | Aprobado |
| **CT-M01-I-FE-010** | <code>changed tokens and forced checks bypass successful cached validation</code> · [session-validation.test.js:33](../../../../../frontend/tests/identidad_acceso/integracion/session-validation.test.js#L33) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.deepEqual(await validator.validate('b'), { token: 'b' })</code>; <code>assert.deepEqual(calls, &#91;'a', 'b', 'b'&#93;)</code> (2 en fuente). | Aprobado |
| **CT-M01-I-FE-011** | <code>failed validation is retried instead of granting a cached session</code> · [session-validation.test.js:45](../../../../../frontend/tests/identidad_acceso/integracion/session-validation.test.js#L45) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.rejects(validator.validate('a'), /desactivada/)</code>; <code>assert.rejects(validator.validate('a'), /desactivada/)</code>; <code>assert.equal(calls, 2)</code> (3 en fuente). | Aprobado |
| **CT-M01-I-FE-012** | <code>logout invalidates a pending check even when the same token is reused later</code> · [session-validation.test.js:56](../../../../../frontend/tests/identidad_acceso/integracion/session-validation.test.js#L56) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(calls, 2)</code>; <code>assert.deepEqual(await next, { name: 'Sesión actual' })</code> (2 en fuente). | Aprobado |
