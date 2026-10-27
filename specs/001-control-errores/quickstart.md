# Ejecutar el piloto

## Spec Kit

La CLI está instalada localmente en `.tools/spec-kit`. En otro checkout, desde
la raíz, con Python 3.11+, venv, pip, Git y acceso de descarga:

```bash
bash scripts/setup-spec-kit.sh
bash scripts/specify version
```

Los archivos de integración y las skills ya se versionan: no hace falta repetir
`init`. La instalación local se ignora en Git. El script no modifica el PATH ni
las dependencias de la aplicación.

Seleccionar el piloto para los scripts oficiales:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/001-control-errores
bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
```

Se espera la ruta del piloto y sus documentos. Esto verifica presencia de
artefactos; no ejecuta ni demuestra sus criterios de aceptación.

En el chat del agente configurado, ejecutar una skill por paso:

```text
$speckit-analyze
$speckit-implement
$speckit-converge
```

Para este piloto, empezar por las tareas abiertas y leer la evidencia. Las
skills no son órdenes de terminal. Si el cliente no permite seleccionarlas,
referenciar el `SKILL.md` correspondiente y los documentos del piloto.
El archivo `.specify/feature.json` es estado local ignorado; se puede usar la
variable anterior en cada nueva sesión sin cambiar de rama Git.

## Pruebas de la aplicación

Frontend instalado con `npm ci` desde `frontend/`:

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

Subset del piloto desde `frontend/`:

```bash
node --test tests/23-layer-boundaries.test.js tests/26-stock-edit-forms.test.js tests/31-module-error-control.test.js tests/32-http-error-control.test.js tests/33-trainer-refresh-errors.test.js tests/34-form-validation.test.js tests/35-response-identifiers.test.js
```

Backend: crear y activar un venv como en README e instalar
`backend/requirements-dev.txt`. Desde `backend/`, usar la clave sintética de CI:

```bash
AUTH_SECRET_KEY=ci-only-test-key-not-for-production-0123456789abcdef python -m pytest tests/test_module_error_control.py tests/test_basic_form_validation.py tests/test_layer_boundaries.py -q
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

Para una entrega funcional completa ejecutar también la suite backend y las
comprobaciones adicionales afectadas. SQL/concurrencia requiere el contenedor
PostgreSQL aislado del workflow de PR; un test omitido no lo demuestra.

## Comprobación observable

1. Con datos sintéticos cargados, simular una consulta fallida y comprobar que
   conserva los datos y libera la carga.
2. En un formulario, provocar un rechazo y comprobar borrador y error por campo.
3. Bloquear una confirmación de escritura y comprobar el aviso antes de repetir.
4. Confirmar progreso y hacer fallar solo la recarga: se informa de ambos estados.
5. Para ERR-009, añadir y ejecutar los casos nuevos de T013 antes de cambiar código.

Registrar cada ejecución, revisión y límite en [verification.md](verification.md).
No usar servicios ni cuentas de producción para estos escenarios.
