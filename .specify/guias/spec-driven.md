# Flujo Spec Kit con Codex

El usuario decide cuándo activar Spec Kit. Por ahora los pedidos se resuelven
sin generar specs, planes ni tareas; esta guía describe el flujo disponible
para cuando lo solicite expresamente.

Usar las etapas oficiales sobre el gimnasio existente. La [estructura](estructura-codex.md)
conserva los elementos de la imagen y la [guía del chatbot](guia-spec-driven-chatbot.md)
incluye todos los prompts y comandos. No hay un runner adicional.

## Qué consulta Codex

Leer [AGENTS raíz](../../AGENTS.md), [índice central](../AGENTS.md),
[constitución](../memory/constitution.md), [base 000](../specs/000-base-implementada/spec.md),
[índice de módulos](../base/modulos/README.md) y los contratos afectados. Leer
arquitectura, diseño, seguridad, DoD, código y pruebas según el alcance.
Los informes de errores no añaden trabajo autorizado.

El índice y los contratos son la única fuente de módulos. El contexto se
completa por lectura de fuentes, no a partir de un segundo inventario automático.

## Etapas

| Etapa de chat | Resultado y componentes que utiliza |
| --- | --- |
| `$gym-spec-driven` | Consulta la base, distingue análisis de implementación y coordina el recorrido. |
| `$speckit-specify` | Crea o continúa una feature; completa contexto y siete componentes. |
| `$speckit-clarify` | Resuelve ambigüedades que afecten al comportamiento. |
| `$speckit-checklist` | Opcional: comprueba calidad de requisitos escritos. |
| `$speckit-plan` | Su script ejecuta el hook de plan y después prepara plan.md. |
| `$speckit-tasks` | Genera tareas con rutas y criterios de aceptación. |
| `$speckit-analyze` | Contrasta spec, plan y tareas; aplica el perfil de revisor. |
| `$speckit-implement` | Comprueba prerrequisitos y ejecuta las tareas y pruebas pertinentes. |
| `$speckit-converge` | Identifica trabajo del alcance todavía sin construir; se vuelve a implementar si lo hay. |
| Cierre | Aplica auditor, actualiza módulos y evidencia; ejecuta hook de cierre y comprobaciones. |

Las skills leen un [preámbulo compartido](../.codex/preamble.md). Las
[reglas](../.codex/rules/README.md) y los [ajustes](../.codex/settings.json) definen
qué consultar y los artefactos de cada etapa. Los [perfiles](../.codex/agents/README.md)
se aplican en la sesión actual, sin abrir agentes automáticamente.

## Scripts oficiales y hooks

Crear una sola feature con el generador oficial, o dejar que lo haga specify:

```bash
bash .specify/scripts/bash/create-new-feature.sh --json --short-name nombre-corto "Cambio solicitado"
```

El script crea `spec.md` y `context.md` en `.specify/specs/NNN-nombre/`.
Completar el contexto con módulos concretos, fuentes leídas, restricciones,
reutilización y pruebas; completar la spec con los siete componentes.
No volver a crear la feature al cambiar de etapa.

`setup-plan.sh` llama al [hook único](../.codex/hooks/validate.py) antes de escribir
el plan. `check-prerequisites.sh --require-tasks` llama al mismo hook para
implementación; las etapas analyze, implement y converge usan esos prerrequisitos.
Las salidas JSON oficiales se conservan; los mensajes del hook van a stderr.

Comprobaciones directas desde la raíz:

```bash
python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage plan
python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage implement
python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage close
python .specify/.codex/hooks/validate.py
python -B -m unittest discover -s .specify/tests -v
```

El hook comprueba archivos, enlaces y trazabilidad. Las suites de producto se
eligen según el [DoD](../docs/DoD.md); no se declaran aprobadas por pasar el hook.

## Retomar y mantener

Indicar la carpeta existente en el chat. En una terminal, los scripts oficiales
permiten seleccionar su ruta mediante la variable nativa:

```bash
export SPECIFY_FEATURE_DIRECTORY="$PWD/.specify/specs/NNN-nombre"
bash .specify/scripts/bash/check-prerequisites.sh --paths-only --json
```

La selección escrita por las operaciones oficiales se conserva en feature.json,
ignorado por Git. La lectura --paths-only no lo modifica. Los punteros antiguos
se normalizan a la ruta real sin recrear un enlace raíz.

No regenerar la constitución por cada feature. `$speckit-constitution` se usa
cuando se solicita cambiar principios. `$speckit-taskstoissues` está obsoleta;
crear issues requiere su propia petición. No se usan workflows CLI que abran
sesiones adicionales. La instalación opcional del CLI está en el [índice](../README.md).
La [procedencia](../UPSTREAM.md) registra las adaptaciones locales.
