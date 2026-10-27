# Evidencia de adopción y base del piloto

Fecha: 27 de octubre de 2026.
Revisión base: `a2c95025a77080bf1c5f99365f04391f42a634f3` más los cambios locales
preexistentes del transporte, identificadores y sus tests. Esta entrega no
modifica esos cuatro archivos; se verificaron sus SHA-256 antes y después.

## Resultado de la integración

Spec Kit 1.2.3 instalado y operativo, con diez skills oficiales para Codex,
scripts Bash, plantillas, constitución y artefactos del piloto. La procedencia
del paquete instalado corresponde al commit oficial
`5ea8b1cf0a38699340a38e00d02770308997d8c0`. Se comprobó con `git ls-remote`:
la etiqueta anotada `v1.2.3` tiene su propio identificador, y el commit indicado
es el valor resuelto de `refs/tags/v1.2.3^{}`.

| Comprobación | Resultado |
| --- | --- |
| `bash scripts/specify version` | CLI 1.2.3 disponible. |
| `bash scripts/setup-spec-kit.sh` | Instalación local ejecutada; versión y procedencia comprobadas. |
| `bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks` | Resuelve el piloto y sus documentos. |
| `bash -n scripts/setup-spec-kit.sh scripts/specify` | Sin errores de sintaxis. |
| SHA-256 de archivos oficiales contra manifiestos instalados | 22 archivos coinciden, incluidas las diez skills. |
| Hashes de los cuatro archivos de aplicación/test preexistentes | Sin cambios durante esta adopción. |
| `git diff --check` | Sin errores en los cambios versionados. |

El contexto del piloto se seleccionó con
`SPECIFY_FEATURE_DIRECTORY=specs/001-control-errores`. CI tiene el mismo contexto
y ejecutará su comprobación estructural en PR; no se afirma una ejecución remota
de GitHub Actions desde esta sesión.

## Pruebas de la aplicación

| Comando desde la raíz, salvo indicación | Resultado observado |
| --- | --- |
| `npm --prefix frontend test` | Ejecución final: 35 archivos aprobados, sin fallos. El runner informó por archivo; no se contabilizan como 35 casos individuales. |
| `npm --prefix frontend run build` | Compilación de producción correcta. |
| `node --test tests/23-layer-boundaries.test.js tests/26-stock-edit-forms.test.js tests/31-module-error-control.test.js tests/32-http-error-control.test.js tests/33-trainer-refresh-errors.test.js tests/34-form-validation.test.js tests/35-response-identifiers.test.js`, desde `frontend/` | Los siete archivos seleccionados pasaron. |
| `AUTH_SECRET_KEY=ci-only-test-key-not-for-production-0123456789abcdef .tools/backend-tests/bin/python -m pytest backend/tests/test_module_error_control.py backend/tests/test_basic_form_validation.py backend/tests/test_layer_boundaries.py -q` | 153 pruebas aprobadas. |
| `AUTH_SECRET_KEY=ci-only-test-key-not-for-production-0123456789abcdef .tools/backend-tests/bin/python -m pytest backend/tests/ -q` | 544 aprobadas; 15 omitidas por requerir PostgreSQL aislado. |
| `.tools/backend-tests/bin/python -m flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics` | 0 errores. |

Entorno: Node.js 24.21.0; backend de pruebas Python 3.12; CLI SDD Python 3.14.2.
Las dependencias backend se prepararon en un entorno local ignorado por Git.
La suite backend emitió una advertencia de deprecación del TestClient con httpx.

La primera ejecución completa del frontend, simultánea con la compilación,
informó un fallo de `28-application-context.test.js`. Ese archivo pasó aislado,
tanto directamente como con `node --test`; la suite completa pasó después sin
la compilación simultánea. No se atribuye una causa confirmada ni se oculta el
primer resultado.

Los primeros intentos de TestClient se bloquearon en el bucle AnyIO dentro del
sandbox y se interrumpieron; las ejecuciones aprobadas se hicieron fuera de ese
sandbox, con clave de prueba y un límite de 60 segundos. Esto no requirió cambios
en el código de la aplicación.

## Matriz de requisitos y brechas

| Requisito | Evidencia ejecutada | Alcance o pendiente |
| --- | --- | --- |
| ERR-001 | `32-http-error-control` y `35-response-identifiers` | Cuerpo completo, respuesta 204 e identidades válidas/inválidas evaluadas. |
| ERR-002 | `31-module-error-control` | Conservación del estado e indicadores en los casos existentes; T018 revisa cobertura de caché y mensaje por flujo. |
| ERR-003 | `31-module-error-control`, `35-response-identifiers` y formularios `26` | Conservación local evaluada; aviso de escritura con respuesta malformada pendiente en T007. |
| ERR-004 | `32-http-error-control` | Timeout, cuerpo bloqueado y ausencia de reintentos evaluados. |
| ERR-005 | `33-trainer-refresh-errors` | Asignación, desvinculación y progreso con recarga fallida evaluados. |
| ERR-006 | `test_module_error_control.py` y `32-http-error-control` | Estados y códigos evaluados con servicios simulados; sesión 401 y permisos reales pendientes en T009. |
| ERR-007 | `test_module_error_control.py` | Casos de validación, secretos y modelos internos evaluados. |
| ERR-008 | Formulario `26`, validación `34` y `test_basic_form_validation.py` | Evidencia automatizada existente aprobada; revisión visual/accesible pendiente en T010. |
| ERR-009 | No existe evidencia completa de la nueva semántica | T013 y T014 pendientes; el transporte actual no marca resultado incierto al cancelar una escritura. |

## Conclusión de la revisión de consistencia

Los cuatro puntos de adopción tienen artefactos concretos y el script oficial
resuelve sus prerrequisitos. Historias, requisitos y tareas mantienen vínculos
explícitos. La decisión D-01 ya está definida y su implementación permanece
señalada como pendiente en especificación, contrato y tareas.

**Adopción de Spec Kit: completada. Aceptación funcional del piloto: parcial.**
T018 permanece abierta. No se ha ejecutado una skill mediante una sesión externa
de agente ni se declara que una comprobación de presencia certifique semántica.

No se ejecutaron PostgreSQL, revisión visual, Deno ni integraciones externas en
esta adopción. No cambian SQL ni Edge Functions. Los quince tests omitidos no
demuestran atomicidad/concurrencia en esta ejecución; el trabajo PostgreSQL del
workflow existente mantiene su responsabilidad.
