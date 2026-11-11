# Plan de pruebas · MOD-07 · Rutinas y progreso

**ID:** PP-MOD-07 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
15 CT (7 backend y 8 frontend) y 5 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Ejercicios, asignación compatible, actor, progreso y descanso.

Actores: Admin/staff/trainer; el progreso utiliza el actor autenticado.

Datos de partida: Matrícula activa/inactiva, horario activo/inactivo, rutina de mismo/distinto servicio, pesos cero/negativos, ejercicios sin identidad; error de guardado y refresco posterior.

Dependencias y orden: MOD-01/05; transversales de actor, validación anidada y transacciones.

Aplicar los [datos y entornos comunes](../plan-de-pruebas.md#entorno-y-datos-de-prueba)
y los criterios de entrada antes de ejecutar. Usar estado limpio para cada
variante y conservar las mismas identidades dentro de un recorrido compuesto.

## Funcionalidades y casos programados por tipo

P1 cubre identidad/permisos, dinero, consistencia y reglas indispensables;
P2 cubre presentación, navegación y ergonomía. Ambos forman parte del alcance.
Las precondiciones y pasos completos están en [casos-de-uso.md](casos-de-uso.md).

### Pruebas unitarias y de reglas

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Validación de ejercicios, pesos y estructuras | [CP-M07-01](casos-de-uso.md) · CA-04 | P1 | Cero se conserva; negativos y estructuras inválidas fallan antes de mutar catálogo/historial. |

### Pruebas de integración

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Catálogo e historial detallado de ejercicios | [CP-M07-02](casos-de-uso.md) · CA-01 | P1 | Ejercicios y sus detalles sobreviven serialización/recarga; esquema ausente no se oculta descartando datos. |
| Asignación compatible con matrícula, horario y servicio | [CP-M07-03](casos-de-uso.md) · CA-02 | P1 | Solo se guarda la combinación compatible; los rechazos no dejan asignación parcial. |
| Autor del progreso determinado por la sesión | [CP-M07-04](casos-de-uso.md) · CA-03 | P1 | Se registra T1, resuelto desde la sesión, sin aceptar suplantación del payload. |

### Pruebas de interfaz y navegación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Monitor, borradores, desasignación y descanso | [CP-M07-05](casos-de-uso.md) · CA-05 | P2 | El error conserva borrador; solo se limpia al confirmar; un refresco posterior fallido no ofrece guardar otra vez lo ya guardado; al desmontar no quedan intervalos. |

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
  tests/horarios_matriculas/integracion/test_schedule_enrollment.py \
  tests/rutinas_progreso/integracion/test_trainer_exercises.py \
  tests/transversales/integracion/test_partial_smell_fixes.py \
  tests/transversales/integracion/test_review_regressions.py -q)
(cd frontend && node --test \
  tests/rutinas_progreso/integracion/trainer-refresh-errors.test.js \
  tests/rutinas_progreso/interfaz/flujos.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

Distinguir fallo de guardado de fallo de refresco después de guardar. El segundo no habilita repetir un progreso ya confirmado.

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
