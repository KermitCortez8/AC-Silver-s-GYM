# Integración continua con Testiny

La integración publica únicamente después de fusionar un PR en `main`.
Los PR y los merges a `develop` validan y conservan artefactos sin publicar.
La publicación exige ejecutar al menos
el **50 % de los casos documentados revisados** antes de publicar sus informes
JUnit en **Automation** del proyecto `SILVE`. La activación requiere una
API key y dos variables de GitHub; los archivos por sí solos no habilitan envíos.

## Organización de resultados

| Fuente en Testiny | Pruebas recogidas | Cuándo se generan |
| --- | --- | --- |
| `gym-backend` | pytest: unitarias, integración, arquitectura y omisiones de PostgreSQL sin contenedor | PR a `develop`/`main` y merge a `main` |
| `gym-frontend` | Node: unitarias, integración e interfaz | PR a `develop`/`main` y merge a `main` |
| `gym-postgres` | Ocho suites de contratos, transacciones y concurrencia con base desechable | PR a `develop`/`main` |
| `gym-notificaciones-deno` | Pruebas de recordatorios de la Edge Function | PR a `develop`/`main` y merge a `main` |
| `gym-casos-documentados` | Un resultado por caso documentado revisado, derivado de sus pruebas obligatorias | Después de las suites, si se alcanza el mínimo del 50 % |

Dentro de cada fuente, las carpetas siguen `módulo → tipo → archivo`. Los nombres
de los once módulos se leen del [índice existente](../base/modulos/README.md).
Las pruebas compartidas quedan en `Transversales`. El tipo se obtiene de las
carpetas reales de pruebas; las suites específicas usan `Integración PostgreSQL`
e `Integración Deno`.

Ejemplo: `gym-backend → MOD-02 - Clientes → Unitarias → test_client_lookup`.
Las fuentes usan identificadores técnicos `gym-...`, en minúsculas y con guiones.
Los nombres descriptivos de módulos y tipos conservan espacios y acentos en sus
carpetas. La validación local de las fuentes ocurre antes de iniciar los envíos.
Las claves técnicas se conservan entre ejecuciones mientras no cambien el archivo,
la clase o el nombre de la prueba. Mover o renombrar una prueba puede crear otra identidad.

