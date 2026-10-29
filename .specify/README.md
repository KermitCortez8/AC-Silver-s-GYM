# Spec Driven de AC Silver's GYM

El usuario decide cuándo activar Spec Kit. Por ahora los pedidos se resuelven
sin generar specs, planes ni tareas; esta guía describe el flujo disponible
para cuando lo solicite expresamente.

Una sola forma de trabajo: las skills y scripts oficiales de Spec Kit, con la
base del gimnasio y un único hook de validación. El [índice](AGENTS.md) enlaza
las reglas y documentos que Codex debe consultar antes de programar.

```text
.specify/
├── AGENTS.md
├── AGENTS.local.md             # local e ignorado por Git
├── AGENTS.local.md.example
├── docs/                       # solo los cinco documentos del equipo
│   ├── arquitectura.md
│   ├── diseno.md
│   ├── DoD.md
│   ├── Backlog.md
│   └── RETRO_ACTIONS.md
├── .codex/
│   ├── rules/                  # reglas comunes y por rutas
│   ├── settings.json           # reglas, artefactos de etapas y perfiles
│   ├── hooks/validate.py        # implementación única de validación
│   ├── agents/                 # revisor y auditor para esta sesión
│   ├── skills/                 # gym-spec-driven y diez etapas oficiales
│   └── preamble.md             # instrucciones comunes, referenciadas una sola vez
├── base/modulos/               # índice y contratos: fuente única de módulos
├── guias/                      # flujo y ejemplo completo del chatbot
├── specs/                      # base 000 y cambios numerados
├── memory/constitution.md
├── templates/overrides/        # contexto, siete componentes, plan y tareas
├── scripts/bash/               # scripts oficiales con ajustes locales registrados
├── tests/                      # regresiones de scripts y hook
├── integrations/               # procedencia, hashes y dependencia fijada del CLI
└── .venv/                      # CLI local, ignorado y oculto en el explorador
```

[AGENTS.md raíz](../AGENTS.md) es la entrada nativa. `.agents/skills/*` enlaza a
`.specify/.codex/skills/*`. `.github/` se conserva separada. No hay carpetas ni
enlaces docs/specs en la raíz. El archivo local complementa las reglas porque
los índices requieren leerlo; no sustituye el índice compartido.

## Flujo

`gym-spec-driven → specify → clarify → plan → tasks → analyze → implement → converge → cierre`.
Las etapas `speckit-*` se invocan con `$` en el chat de Codex. Consultar la
[guía general](guias/spec-driven.md), los [comandos con ejemplo de chatbot](guias/guia-spec-driven-chatbot.md)
y la [estructura](guias/estructura-codex.md).

El generador oficial prepara spec y contexto. El hook se ejecuta desde
setup-plan antes de crear el plan y desde los prerrequisitos que requieren tareas.
Revisor se aplica en análisis y auditor antes de cerrar, dentro de esta sesión.
Las pruebas del producto se eligen según el [DoD](docs/DoD.md).

```bash
python .specify/.codex/hooks/validate.py
python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage close
python -B -m unittest discover -s .specify/tests -v
```

## CLI y entorno local

El flujo y sus comprobaciones requieren Python 3.11+ y Bash; no necesitan un
CLI instalado. Para usar también las funciones del CLI fijado en un clon nuevo:

```bash
python -m venv .specify/.venv
.specify/.venv/bin/python -m pip install -r .specify/integrations/requirements.txt
.specify/.venv/bin/specify version
```

En Windows, usar WSL o un entorno con Bash y enlaces simbólicos operativos.
El entorno existente no necesita recrearse. `.venv` y cachés quedan ocultos en
la configuración local del explorador. No guardar secretos en AGENTS.local.md.
Procedencia y actualización: [UPSTREAM](UPSTREAM.md). El [README principal](../README.md)
conserva la preparación de producto.
