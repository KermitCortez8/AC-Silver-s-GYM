# Integración continua con Testiny

La integración recoge las pruebas existentes de GitHub Actions y publica sus
informes JUnit en **Automation** del proyecto `SILVE`. La activación requiere una
API key y dos variables de GitHub; los archivos por sí solos no habilitan envíos.

## Organización de resultados

| Fuente en Testiny | Pruebas recogidas | Cuándo se generan |
| --- | --- | --- |
| `GYM - Backend` | pytest: unitarias, integración, arquitectura y omisiones de PostgreSQL sin contenedor | PR a `develop`/`main` y merge a `main` |
| `GYM - Frontend` | Node: unitarias, integración e interfaz | PR a `develop`/`main` y merge a `main` |
| `GYM - PostgreSQL` | Ocho suites de contratos, transacciones y concurrencia con base desechable | PR a `develop`/`main` |
| `GYM - Notificaciones Deno` | Pruebas de recordatorios de la Edge Function | PR a `develop`/`main` y merge a `main` |

Dentro de cada fuente, las carpetas siguen `módulo → tipo → archivo`. Los nombres
de los once módulos se leen del [índice existente](../base/modulos/README.md).
Las pruebas compartidas quedan en `Transversales`. El tipo se obtiene de las
carpetas reales de pruebas; las suites específicas usan `Integración PostgreSQL`
e `Integración Deno`.

Ejemplo: `GYM - Backend → MOD-02 - Clientes → Unitarias → test_client_lookup`.
Las claves técnicas se conservan entre ejecuciones mientras no cambien el archivo,
la clase o el nombre de la prueba. Mover o renombrar una prueba puede crear otra identidad.

Los RF y CUS mantienen la trazabilidad documentada en los casos manuales. Esta
integración añade evidencia técnica por módulo y tipo; no asigna automáticamente
un resultado técnico a un RF, CUS o caso manual. Testiny mantiene separados los
casos automatizados y manuales, y actualmente no ofrece su vinculación automática.
Véase la [guía oficial de Automation](https://www.testiny.io/docs/automation/importing-results/#test-cases).

## Configuración inicial

1. **Incorporar los cambios al repositorio.** Llevarlos por el flujo habitual
   de PR hasta la rama predeterminada de GitHub, normalmente `main`. El publicador
   usa `workflow_run`, que requiere que su archivo exista en esa rama. El primer
   PR de instalación podría generar artefactos sin publicarlos todavía; verificar
   la siguiente ejecución después de incorporar la integración.

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

5. **Comprobar una ejecución normal.** Abrir o actualizar un PR del propio
   repositorio hacia `develop` o `main`. En `Actions`, esperar a que termine
   `Validar PR` y después abrir `Publicar resultados en Testiny`. Sus logs deben
   mostrar los recuentos y los identificadores de las ejecuciones importadas.
   En Testiny, seleccionar `SILVE → Automation` y comprobar las fuentes anteriores.
   El importador crea cada fuente cuando recibe su primer informe; no hace falta
   crear esas carpetas ni cargar un CSV a mano. Consultar el
   [flujo oficial para GitHub Actions](https://www.testiny.io/docs/integrations/ci-cd/github-actions/).

Si GitHub Actions está deshabilitado en el repositorio, habilitarlo en
`Settings → Actions → General` y permitir las acciones utilizadas por los workflows.
Los permisos de token necesarios ya están declarados en YAML: lectura del código
y de los artefactos para publicar. No hace falta dar permiso de escritura general.

## Comportamiento del pipeline

Las suites generan `gym-junit-<suite>-<intento>` con XML y metadatos del checkout.
Al terminar el workflow de origen, el publicador descarga solamente los
artefactos de ese intento, valida los informes, ordena las carpetas y los importa.
También guarda `gym-testiny-normalized` con el resumen y los XML normalizados.
Los artefactos de GitHub se conservan durante catorce días.

Los resultados incluyen el repositorio, rama, URL de GitHub Actions, número de
ejecución, intento y revisión exacta probada. `vc_commit` identifica el checkout
que generó el informe; en un PR puede ser el merge provisional.
`vc_source_commit` conserva el SHA de origen del evento. La ejecución del
publicador tiene otro ID y no sustituye esos datos.

Se publican informes disponibles aunque una prueba haya fallado. Los fallos,
errores y omisiones conservan su estado; el job original continúa fallando.
Una omisión de PostgreSQL en la suite general no acredita la prueba SQL; el
resultado real está en su fuente específica cuando se ejecuta con contenedor.
Si un job no alcanza a generar XML, no se inventan resultados para ese job.
Sin ningún informe válido, el publicador falla y no crea una ejecución vacía.

El publicador acepta los workflows `Validar PR` y `CI/CD Pipeline GYM` del propio
repositorio, terminados con éxito, fallo o timeout. Excluye ejecuciones canceladas
y PR de forks. El código del importador se obtiene de la rama predeterminada,
y la clave solo se entrega al paso de publicación. Los adjuntos están desactivados.

La publicación es independiente del despliegue existente en Vercel/Render.
No vuelve a ejecutar las suites: importa los informes que estas generan. La
primera prueba remota del envío queda pendiente hasta configurar la clave y
activar el workflow. Tampoco se usa la cuenta de prueba de la web desplegada.

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
python .github/scripts/testiny/publish.py --incoming /ruta/incoming --output /ruta/normalized
python -B -m unittest discover -s .specify/tests -p test_testiny_ci.py -v
```

En Windows se puede sustituir `python` por `py -3.12`. El primer comando solo
prepara XML y `resumen.json`: no contacta a Testiny, incluso si existe una clave
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
| Una fuente no aparece | Revisar si su job produjo XML en el intento actual. PostgreSQL solo se ejecuta en la validación del PR. |
| Informe vacío, duplicado o inválido | Revisar el artefacto original y el error del normalizador. No convertirlo en resultados aprobados. |
| Falla una suite | Corregir el fallo en el proyecto; publicar sus resultados no corrige ni oculta el error de CI. |
| Se quiere detener el envío | Establecer `TESTINY_ENABLED=false`; las pruebas y los artefactos continúan funcionando. |

No hay reintentos automáticos de importación. Si una publicación se interrumpe
después de enviar alguna fuente, volver a lanzar el publicador puede crear
ejecuciones adicionales de fuentes ya completadas. Revisar primero los logs y
Testiny. Al repetir solo jobs fallidos del workflow de pruebas, se publican los
informes de ese nuevo intento; para obtener todas las suites en un mismo intento,
usar `Re-run all jobs` en el workflow de origen.

## Archivos y evidencia

- [Publicador de GitHub Actions](../../.github/workflows/testiny.yml).
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

Sobre la ejecución separada y su rama de confianza, consultar
[workflow_run en GitHub](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run).
