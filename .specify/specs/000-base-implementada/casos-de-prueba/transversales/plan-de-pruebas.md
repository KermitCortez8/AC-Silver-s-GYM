# Plan de pruebas · Transversal · Controles transversales

**ID:** PP-Transversal · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
587 CT (390 backend y 197 frontend) y 4 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Errores HTTP, resultado incierto, validaciones, rollback y arquitectura.

Actores: Todos los roles según la matriz API y dos sesiones/aplicaciones independientes.

Datos de partida: Servicios que fallan con dato centinela privado, escritura con cuerpo demorado, 204 sin cuerpo, IDs inválidos, longitudes límite/límite+1 y snapshots incompatibles.

Dependencias y orden: Se ejecuta junto con cada módulo afectado y en la regresión total; no se suma varias veces el mismo CT en los recuentos de alcance.

Aplicar los [datos y entornos comunes](../plan-de-pruebas.md#entorno-y-datos-de-prueba)
y los criterios de entrada antes de ejecutar. Usar estado limpio para cada
variante y conservar las mismas identidades dentro de un recorrido compuesto.

## Funcionalidades y casos programados por tipo

P1 cubre identidad/permisos, dinero, consistencia y reglas indispensables;
P2 cubre presentación, navegación y ergonomía. Ambos forman parte del alcance.
Las precondiciones y pasos completos están en [casos-de-uso.md](casos-de-uso.md).

### Pruebas de integración

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Errores HTTP, códigos de negocio y datos privados | [CP-TR-01](casos-de-uso.md) · Transversal | P1 | Se conserva el estado HTTP previsto (400/403/404/409/422/503 según causa), mensajes legibles y ausencia de valores privados en respuesta. |
| Escritura con resultado incierto y reconciliación | [CP-TR-02](casos-de-uso.md) · Transversal | P1 | No hay reintento automático ni éxito falso; se informa resultado no confirmado para reconciliar antes de repetir. |

### Pruebas PostgreSQL y concurrencia

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Rollback transaccional y snapshot obsoleto | [CP-TR-03](casos-de-uso.md) · Transversal | P1 | Ningún recurso queda parcialmente modificado y el conflicto no habilita escritura REST alternativa. |

### Pruebas de arquitectura y documentación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Arquitectura, documentación y trazabilidad | [CP-TR-04](casos-de-uso.md) · Transversal | P2 | Los 99 archivos están catalogados, los criterios de once módulos tienen casos y el cambio se limita a documentación; controles estáticos no se presentan como aceptación funcional. |

## Selección y orden de ejecución

1. Revisar los CP anteriores y los [casos individuales](casos-de-prueba.md);
   clasificar las variantes por sus precondiciones y el entorno requerido.
2. Ejecutar reglas y contratos locales, después servicios/HTTP y los controles
   compartidos indicados por las fuentes de los CP. Separar resultados SQL.
3. Preparar y ejecutar cada variante PostgreSQL en su contenedor desechable;
   comprobar locks, rollback y recarga cuando el caso lo exige. Sin ese entorno,
   registrar omisión o bloqueo y continuar con las pruebas independientes.
4. Realizar los recorridos de interfaz que correspondan: estados correcto/error,
   teclado, móvil/escritorio, claro/oscuro y conservación de borradores.
   Un resultado Node/SSR no aprueba por sí solo el recorrido de navegador.
5. Repetir el caso fallido tras la corrección y su regresión relacionada; cerrar
   con la regresión completa del plan general en la versión que se informa.

La selección reproducible se obtiene de [catalogo-pruebas.json](catalogo-pruebas.json).
Estos comandos cubren suites propias y fuentes compartidas citadas por sus CP;
los totales reales se registran desde el runner y se deduplican por selector.

```bash
(cd backend && python -m pytest \
  tests/transversales/arquitectura/test_layer_boundaries.py \
  tests/transversales/integracion/test_basic_form_validation.py \
  tests/transversales/integracion/test_client_flow_control.py \
  tests/transversales/integracion/test_form_limits.py \
  tests/transversales/integracion/test_maintainability_fixes.py \
  tests/transversales/integracion/test_module_error_control.py \
  tests/transversales/integracion/test_partial_smell_fixes.py \
  tests/transversales/integracion/test_priority_fixes.py \
  tests/transversales/integracion/test_remaining_smells.py \
  tests/transversales/integracion/test_review_regressions.py \
  tests/transversales/integracion/test_scoped_operations.py \
  tests/transversales/postgres/test_atomic_transactions_postgres.py -q)
(cd frontend && node --test \
  tests/transversales/arquitectura/layer-boundaries.test.js \
  tests/transversales/integracion/api-response.test.js \
  tests/transversales/integracion/data-repositories.test.js \
  tests/transversales/integracion/form-validation.test.js \
  tests/transversales/integracion/http-error-control.test.js \
  tests/transversales/integracion/module-error-control.test.js \
  tests/transversales/integracion/navigation-stores.test.js \
  tests/transversales/integracion/response-identifiers.test.js \
  tests/transversales/interfaz/formularios.test.js \
  tests/transversales/interfaz/table-pagination-views.test.js \
  tests/transversales/interfaz/table-pagination.test.js \
  tests/transversales/unitarias/input-rules.test.js \
  tests/transversales/unitarias/priority-money-dates.test.js)
python .specify/.codex/hooks/validate.py
python -B -m unittest discover -s .specify/tests -v
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

Comprobaciones de arquitectura/documentación no sustituyen aceptación funcional. Las 587 pruebas de esta carpeta contienen controles compartidos; no representan otro módulo de negocio.

Por cada CP registrar variante, CT/selector o recorrido manual que lo comprueba,
versión, datos, resultado observado y evidencia. Para navegador adjuntar captura
propia y pasos; para API/SQL registrar respuesta/consulta y estado antes/después.
Si la referencia solo aporta código, completar una verificación directa en el
entorno de pruebas o registrar la cobertura pendiente; no inferir una aprobación.

El módulo se declara aprobado cuando todos sus casos programados y regresiones
aplicables cumplen el resultado esperado, sin defectos S1/S2 abiertos ni bloqueos
P1. Cada omisión/bloqueo mantiene pendiente la funcionalidad que depende de ella.
El [plan general](../plan-de-pruebas.md#criterios-de-salida-y-entregables) define
el cierre completo y el tratamiento de un informe parcial.
