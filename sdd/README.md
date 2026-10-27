# Desarrollo guiado por especificaciones

Todo el material de SDD del proyecto se mantiene en esta carpeta.
GitHub Spec Kit **1.2.3** está fijado al commit oficial de
[requirements.txt](requirements.txt).

## Organización

```text
sdd/
├── README.md                  Guía para el equipo
├── requirements.txt           Versión fijada de Spec Kit
├── scripts/                   Instalación y acceso a la CLI
├── specs/                     Especificaciones, planes, tareas y evidencia
├── .specify/
│   ├── memory/constitution.md  Principios y mapa de módulos
│   ├── templates/             Plantillas oficiales
│   ├── scripts/               Scripts oficiales
│   └── ...                    Metadatos, integración y workflow
├── .agents/skills/             Skills oficiales
└── .tools/spec-kit/            Instalación local, ignorada por Git
```

`backend/`, `frontend/`, `supabase/` y la documentación técnica en `docs/`
permanecen en la raíz del repositorio. Las rutas de la aplicación que aparecen
en las especificaciones se refieren a esa raíz.

El enlace `.agents/skills` de la raíz apunta a `sdd/.agents/skills`: permite
descubrir las skills sin duplicar sus archivos. Las instrucciones de
[AGENTS.md](../AGENTS.md) indican al agente que trabaje con Spec Kit dentro de
`sdd/`. No se requieren carpetas `specs/`, `.specify/`, `scripts/` o `tools/`
de SDD fuera de esta carpeta.

## Los cuatro puntos del proceso

| Punto | Documento |
| --- | --- |
| Principios y módulos | [Constitución](.specify/memory/constitution.md). |
| Comportamiento esperado | [Especificación piloto](specs/001-control-errores/spec.md). |
| Diseño y tareas | [Plan](specs/001-control-errores/plan.md) y [tareas](specs/001-control-errores/tasks.md). |
| Verificación | [Guía del piloto](specs/001-control-errores/quickstart.md) y [evidencia](specs/001-control-errores/verification.md). |

La herramienta está instalada. La aceptación funcional del piloto conserva
tareas abiertas; la presencia de documentos no demuestra que estén resueltas.

## Instalar y comprobar

Desde la raíz del repositorio, con Python 3.11+, venv/pip y Git disponibles:

```bash
bash sdd/scripts/setup-spec-kit.sh
bash sdd/scripts/specify version
```

El instalador usa `sdd/.tools/spec-kit/`. No cambia el PATH ni las dependencias
de la aplicación. Los archivos oficiales ya se versionan: no hace falta repetir
`init`. El lanzador `sdd/scripts/specify` selecciona automáticamente `sdd/`
como proyecto de Spec Kit, desde cualquier directorio.

## Trabajar con el piloto

Desde la raíz del repositorio:

```bash
export SPECIFY_INIT_DIR="$PWD/sdd"
export SPECIFY_FEATURE_DIRECTORY=specs/001-control-errores
bash sdd/.specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
```

`SPECIFY_INIT_DIR` selecciona el proyecto que contiene `.specify/`.
`SPECIFY_FEATURE_DIRECTORY` es relativo a ese proyecto, por eso se usa
`specs/001-control-errores`, sin otro prefijo `sdd/`.
También se puede ejecutar el script desde `sdd/` sin definir `SPECIFY_INIT_DIR`.

El archivo `sdd/.specify/feature.json` guarda la selección local y se ignora en
Git. CI selecciona el piloto mediante variables explícitas y trabaja desde `sdd/`.
La comprobación estructural no ejecuta las pruebas funcionales ni valida el
significado de los requisitos.

En el **chat del agente**, no en Bash:

```text
$speckit-analyze Revisa sdd/specs/001-control-errores.
$speckit-implement Continúa con las tareas abiertas del piloto.
$speckit-converge
```

Ejecutar una skill por paso, leyendo el resultado. El agente debe usar `sdd/`
como directorio de trabajo para los scripts y referencias de las skills
oficiales. Desde otro directorio puede definir `SPECIFY_INIT_DIR` con la ruta
absoluta a `sdd/`. La ruta `/specs/` de sus plantillas se interpreta dentro
del proyecto SDD, no como una carpeta que deba crearse en la raíz de la aplicación.

## Siguiente cambio

1. `$speckit-specify`: problema, actores, alcance, escenarios y requisitos.
2. `$speckit-clarify`: resolver ambigüedades relevantes cuando existan.
3. `$speckit-plan`: diseño compatible con las capas y contratos existentes.
4. `$speckit-tasks` y `$speckit-analyze`: dividir trabajo y revisar consistencia.
5. `$speckit-implement` y `$speckit-converge`: implementar, comprobar y registrar brechas.

Las nuevas funcionalidades se crean en `sdd/specs/NNN-cambio/`. La constitución
aporta el contexto compartido; cada especificación describe un cambio acotado.
La extensión Git no está instalada: las ramas y los commits siguen el flujo
habitual del equipo.

Los documentos habituales son `spec.md`, `plan.md`, `tasks.md` y la evidencia.
Investigación, contratos, modelo de datos y guía de validación se incluyen cuando
aporten información aplicable. No se inventan entidades o dependencias para
rellenar plantillas.

## Evidencia y mantenimiento

Reutilizar pytest, node:test, compilación y CI existentes. Para un comportamiento
nuevo, demostrar el escenario fallido antes de corregirlo; para uno existente,
reutilizar su prueba sin duplicarla. Registrar comandos, revisión, resultados y
omisiones. Las tareas solo se cierran cuando existe evidencia suficiente.

Las pruebas de la aplicación se ejecutan desde la raíz del repositorio o sus
carpetas de trabajo habituales; consultar [AGENTS.md](../AGENTS.md) y la
[guía del piloto](specs/001-control-errores/quickstart.md).

Para actualizar Spec Kit, probar otra release en una carpeta temporal y revisar
el diff antes de sustituir archivos oficiales. Preservar la constitución y
especificaciones. Mantener el enlace de descubrimiento de skills en la raíz.

Referencias: [proyectos anidados en Spec Kit](https://github.com/github/spec-kit/blob/v1.2.3/docs/guides/monorepo.md)
y [descubrimiento de skills](https://learn.chatgpt.com/docs/build-skills).