Los RF y CUS mantienen la trazabilidad documentada en los casos manuales. La
fuente `gym-casos-documentados` añade RF, CUS, tipo, ID y enlace del caso manual
mediante una correspondencia revisada de pasos y aserciones. Las otras fuentes
conservan las pruebas técnicas individuales. Testiny mantiene separados los
casos automatizados y manuales, y actualmente no ofrece su vinculación automática.
Véase la [guía oficial de Automation](https://www.testiny.io/docs/automation/importing-results/#test-cases).

La [revisión del catálogo](../base/testiny/README.md) incluye **199 casos** y
**100 automatizados y verificados (50,25 %)** por API, servicios y componentes.
No equivale a 100 recorridos E2E en navegador ni certifica proveedores externos.
Los otros 99 siguen en el denominador. Pruebas ausentes/omitidas no acreditan un
caso; el cálculo exige todos sus resultados esperados y variantes obligatorias.
Los fallidos se publican como fallidos y cuentan como ejecutados, no aprobados.

## Configuración inicial

1. **Incorporar los cambios al repositorio.** Llevarlos por el flujo habitual
   de PR hasta `main`. El publicador está integrado en `ci-cd.yml` y se ejecuta
   solamente cuando el PR se cierra fusionado hacia `main`.

2. **Crear la clave en Testiny.** En la organización del gimnasio, abrir
   `Settings → API Keys` y crear una clave llamada `github-actions-gym`.
   Seleccionar únicamente el proyecto del gimnasio (`SILVE`), activar
   `Limit API key permissions` y elegir el rol `Automation Importer`. Copiarla
   desde el diálogo de creación y elegir una caducidad que se pueda mantener.
   Los permisos efectivos también dependen del usuario que crea la clave.
   Referencia: [API keys de Testiny](https://www.testiny.io/docs/settings/api-keys/).

3. **Guardar la clave en GitHub.** Abrir el repositorio
   `KermitCortez8/AC-Silver-s-GYM`, entrar en
   `Settings → Secrets and variables → Actions → Secrets → New repository secret`
   y crear `TESTINY_API_KEY` con el valor copiado. La clave pertenece a GitHub
   Secrets; no debe guardarse en código, documentación ni variables `VITE_*`.

4. **Crear las variables del repositorio.** En la pestaña `Variables` de la
   misma pantalla, añadir las dos filas siguientes. Activar `TESTINY_ENABLED`
   después de guardar la clave.

   | Nombre | Valor | Función |
   | --- | --- | --- |
   | `TESTINY_PROJECT` | `SILVE` | Proyecto de destino; también se admite su ID numérico. |
   | `TESTINY_ENABLED` | `true` | Habilita el publicador. `false` lo desactiva. |

5. **Comprobar una ejecución normal.** Después de un merge a `main`, abrir en
   `Actions` el workflow `CI/CD Pipeline GYM`, job `Importar JUnit por módulo y tipo`. Sus logs deben
   mostrar los recuentos y los identificadores de las ejecuciones importadas.
   En Testiny, seleccionar `SILVE → Automation` y comprobar las fuentes anteriores.
   El resumen de GitHub debe mostrar al menos `100/199` casos documentados.
   El importador crea cada fuente cuando recibe su primer informe; no hace falta
   crear esas carpetas ni cargar un CSV a mano. Consultar el
   [flujo oficial para GitHub Actions](https://www.testiny.io/docs/integrations/ci-cd/github-actions/).

Si GitHub Actions está deshabilitado en el repositorio, habilitarlo en
`Settings → Actions → General` y permitir las acciones utilizadas por los workflows.
Los permisos de token necesarios ya están declarados en YAML: lectura del código
y de los artefactos para publicar. No hace falta dar permiso de escritura general.

## Comportamiento del pipeline

Las suites generan `gym-junit-<suite>-<intento>` con XML, metadatos del checkout
y huellas de los archivos de pruebas y soporte.
Tras las pruebas del merge a `main`, el publicador descarga solamente los
artefactos de esa ejecución e intento, valida los informes y los importa.
También guarda `gym-testiny-normalized` con el resumen y los XML normalizados,
`cobertura-documentada.json` y `trazabilidad-documentada.csv` (RF–CUS–TC–pruebas).
Los artefactos de GitHub se conservan durante catorce días.

Los resultados incluyen el repositorio, rama, URL de GitHub Actions, número de
ejecución, intento y revisión exacta probada. `vc_commit` identifica el checkout
que generó el informe; en un PR puede ser el merge provisional.
`vc_source_commit` conserva el SHA de origen del evento. Se publica desde
la propia ejecución de CI/CD del merge.

Se publican informes disponibles aunque una prueba haya fallado. Los fallos,
errores y omisiones conservan su estado; el job original continúa fallando.
Una omisión de PostgreSQL en la suite general no acredita la prueba SQL; el
resultado real está en su fuente específica cuando se ejecuta con contenedor.
Si un job no alcanza a generar XML, no se inventan resultados para ese job.
Sin ningún informe válido, el publicador falla y no crea una ejecución vacía.
Con `--documented`, también falla antes de enviar si no alcanza el 50 % de casos
completamente ejecutados o cambiaron las aserciones/soporte revisados. Se
conserva el detalle de cobertura insuficiente en el artefacto. El catálogo es un
snapshot versionado: debe actualizarse y revisarse cuando cambien los casos de
Testiny. La revisión de confianza se obtiene de la rama predeterminada; un PR
con cambios en pruebas revisadas puede requerir actualizar esa revisión allí.

El job solo acepta PR cerrados y fusionados hacia `main`. No existe un disparador
`workflow_run`: validar un PR o fusionar en `develop` no publica resultados.
El importador se obtiene del commit fusionado y la clave solo se entrega al paso
de publicación. Los adjuntos están desactivados.

La publicación es independiente del despliegue existente en Vercel/Render.
No vuelve a ejecutar las suites: importa los informes que estas generan. La
verificación del envío corregido queda pendiente de incorporar estos cambios y
ejecutar todas las suites de nuevo. Los artefactos anteriores no contienen las
huellas necesarias para acreditar el catálogo revisado. Tampoco se usa la cuenta
de prueba de la web desplegada.

## Revisión local sin publicar

Descargar los artefactos JUnit de un mismo intento y extraer sus XML y metadatos
en una carpeta común fuera del repositorio, por ejemplo:

```text
incoming/
  backend.xml
  backend.metadata.json
  frontend.xml
  frontend.metadata.json
  postgres.xml
  postgres.metadata.json
  schedule-emails.xml
  schedule-emails.metadata.json
```

Solo son necesarios los archivos de las suites que se hayan ejecutado. Desde
la raíz, con Python 3.12 o posterior:

```bash
python .github/scripts/testiny/publish.py --incoming /ruta/incoming --output /ruta/normalized --documented
python -B -m unittest discover -s .specify/tests -p 'test_testiny*.py' -v
```

En Windows se puede sustituir `python` por `py -3.12`. El primer comando solo
prepara XML, cobertura, CSV y `resumen.json`: no contacta a Testiny, incluso si existe una clave
en el entorno. La publicación exige `--publish`, el evento original de GitHub,
metadatos coherentes, la clave y el importador instalado.

GitHub instala Python 3.12, Node 22 y `@testiny/cli` **1.43.1** mediante su lockfile.
Para revisar la CLI localmente se necesita Node **22.17 o posterior**:

```bash
npm ci --prefix .github/scripts/testiny --ignore-scripts --no-audit --no-fund
node .github/scripts/testiny/node_modules/@testiny/cli/testiny-importer.js automation --help
```

## Incidencias habituales

| Síntoma | Comprobación |
| --- | --- |
| El publicador aparece omitido | Revisar `TESTINY_ENABLED=true`, origen del PR, conclusión y presencia del workflow en la rama predeterminada. |
| `Falta TESTINY_API_KEY` | Crear el secret de repositorio con ese nombre exacto. |
| Error 401/403 o proyecto inaccesible | Revisar caducidad, proyecto `SILVE`, rol de la clave y acceso del usuario que la creó. |
| `isValidAutomationSourceName` / `API_INVALID_INPUT_DATA` en `AutomationResults.source` | Actualizar a las fuentes técnicas de esta guía. La versión inicial usó nombres con espacios que la API rechazó; no requiere cambiar la clave ni las variables. |
| Una fuente no aparece | Revisar si su job produjo XML en el intento actual. PostgreSQL solo se ejecuta en la validación del PR. |
| Informe vacío, duplicado o inválido | Revisar el artefacto original y el error del normalizador. No convertirlo en resultados aprobados. |
| Cobertura documentada insuficiente | Consultar JSON/CSV del artefacto; ejecutar todas las suites del mismo intento, sin contar skips ni casos parciales. |
| La ejecución no acredita las aserciones revisadas | Comparar los cambios con `automatizacion.json`; revisar pruebas y soporte. Artefactos antiguos requieren una nueva ejecución completa. |
| Falla una suite | Corregir el fallo en el proyecto; publicar sus resultados no corrige ni oculta el error de CI. |
| Se quiere detener el envío | Establecer `TESTINY_ENABLED=false`; las pruebas y los artefactos continúan funcionando. |

No hay reintentos automáticos de importación. Si una publicación se interrumpe
después de enviar alguna fuente, volver a lanzar el publicador puede crear
ejecuciones adicionales de fuentes ya completadas. Revisar primero los logs y
Testiny. Al repetir solo jobs fallidos del workflow de pruebas, se publican los
informes de ese nuevo intento; para obtener todas las suites en un mismo intento,
usar `Re-run all jobs` en el workflow de origen.

## Archivos y evidencia

- [Publicador de GitHub Actions](../../.github/workflows/ci-cd.yml).
- [Validación de PR](../../.github/workflows/pr-validation.yml) y
  [pipeline de merge y despliegue](../../.github/workflows/ci-cd.yml).
- [Acción de pruebas Docker](../../.github/actions/test-with-report/action.yml) y
  [conservación de informes](../../.github/actions/upload-junit/action.yml).
- [Normalizador e importador](../../.github/scripts/testiny/publish.py),
  [reporter de Node](../../.github/scripts/testiny/node-junit.mjs),
  [dependencia fijada](../../.github/scripts/testiny/package.json) y
  [lockfile](../../.github/scripts/testiny/package-lock.json).
- [Pruebas de la integración](../tests/test_testiny_ci.py) y
  [validación realizada](../base/validaciones/testiny-ci/validation.md).
- [Catálogo y revisión por caso](../base/testiny/README.md) y
  [pruebas del cálculo de cobertura](../tests/test_testiny_documented.py).

Sobre la ejecución separada y su rama de confianza, consultar
[workflow_run en GitHub](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run).
