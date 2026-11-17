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
- **Publicación real, verificación inicial:** en esa etapa no se configuraron
  secretos, variables ni ajustes remotos; tampoco se hicieron importaciones,
  despliegues ni cambios en casos o runs manuales de Testiny. El usuario configuró
  después los secretos y variables y ejecutó el pipeline; su diagnóstico está abajo.

## Corrección del primer envío real a Testiny

La [ejecución 43782181497](https://github.com/KermitCortez8/AC-Silver-s-GYM/actions/runs/43782181497)
del 2026-11-16 00:44 UTC descargó los cuatro informes y los normalizó correctamente.
La CLI 1.43.1 autenticó la clave y resolvió el proyecto `SILVE`, pero el primer
envío terminó con:

```text
Invalid string: 'isValidAutomationSourceName' validation failed
at AutomationResults.source (API_INVALID_INPUT_DATA)
```

Causa: la fuente `GYM - Backend` contenía espacios. El validador incluido en la
CLI fijada admite el patrón `^[$a-z][$a-z0-9_.-]*$`, sin distinción de mayúsculas,
y excluye nombres reservados de objetos JavaScript. Los identificadores técnicos
elegidos para la corrección son `gym-backend`, `gym-frontend`, `gym-postgres` y
`gym-notificaciones-deno`. Las carpetas de módulos y tipos mantienen sus nombres.

El integrador valida su convención `gym-` y palabras en minúsculas con guiones
antes de iniciar cualquier envío. La regresión comprueba las cuatro fuentes
contra el patrón de la API y simula una fuente inválida en el segundo componente:
ningún importador debe ejecutarse, incluido el del primer componente válido.
No se modifican las credenciales ni las variables de GitHub.

Los informes de origen de esa ejecución muestran backend: 818 casos, 57 omitidos;
frontend: 373 casos; PostgreSQL: 57 casos, 3 omitidos; Deno: 7 casos. Los cuatro
carecen de fallos/errores y sus jobs de GitHub terminaron correctamente.
Esto documenta la ejecución Linux posterior a la validación local de arriba;
no convierte omisiones en aprobaciones.

El aviso de Node.js 20 corresponde al runtime interno de las acciones y no causó
este error de validación: los pasos de instalación, descarga y normalización
terminaron correctamente. El importador se ejecutó con Node 22.23.4.

Comprobación de la corrección: la suite específica contiene ahora 16 pruebas,
con 15 aprobadas y una omitida por permisos de enlaces de Windows.
El hook global mantiene las once skills no descubribles del checkout Windows.
La suite global terminó con 29 pruebas: 15 aprobadas, 13 errores de preparación
por `WinError 1314` y una omitida. Los enlaces locales modificados son válidos
y `git diff --check` terminó con código 0.
La importación corregida queda pendiente de incorporar el cambio en `main`
y volver a ejecutar únicamente el publicador. El diagnóstico y las pruebas de
regresión no realizan una importación remota.

La [guía de configuración](../../../guias/testiny-ci.md) recoge la activación,
las fuentes, las omisiones, los reintentos y la revisión local sin publicación.

## Ejecución de al menos el 50 % del catálogo documentado

Petición: ejecutar al menos la mitad de los casos de Testiny, revisando primero
que sus pruebas estén implementadas correctamente. No se dedujo cobertura por
coincidir en módulo/RF ni se usaron las pruebas del integrador como evidencia
funcional del producto.

Consulta de solo lectura con Chromium/Playwright aislado, el 2026-11-15:
**199 casos** actuales del proyecto `SILVE`, frente a los 191 del snapshot anterior.
Mínimo calculado: `ceil(199 / 2) = 100`. Se conservaron módulos, IDs, tipos,
RF/CUS y todos los casos en el denominador.

La [revisión versionada](../../testiny/README.md) selecciona **100 casos**,
**316 pasos/resultados esperados** y **192 grupos de pruebas**. El CSV completo
explica correspondencias y pendientes; los archivos de aserciones/soporte tienen
huellas SHA-256 normalizadas a LF. Los artefactos de CI incluyen las huellas del
checkout probado, para no aceptar la revisión de otro contenido con el mismo
nombre de test.

### Fallo encontrado y corregido antes de integrar

La nueva regresión de TC-43 reprodujo un HTTP 200 al crear una membresía con un
plan guardado como `activo=False`. Faltaba la validación de disponibilidad en
`MembershipsRules.crear_membresia`. Se añadió antes de la escritura; ahora los
planes inexistentes/inactivos rechazan sin modificar el estado y volver a elegir
un plan activo permite crear una sola compra. La suite completa posterior pasó.
El [contrato de membresías](../../modulos/03-membresias-pagos.md) registra el borde.

TC-101 y TC-104 muestran diferencias de mensaje/método; TC-51–53 tienen una traza
heredada por revisar y TC-194 indica una redirección distinta. TC-102, 119 y 174
tienen evidencia parcial. Ninguno se cuenta entre los 100 aprobados. No se
cambiaron resultados esperados ni se modificaron casos/runs manuales para
convertir esos pendientes en aprobaciones.

### Verificación ejecutada

Se copiaron fuentes sin `.env` a carpetas temporales independientes. Backend con
Python 3.12 y dependencias de desarrollo; frontend con `npm ci` aislado y Node
**22.23.4**, versión de la ejecución GitHub consultada. No se tocaron los
`node_modules` del usuario ni su sesión de Edge.

| Comprobación | Resultado final |
| --- | --- |
| `python -B -m pytest tests/ -q --junitxml=.../backend.xml` | **866 aprobadas, 57 omitidas, 0 fallos**, 39,24 s. |
| Node `--test` con `node-junit.mjs` y destino `frontend.xml` | **386 aprobadas, 0 fallos/omisiones**. |
| `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` | Código 0; ninguna incidencia seleccionada. |
| `vite build` con la instalación aislada | Código 0. |
| `python -B -m unittest discover -s .specify/tests -p 'test_testiny*.py' -q` | **32 pruebas: 31 aprobadas y 1 omitida** por privilegio de enlaces Windows. |
| `publish.py --incoming ... --output ... --documented` sin `--publish` | **100/199 (50,25 %), 100 aprobados, 0 fallos/omisiones** entre los revisados. |
| Preparación con metadatos de origen simulados y acción `upload-junit` real | Mismo resultado 100/199; huellas verificadas, sin API ni publicación. Metadatos backend 13.956 bytes/frontend 7.772, dentro del límite. |
| `actionlint .github/workflows/testiny.yml` | Código 0. |
| `git diff --check` | Código 0. |

La prueba de temporizador fallida anteriormente con Node 22.14 pasó con
22.23.4 sin modificar el temporizador ni sus aserciones. No se actualizaron
dependencias de la aplicación para conseguir ese resultado.

Las propiedades de medición de TC-178/179 están presentes en el JUnit original:
traza inicio/fin/error de lecturas, máximo de conexiones, filas transferidas,
consultas y segundos. pytest avisa que `record_property` no pertenece al esquema
xunit2 estricto; la extracción confirmó las propiedades en ambos casos. La
normalización mantiene los resultados y conserva el XML original en su artefacto
de suite. También aparece el aviso de deprecación de TestClient/httpx; no hay
fallos asociados. Las mediciones usan proveedor doble y no certifican SLA remoto.

Los informes completos de esta sesión están en
`%TEMP%/gym-testiny-coverage-20261115/`: `backend.xml`, `frontend.xml`, logs de
suites y carpeta `resultado/` con XML de casos, JSON y CSV. El
[resumen conservado en el repositorio](../../testiny/resultado-local.json)
contiene los recuentos finales sin inventar un ID de GitHub o Testiny.

### Control incorporado y límites pendientes

Solo después de revisar y ejecutar esos casos se activó `--documented` en los
dos pasos del publicador. La fuente nueva `gym-casos-documentados` tiene una
clave estable por TC, RF/CUS, tipo e hipervínculo al caso manual. Los otros 99
siguen pendientes y no generan automatizaciones sin revisión.

La comprobación específica cubre redondeo, unicidad, variantes, skips, fallos,
todos los pasos, cambios de catálogo/aserciones, huellas LF/CRLF, metadatos del
checkout, trazabilidad y rechazo de pruebas del integrador como cobertura.
El control exige ejecución completa, no un porcentaje ficticio de aprobaciones.

La validación global sigue encontrando **11 skills no descubribles** por el
checkout Windows. La suite global de herramientas terminó con **45 pruebas:
31 aprobadas, 13 errores de preparación `WinError 1314` y 1 omitida**. Los
enlaces no se modificaron para eludir ese límite. Docker no está disponible;
no se ejecutó PostgreSQL local y las 57 omisiones no acreditan SQL.

Esta verificación es por API/servicios/componentes y dobles explícitos, con
datos sintéticos. No acredita todos los clics manuales, E2E de navegador,
Supabase/Google/Stripe/Resend productivos ni compatibilidad entre navegadores.
No se hicieron cobros, correos reales, despliegues, push ni importaciones
remotas. Para comprobar el envío en GitHub hay que incorporar los cambios a
la rama predeterminada y ejecutar **todas** las suites de nuevo: los artefactos
anteriores no contienen las nuevas huellas de revisión. Esto sustituye, para
esta ampliación, la indicación anterior de repetir únicamente el publicador.

## Consolidación de workflows · 2026-11-17

Se sustituyen los cuatro workflows por `pr-validation.yml` y `ci-cd.yml`.
Ambos incluyen validación documental y pruebas de Spec Driven. CI/CD publica
los resultados de PR mediante `workflow_run` (solo `Validar PR`) y los de merge
en su propia ejecución; no se escucha a sí mismo ni despliega por ese evento.
La documentación se añade a los requisitos de ambos despliegues.

Regresión: la publicación acepta el evento de merge a `main` conservando ID,
intento y commit; rechaza PR sin fusionar, otras ramas y otros workflows.

| Comprobación local | Resultado |
| --- | --- |
| actionlint 1.7.7, ambos workflows | Aprobada; shellcheck no instalado, desactivado. |
| unittest `test_testiny_ci.py` | 15 aprobadas, 2 omitidas: privilegio de symlinks y Node ausente. |
| Hook global `validate.py` | Falló: las once skills nativas no son descubribles en este checkout de Windows. |
| Suite completa `.specify/tests` | Interrumpida tras errores de preparación de fixtures que requieren enlaces simbólicos; Windows no concede ese privilegio. |
| git diff --check | Aprobada. |

No se ejecutaron workflows remotos, despliegues ni publicaciones reales en Testiny.

## Corrección de publicación y fallos de PR · 2026-11-17

La publicación desde PR añadida en la consolidación anterior contradecía el
alcance solicitado. Se retira `workflow_run` de CI/CD y se exige PR cerrado,
fusionado y con destino `main` en el job Testiny. Se conservan normalización,
cobertura, publicación y artefactos; los PR solo validan y guardan JUnit.
Se añade regresión para los disparadores y la procedencia de los artefactos.

El enlace del README apuntaba a `spec-docs.yml` retirado. Se actualiza al workflow
integrado, corrigiendo la causa del fallo documental mostrado por GitHub.

El fallo SQL de salida tardía era una carrera del fixture: adelantaba el límite
con microsegundos, mientras `guardar_asistencia` trunca la hora al segundo.
La prueba espera ahora al primer segundo completo posterior al límite antes de
cerrar la visita. No cambia SQL ni las reglas de negocio de asistencia.

| Comprobación | Resultado |
| --- | --- |
| actionlint 1.7.7, ambos workflows, sin shellcheck local | Aprobada. |
| unittest `test_testiny_ci.py` | 16 aprobadas, 2 omitidas (symlinks y Node). |
| Hook documental | Ya no informa del enlace roto; persisten las once skills no descubribles del checkout Windows. |
| PostgreSQL real | No ejecutado: Docker no está disponible en esta sesión; requiere nueva ejecución en CI. |
| Suite completa Spec Driven | No repetida por los impedimentos de symlinks ya registrados. |
| git diff --check | Aprobada. |

Cambios locales en `feat/correcciones`, sin push ni sincronización de `develop`.

## Validador compatible con checkout Windows · 2026-11-17

Causa: `core.symlinks=false` materializa los once enlaces Git (modo 120000)
como archivos de texto; Windows no concede privilegio para recrearlos como
symlinks. No se cambian los archivos de `.agents/skills` ni la configuración Git.

El hook acepta en Windows solamente el destino relativo exacto esperado y exige
el `SKILL.md` real. Sigue rechazando destinos alterados, archivos inválidos,
directorios copiados y skills ausentes. En Linux exige symlinks reales. Esta
compatibilidad valida el checkout, no habilita el descubrimiento nativo de skills
cuando Windows conserva los enlaces como texto; esa limitación queda documentada.

| Comprobación | Resultado |
| --- | --- |
| Hook global `validate.py` | Aprobado: 135 documentos y 14 contratos. |
| unittest `test_skill_aliases.py` | 5 aprobadas; incluye Windows, Linux, destinos inválidos y rama symlink. |
| git diff --check | Aprobada. |
| Suite completa Spec Driven | No repetida: sus fixtures crean symlinks y requieren permisos que esta sesión de Windows no tiene. |

## Revisión desactualizada de fuentes Testiny · 2026-11-17

Síntoma: el publicador falla en la preparación local con «La prueba
BE:inventario/integracion/test_inventario_tienda_stock.py::test_alta_de_item_tienda_registra_entrada_y_crea_producto_vacio
cambió o no tiene una revisión válida». No alcanza a ejecutar la publicación.

Causa: el registro SHA-256 cubre archivos completos. Los cambios de inventario
por unidades y carga de INVENTARIO_UNIDADES modificaron seis archivos incluidos
en la revisión (42 selectores), aunque la primera función nombrada no cambió.
Se compararon con las versiones registradas en 4b63165 y 573b907, se revisaron
los pasos asociados y se actualizaron únicamente las seis huellas. La revisión
razonada queda en `base/testiny/revision.md`. No se altera el catálogo, el mínimo
del 50 %, los 100 casos seleccionados ni los controles del publicador.

Regresión: `test_revision_del_repositorio_coincide_con_las_pruebas_actuales`
ejecuta load_review contra las fuentes reales. Reprodujo el mismo error antes
del ajuste y pasa después. Se ejecutará en el job documental de los PR.

| Comprobación | Resultado |
| --- | --- |
| Backend: inventario/tienda, oráculos de inventario, inventario por unidades, supabase_refresh, oráculo de lecturas y reglas transversales | 128 aprobadas; aviso existente de Starlette/httpx. |
| Frontend: navigation-stores.test.js | 30 aprobadas; avisos existentes de Pinia y error sintético de proveedor esperado por su prueba. |
| unittest test_testiny_documented.py | 17 aprobadas. |
| unittest test_testiny_ci.py | 17 aprobadas, 1 omitida por privilegios de symlinks. Reporter Node real incluido. |
| Hook documental | Aprobado: 135 documentos y 14 contratos. |
| git diff --check | Aprobada. |

Se prepararon Python/Node temporales fuera del repositorio y dependencias locales
ignoradas para verificar. Python de Windows necesitó tzdata local. No se publicaron
resultados ni se usaron credenciales de Testiny. No se reejecutaron las suites
completas del producto ni se acreditaron nuevamente los 100 casos: CI debe generar
informes nuevos del commit corregido. Cambios locales sin commit ni push.
