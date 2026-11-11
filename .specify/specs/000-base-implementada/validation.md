# Evidencia de la adopción documental

Registro histórico de la primera entrega documental. La configuración vigente
del CLI, skills y flujo se describe en el [índice central](../../README.md).

Fecha: 2026-10-29. Alcance: documentos, plantillas, instrucciones para Codex y
control documental. Referencia funcional: `fc1577e`.

## Comprobaciones ejecutadas

| Comprobación | Resultado |
| --- | --- |
| `python .specify/scripts/validate_docs.py` | Correcto: enlaces locales, siete componentes y fila de evidencia por criterio en once módulos y la spec base. |
| Nombres `test_*` citados en los módulos, contrastados mediante AST con `backend/tests/` | Todos existen. No equivale a ejecutar esas pruebas. |
| Casos negativos del validador con contenido en memoria | Rechazó componente ausente/vacío, criterio duplicado, criterio sin evidencia y evidencia solo externa. |
| Enlaces de ejemplo y enlace roto en directorio temporal | Ignoró el ejemplo dentro de código y detectó el destino inexistente. |
| Sintaxis Python del validador y YAML del workflow | Correctas, usando `compile` y el parser YAML disponible. |
| `git diff --check` y revisión de espacios/saltos finales de archivos nuevos | Sin errores. |
| Revisión del alcance del diff | Solo se modifican README y `.gitignore` existentes y se añaden los archivos de esta adopción. Código e informes históricos intactos. |

La [tabla de criterios](spec.md) enlaza los documentos que satisfacen CA-01…CA-08.
La comprobación puede repetirse desde la raíz con el validador; el
[workflow](../../../.github/workflows/spec-docs.yml) la ejecutará en los PR configurados
una vez incorporado al repositorio remoto.

## Límites de esta verificación

No se ejecutaron las suites de aplicación, compilación frontend, integración
PostgreSQL, navegador, migraciones, cobros o correos reales: no se cambió
comportamiento del producto. La documentación indica pruebas disponibles y
dependencias de configuración; no certifica sus resultados de ejecución actuales.

No se instaló Specify CLI ni se generaron skills nativas en esta sesión. La base
se utiliza directamente con `AGENTS.md`; los pasos para añadir la integración
oficial están en [el flujo de trabajo](../../guias/spec-driven.md).

### Corrección directa: correo del preregistro

- Síntoma: la regla compartida limitaba las cuentas a Gmail/Hotmail.
- Regresión: aceptar dominios `.com` con una sola `@` y formato válido;
  rechazar otros sufijos, coma en lugar de punto y direcciones malformadas.
- Frontend: 49 pruebas dirigidas aprobadas (`34-form-validation` y
  `26-stock-edit-forms`); `npm run build` aprobado.
- Backend: 10 casos directos de `account_email` aprobados. La suite pytest
  no se ejecutó porque el entorno carece de `pytest`.
- Validador documental y `git diff --check` aprobados. No se realizó revisión
  visual en navegador; las pruebas ejercitan el formulario y su HTML renderizado.
- La primera ejecución completa del frontend se interrumpió tras encontrar
  un caso que todavía esperaba el rechazo de un subdominio `.com`; se actualizó
  el caso y se aprobaron las 49 pruebas dirigidas. No se certifica la suite completa.

## Revisión de pruebas por módulo y batería de casos de uso · 2026-11-10

Petición: revisar las pruebas existentes, ordenarlas primero por módulo y luego
por tipo, y documentar en la spec una batería de pruebas de casos de uso.
Referencia inspeccionada: `7744c6c`; cambio exclusivamente documental.

La evidencia estaba repartida entre suites, contratos de módulos, validaciones
históricas y prototipos. El [inventario ordenado](pruebas-por-modulo.md) reúne
94 archivos automatizados (46 backend, 46 frontend, uno Deno y uno documental),
tres scripts manuales, los 20 informes de `base/validaciones` y las validaciones
de specs/prototipos. Conserva su contexto, fallos, omisiones y límites; no suma
ejecuciones de versiones diferentes ni traslada físicamente los archivos de pruebas.

