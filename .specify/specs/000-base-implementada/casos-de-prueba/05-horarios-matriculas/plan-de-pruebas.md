# Plan de pruebas · MOD-05 · Horarios y matrículas

**ID:** PP-MOD-05 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
38 CT (30 backend y 8 frontend) y 8 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Catálogo, identidad propia, reserva/cancelación por fecha y concurrencia.

Actores: Cliente propio y personal autorizado; user no determina su identidad mediante payload.

Datos de partida: Horario de un cupo, sesiones D y D+7, C1/C2 habilitados y membresía que cubre o no cada sesión; lectura anterior a guardar/cancelar.

Dependencias y orden: MOD-01/03/04 antes de matricular; MOD-06/07/11 consumen matrícula, servicio y fecha.

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
| Catálogo de horarios, rutinas y plazas | [CP-M05-01](casos-de-uso.md) · CA-01 | P1 | Se exponen servicio/ejercicio, horas y plazas disponibles coherentes. |
| Matrícula con identidad de sesión | [CP-M05-02](casos-de-uso.md) · CA-03 | P1 | El servidor usa C1; el ID enviado no suplanta a C2. |
| Cancelación propia y liberación de plaza | [CP-M05-03](casos-de-uso.md) · CA-04 | P1 | La ajena se conserva; la propia se cancela y libera únicamente su plaza. |
| Persistencia de matrícula mediante RPC obligatoria | [CP-M05-04](casos-de-uso.md) · CA-05 | P1 | Se informa el fallo de persistencia; no se usa INSERT REST parcial ni se añade matrícula local. |
| Validación de fecha y cobertura de membresía | [CP-M05-05](casos-de-uso.md) · CA-08 | P1 | Todas se rechazan sin insertar ni consumir cupos; una fecha de otra semana válida sigue siendo reservable. |

### Pruebas PostgreSQL y concurrencia

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Matrículas concurrentes y duplicadas | [CP-M05-06](casos-de-uso.md) · CA-02 | P1 | Solo una matrícula ocupa la plaza; duplicar la misma sesión se rechaza sin superar cupo. |
| Reservas y cancelaciones aisladas por sesión | [CP-M05-07](casos-de-uso.md) · CA-07 | P1 | Las sesiones no heredan clientes ni cancelaciones; D libera cupo y D+7 conserva su reserva. |

### Pruebas de interfaz y navegación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Actualización del portal y lecturas obsoletas | [CP-M05-08](casos-de-uso.md) · CA-06 | P1 | La respuesta antigua no repone ni elimina matrículas confirmadas; el portal vuelve a consultar y conserva el último estado válido ante fallo. |

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
  tests/horarios_matriculas/integracion/test_enrollment_errors.py \
  tests/horarios_matriculas/integracion/test_schedule_enrollment.py \
  tests/horarios_matriculas/integracion/test_schedule_sessions.py \
  tests/horarios_matriculas/postgres/test_schedule_sessions_postgres.py -q)
(cd frontend && node --test \
  tests/horarios_matriculas/unitarias/landing-schedules.test.js \
  tests/horarios_matriculas/unitarias/schedule-calendar.test.js \
  tests/horarios_matriculas/unitarias/schedule-enrollment.test.js \
  tests/transversales/integracion/module-error-control.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

Requiere RPC especializada y migraciones por dependencia. Una reserva semanal no autoriza asistencia de otra fecha. Las consultas viejas no restauran cancelaciones.

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
