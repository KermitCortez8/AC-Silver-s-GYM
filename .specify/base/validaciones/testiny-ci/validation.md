# Validación de la integración continua con Testiny

Fecha: 2026-11-15. Cambio directo solicitado por el usuario, sin activar Spec Kit.
Entorno local: Windows, Python 3.12.10 y Node 22.14.0. Deno 2.9.8 y actionlint
1.7.12 descargados en la carpeta temporal y comprobados contra sus SHA-256 oficiales.

## Cambio y criterio de comprobación

Los workflows existentes deben generar JUnit sin ocultar sus fallos. Un workflow
separado, activado mediante variable, debe ordenar e importar esos informes a
Testiny Automation con la revisión y ejecución originales. Los casos manuales
RF/CUS no reciben resultados técnicos automáticamente.

Se añadieron acciones compartidas para pruebas Docker y artefactos; un reporter
de Node conserva el archivo de cada prueba; el normalizador reutiliza el índice
de módulos, preserva estados y elimina adjuntos y propiedades ajenas. El importador
usa una dependencia fijada y solo publica con `--publish`. Los artefactos incluyen
el intento para evitar reutilizar informes de un intento anterior.

## Comprobaciones realizadas

| Comprobación | Resultado observado |
| --- | --- |
| `python -B -m unittest discover -s .specify/tests -p test_testiny_ci.py -v` | 14 pruebas: 13 aprobadas y 1 omitida por falta de permiso de enlaces simbólicos de Windows. |
| actionlint 1.7.12 sobre los cuatro workflows | Código 0, sin incidencias. No se ejecutaron analizadores externos shellcheck/pyflakes. |
| Lectura YAML de cuatro workflows y dos acciones compuestas | Sintaxis válida. |
| Ejecución aislada del código de metadatos de la acción | XML, JSON y salida de GitHub coherentes, también en una ruta con espacios; SHA del checkout confirmado. |
| `git diff --check` | Código 0. |
| Ayuda local de `@testiny/cli` 1.43.1, comando `automation --help` | Opciones utilizadas confirmadas; ninguna importación. Node local es inferior al mínimo 22.17 exigido por la CLI; GitHub instala Node 22 actualizado. |
| Backend: `python -B -m pytest tests/ -q -p no:cacheprovider --junitxml=...` | 761 aprobadas y 57 omitidas; código 0. Un aviso de deprecación de Starlette/httpx. |
| Backend: `python -B -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` | Cero errores seleccionados; código 0. |
| Frontend: `node --test` con los reporters spec y `node-junit.mjs` | 373 pruebas: 372 aprobadas y 1 fallida; código 1. |
| Deno: `deno check supabase/functions/schedule-emails/index.ts` | Código 0. |
| Deno: `deno test --junit-path=... supabase/tests/` | 7 aprobadas; código 0 y XML generado. |
| Normalización de los JUnit reales | Backend: 818 casos, 57 omitidos y cero fallos/errores. Frontend: 373 casos y 1 fallo. Deno: 7 casos aprobados. |

Backend y frontend se comprobaron en copias temporales del código, con sus
dependencias instaladas allí y sin copiar archivos `.env`. El backend utilizó
una clave sintética y no habilitó `GYM_TEST_POSTGRES_CONTAINER`.
Fue necesario instalar `tzdata` únicamente en el entorno virtual temporal de
Windows para resolver `America/Lima`; no se cambió el runtime Linux del proyecto.
La instalación npm del frontend del workspace estaba desactualizada y produjo
68 fallos por falta de `lucide-vue-next`; la copia con `npm ci` dejó un único fallo.

Las pruebas del nuevo integrador cubren clasificación por módulos y tipos,
fallos/errores/omisiones, claves estables, suites anidadas reales de Node, rechazo
de informes vacíos/duplicados o con DTD, eliminación de adjuntos, exclusión de
forks, revisión probada, validación de metadatos, preparación sin red, clave
fuera de argumentos y propagación de errores sin reintentos. La publicación de
esas pruebas se simula; no utiliza credenciales ni contacta a Testiny.

## Fallos y limitaciones observados

- **Frontend:** falla `one rest timer supports pause, resume, completion and
  disposal without leaked intervals`, en
  `frontend/tests/rutinas_progreso/interfaz/flujos.test.js:187`, con `0 !== 3`.
  Se reprodujo ejecutando únicamente ese caso con el reporter nativo de Node,
  sin `node-junit.mjs`. No se modificó el código del temporizador ni su prueba.
- **Hook global:** `python .specify/.codex/hooks/validate.py` encuentra once
  skills no descubribles. Git registra `.agents/skills/*` como enlaces, pero el
  checkout de Windows los presenta como archivos ordinarios. No se alteraron.
- **Suite global de herramientas:** se ejecutó
  `python -B -m unittest discover -s .specify/tests -v`. Las trece pruebas
  existentes de `test_integration.py` fallan al crear enlaces simbólicos en su
  preparación con `WinError 1314`. Este límite impide completar esa suite en el
  Windows actual. Resultado final: 27 pruebas, 13 aprobadas, 13 errores y
  1 omitida. Las pruebas específicas de Testiny se verificaron aparte.
- **Docker/PostgreSQL:** el daemon Docker no estaba disponible. No se ejecutaron
  construcciones ni suites SQL en contenedor. Las 57 omisiones del backend
  permanecen como omitidas; no se cuentan como aprobaciones. En PR, el job SQL
  existente incorpora las ocho suites PostgreSQL disponibles, incluidas las
  dos de eliminación de clientes y renovación de membresías.
- **Publicación real:** no se configuraron secretos, variables ni ajustes remotos;
  no hubo importaciones, despliegues ni cambios en casos o runs manuales de Testiny.
  La primera ejecución completa en GitHub y el envío remoto quedan pendientes
  de incorporar los archivos, configurar la clave y habilitar `TESTINY_ENABLED`.

La [guía de configuración](../../../guias/testiny-ci.md) recoge la activación,
las fuentes, las omisiones, los reintentos y la revisión local sin publicación.