La [batería en la spec](spec.md#batería-de-pruebas-de-casos-de-uso) contiene
89 casos: 85 entre los once módulos y cuatro transversales. Incluye actor/datos,
precondiciones, pasos, resultado esperado, tipo y referencia disponible. Los 71
criterios vigentes de los once contratos tienen al menos un caso asociado.
Los casos quedan pendientes de ejecución como batería consolidada.

| Comprobación ejecutada en esta entrega | Resultado |
| --- | --- |
| `python .specify/.codex/hooks/validate.py` | Aprobada: 92 archivos y 14 contratos de siete componentes. |
| `python -B -m unittest discover -s .specify/tests -v` | 13 aprobadas, 0 fallos, en 8,979 s. Comprueban el flujo documental. |
| Contraste estático de los cuatro directorios de suites con los enlaces del inventario | 94/94 archivos automatizados incluidos; 20/20 informes históricos enlazados. También se incluyen los once archivos frontend con aserciones de nivel superior. |
| IDs de casos y trazabilidad contra criterios de cada contrato | 89 IDs únicos y 71/71 criterios asociados; ninguna referencia de criterio inexistente. |
| Selectores Python citados, contrastados mediante AST | Todos existen en los archivos enlazados; no equivale a ejecutar esas pruebas. |
| `git diff --check` y alcance documental | Sin errores de espacios; cambios en spec, inventario, validación e índices. |

La revisión distingue Node/SSR, navegador con API sintética, integración con
dobles y PostgreSQL/cron reales. El prototipo 002 conserva sus 18 comprobaciones
de navegación como demostración local; la integración productiva/UAT sigue pendiente.

Límite confirmado al inspeccionar archivos: la migración
[023_general_attendance_three_hour_close.sql](../../../backend/migrations/023_general_attendance_three_hour_close.sql)
tiene 0 bytes. Los registros históricos de cierre general no certifican su
reproducción con este árbol. Se conserva la incidencia y se marca pendiente la
variante SQL/cron del cierre general; esta revisión no modifica la migración.
El job SQL actual tampoco incluye todas las suites PostgreSQL del inventario.

No se reejecutaron suites funcionales backend/frontend, build, Deno, PostgreSQL,
recorridos de navegador ni scripts manuales. No se escribieron datos remotos ni
se enviaron pagos/correos. Estas omisiones corresponden al alcance documental;
los resultados históricos siguen perteneciendo a sus informes originales.

## Organización física de backend/frontend y casos por tipo · 2026-11-10

La aclaración del usuario precisó que la organización debía aplicarse a los
archivos de pruebas. Se trasladaron las suites a
`backend/tests/<módulo>/<tipo>/` y `frontend/tests/<módulo>/<tipo>/`, con nombres
de módulo en español. Los tipos presentes son `unitarias`, `integracion`,
`postgres`, `interfaz`, `arquitectura` y `manuales`, según el componente.
`transversales` conserva las comprobaciones que cubren varios módulos.

- Backend: 46 suites automatizadas y tres scripts manuales por módulo; paquetes
  explícitos, imports entre fixtures actualizados y doble/esquema SQL en `soporte`.
- Frontend: 51 suites frente a las 46 originales. Los 22 casos de asistencia/rutinas
  y los 25 casos de formularios se distribuyeron en siete suites de sus módulos,
  reutilizando dos entornos en `soporte`. Se retiraron prefijos numéricos de nombres.
- Se ajustaron imports relativos, raíces de Vite, búsquedas de migraciones/fixtures
  y las seis rutas del job SQL de CI. Los comandos generales siguen siendo
  `python -m pytest tests/ -q` y `npm test`, desde sus componentes.
- Los 89 casos de uso de la spec tienen subsecciones explícitas por módulo y tipo,
  preparación, pasos, resultados y referencias a los archivos actuales. El inventario
  contiene ahora 99 archivos automatizados, incluidos Deno y control documental.
- Los enlaces y comandos documentados apuntan a las nuevas rutas. Actualizar la
  ruta de una evidencia histórica no significa que aquella ejecución se haya repetido.

| Comprobación ejecutada | Resultado |
| --- | --- |
| Backend completo antes de mover, con `AUTH_SECRET_KEY` sintética | 751 aprobadas y 54 omitidas por no configurar PostgreSQL; 0 fallos. |
| Backend completo después de mover, con la misma configuración | 751 aprobadas y 54 omitidas; 0 fallos, en 31,26 s. |
| Colección pytest antes/después, normalizando solo el cambio de ruta | Los mismos 805 IDs parametrizados; no falta ni se duplica ningún caso. |
| Frontend completo antes/después, `npm test` | 372 aprobadas en ambas ejecuciones, 0 fallos/omisiones; después, 45,28 s. |
| Contraste AST de llamadas `test()` frontend antes/después | 293 declaraciones conservadas con sus cuerpos intactos, normalizando únicamente rutas al código. Los bucles/archivos con aserciones completan los 372 casos ejecutados. |
| `node --test tests/planes_promociones/integracion/plan-directory.test.js` desde frontend | 4 aprobadas tras ajustar su carpeta de tipo a `integracion`. |
| `npm run build` desde frontend | Aprobada. |
| `python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` desde backend | 0 errores. |
| Siete suites SQL en PostgreSQL 16 desechable con pg_cron | 43 aprobadas: transacciones, preregistros, borrado con ventas, plazo de clase, recorrido de asistencia, sesiones y avisos de renovación. |
| Casos de clase de `test_automatic_attendance_postgres.py`, seleccionados por `-k` | 7 aprobadas, 4 no seleccionadas; incluye cron real sin navegador. |
| `python -B -m unittest discover -s .specify/tests -v` | 13 aprobadas, 0 fallos, en 14,207 s. |
| Validador documental y `git diff --check` | Aprobados; 92 documentos y 14 contratos. |
| Comprobación estática de inventario/casos | 99/99 archivos enlazados, 89 IDs únicos, 71/71 criterios de módulos asociados y selectores Python existentes. |

El SQL se ejecutó exclusivamente en `gym-tests-organizacion`, con base `gym_test`,
sin red ni puertos publicados, credenciales sintéticas y
`GYM_TEST_POSTGRES_CONTAINER` apuntando solo a ese contenedor. Se eliminó al
terminar. No se utilizaron bases compartidas ni se cambiaron servicios de aplicación.

Los cuatro casos SQL generales de la suite automática no se seleccionaron:
dependen de la migración 023 vacía ya identificada. Las 50 aprobaciones SQL
corresponden a dos ejecuciones disjuntas y no se suman a las 54 omisiones como
si fueran una sola ejecución completa. Esta organización no corrige la migración.
No se ejecutaron scripts manuales, Deno ni una revisión visual nueva; no cambian
Edge Function ni interfaz. Se conservan avisos de Pinia/Browserslist/tiempos de
plugins y la deprecación de Starlette/httpx, sin fallos en los controles realizados.

## Catálogo individual exhaustivo de la suite · 2026-11-10

La revisión del usuario señaló que los 89 escenarios agrupados no daban una
enumeración individual de las pruebas. Se conserva esa síntesis y se añade la
[batería completa](casos-de-prueba/indice.md), con un registro por resultado del runner,
incluidas las variantes de parametrización. La spec enlaza ambas vistas y
distingue escenarios de negocio/recorridos de casos técnicos individuales.

| Componente | Casos detectados | Aprobados | Omitidos |
| --- | ---: | ---: | ---: |
| Backend | 805 | 751 | 54 |
| Frontend | 372 | 372 | 0 |
| Total | 1.177 | 1.123 | 54 |

Se repitió backend con una clave sintética y un plugin local de registro de
colección/resultados: `python -m pytest tests/ -q -p gym_catalogo_pytest` desde
backend, con el plugin temporal en `PYTHONPATH=/tmp`. Resultado: 751 aprobadas,
54 omitidas, 0 fallos, en 26,31 s. Las omitidas requieren PostgreSQL explícito.
El plugin solo recoge metadatos y resultados; no cambia pruebas ni fixtures.

Frontend se repitió con
`node --test --test-reporter=/tmp/gym_catalogo_node.mjs` desde frontend. El
reportero local registró 372 resultados aprobados, 0 fallidos. Conserva las once
unidades con aserciones de archivo y expande los nombres generados en bucles.
Las dependencias y los archivos de prueba no cambiaron en esta ampliación.

El [catálogo estructurado](casos-de-prueba/catalogo.json) conserva IDs, módulo/tipo,
componente, selector, comando individual, variante, preparación y extractos de
aserciones/expectativas obtenidos del código. La revisión AST reconoce `assert`,
`pytest.raises`, aserciones `unittest` y aserciones Node; cada uno de los 1.177
casos enlaza una fuente existente y tiene al menos un extracto de comprobación.
Un extracto abreviado no sustituye todas las comprobaciones de su fuente.

Conciliación: 805 selectores backend y 372 resultados frontend distintos,
1.177 IDs únicos, 97 archivos fuente y correspondencia exacta con los registros
de ambos runners. Los 89 escenarios de la spec y sus 71 criterios de módulo
se conservan; no se presentan como toda la suite ni como 1.177 casos de uso de negocio.
Validador documental aprobado: 93 documentos y 14 contratos. `git diff --check`
sin errores. No se repitieron PostgreSQL, Deno, navegador ni build al ampliar
esta documentación; sus ejecuciones previas conservan sus propios alcances.

## Separación de los casos en carpetas por módulo · 2026-11-10

Por petición del usuario se sustituyó el documento global de casos por la
carpeta [casos-de-prueba](casos-de-prueba/indice.md), con once subcarpetas de
módulo y una de controles transversales. Cada una contiene:

- `casos-de-prueba.md`: los casos individuales de ese módulo, ordenados por tipo.
- `casos-de-uso.md`: sus escenarios agrupados con preparación, pasos y resultados.
- `catalogo-pruebas.json`: los datos, selectores y comandos de ese módulo.

La spec conserva la tabla de acceso a los módulos y sus totales. El
[índice JSON](casos-de-prueba/catalogo.json) registra las rutas de los doce
catálogos y sus recuentos; los casos completos permanecen en sus archivos de
módulo. Se ajustaron todos los enlaces relativos al código y a los contratos.

Comprobaciones de esta separación:

- Los 1.177 registros JSON coinciden campo por campo con el catálogo anterior;
  no cambiaron IDs, parámetros, comandos, resultados ni extractos de comprobación.
- Se conservan exactamente las 1.177 filas `CT-*` y los 89 escenarios `CP-*`,
  sin pérdidas ni duplicados. Las referencias siguen apuntando a las mismas fuentes.
- Los totales se mantienen: 805 backend y 372 frontend; 1.123 aprobaciones y
  54 omisiones registradas. La división no representa una ejecución nueva.
- Validador documental aprobado: 117 documentos y 14 contratos de siete componentes.
- `git diff --check` aprobado. No se reejecutaron suites funcionales para este
  traslado exclusivamente documental.

## Plan de pruebas de las funcionalidades documentadas

Se redactó el [plan general PP-GYM-001](casos-de-prueba/plan-de-pruebas.md)
y un `plan-de-pruebas.md` en cada una de las once carpetas de módulos y en
la de controles transversales. La spec, el índice y los documentos de casos
enlazan los planes correspondientes.

El plan define objetivo/alcance, funcionalidades por CP/CA, prioridades,
datos/actores, entornos y dependencias, tipos de prueba, hitos de ejecución,
cinco recorridos entre módulos, comandos de regresión, responsables por rol,
evidencias, severidades, métricas y criterios de entrada/salida. Conserva
las brechas conocidas de 023, cron y verificación directa de tienda como
impedimentos para declarar una aceptación completa cuando les corresponda.

Comprobaciones de esta entrega:

- 89/89 escenarios CP aparecen una vez en las matrices funcionales de los
  doce planes de módulo/bloque; sus 1.177 CT permanecen accesibles mediante
  los documentos y catálogos originales, sin alterar datos ni resultados.
- Las rutas de las suites propuestas en los comandos de cada plan existen;
  se incluyen fuentes compartidas y se explica cómo evitar duplicar recuentos.
- Los planes separan resultados históricos de la próxima ejecución y no
  confunden Node/SSR, dobles, SQL y revisión visual propia.
- Validador documental aprobado: 130 archivos y 14 contratos de siete componentes.
- `git diff --check` aprobado. No se ejecutaron suites funcionales, SQL,
  navegador o proveedores durante la formulación de este plan documental.
