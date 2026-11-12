# Plan de pruebas · MOD-06 · Asistencias

**ID:** PP-MOD-06 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
118 CT (101 backend y 17 frontend) y 15 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Entrada/salida, aforo, horario/fecha, bloqueo cruzado, auditoría y automatización.

Actores: Admin registra/corrige/anula; user consulta exclusivamente su historial; staff/trainer no escriben.

Datos de partida: Visitas general/clase abiertas y cerradas, capacidad uno, request_id repetido, clase 09:00–10:00, salida 11:00 y 11:00:01, general 09:00 con límite 12:00; reloj Lima.

Dependencias y orden: MOD-01/03/05 y controles de privacidad, reloj y transacciones de transversales.

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
| Entrada general con reloj del servidor | [CP-M06-01](casos-de-uso.md) · CA-01 | P1 | La entrada usa fecha/hora del servidor Lima y membresía real; la hora enviada no gobierna el registro. |
| Aforo compartido entre general y clases | [CP-M06-02](casos-de-uso.md) · CA-02 | P1 | No se supera una persona; general y clase consumen el mismo aforo. |
| Idempotencia de entrada antes/después de salir | [CP-M06-03](casos-de-uso.md) · CA-03 | P1 | Siempre vuelve la visita original; no crea otra ni reabre la cerrada. Una visita nueva requiere otra identidad de solicitud. |
| Permisos administrativos de escritura | [CP-M06-04](casos-de-uso.md) · CA-04 | P1 | Los roles no autorizados son rechazados y no escriben; solo admin ejecuta la operación permitida. |
| Historial, semana y exportación privados | [CP-M06-05](casos-de-uso.md) · CA-05 | P1 | El filtro no amplía la identidad de sesión; solo salen datos propios y ninguna auditoría interna. |
| Corrección, anulación, versión y auditoría | [CP-M06-06](casos-de-uso.md) · CA-06 | P1 | Se mantiene auditoría de las acciones y control de versión; resumen/aforo reflejan los cambios confirmados. |
| Revalidación de clase terminada | [CP-M06-07](casos-de-uso.md) · CA-07 | P1 | Se rechaza la nueva entrada con motivo de clase terminada y sin guardar; la salida pendiente sigue disponible. |
| Cierre general automático después de tres horas | [CP-M06-08](casos-de-uso.md) · CA-11 | P1 | En el límite la salida manual completa; superarlo produce incompleta con cierre automático, libera aforo y distingue ese cierre de una salida real. |
| Aviso cruzado y margen de treinta minutos | [CP-M06-09](casos-de-uso.md) · CA-02, CA-08, CA-09 | P1 | El aviso usa margen inclusivo y origen correcto; otra fecha/franja lejana no ofrece salida cruzada. Ocultar aviso no levanta el bloqueo de visita abierta ni amplía el intervalo de admisión. |

### Pruebas PostgreSQL y concurrencia

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Bloqueo cruzado y carreras de dos entradas | [CP-M06-10](casos-de-uso.md) · CA-02 | P1 | Antes de salir se rechaza sin doble visita; después se permite si cumple admisión. En la carrera solo se guarda una entrada. |
| Intervalo de entrada y matrícula de la fecha correcta | [CP-M06-11](casos-de-uso.md) · CA-09 | P1 | Solo el intervalo [09:00,10:00) es admisible; la matrícula de otra semana no autoriza y los rechazos no guardan. |
| Salida de clase, límite original y tardanza | [CP-M06-12](casos-de-uso.md) · CA-10 | P1 | 11:00 completa; después queda incompleta. Sin salida sigue abierta, consume aforo y no inventa hora; editar horario no modifica el límite guardado. |
| Programación SQL del cierre general | [CP-M06-13](casos-de-uso.md) · CA-11 | P1 | Debe guardar cierre automático/auditoría y liberar aforo; registrar fallo o bloqueo de esquema mientras 023 esté vacía. El resultado histórico no aprueba esta ejecución. |
| Recorrido de clase sin salida y recuperación | [CP-M06-14](casos-de-uso.md) · CA-02, CA-03, CA-05, CA-10 | P1 | Una única visita pasa a incompleta sin salida inventada; mantiene aforo/bloqueo hasta salida real, conserva auditoría y el cliente solo lee lo propio. |

### Pruebas de interfaz y navegación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Calendario, matriculados y selección por fecha | [CP-M06-15](casos-de-uso.md) · CA-08 | P2 | Calendario/agenda comparten sus datos y cupos; solo aparecen matriculados de la fecha actual y la selección vieja no reaparece. |

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
  tests/asistencias/integracion/test_general_attendance.py \
  tests/asistencias/integracion/test_schedule_attendance.py \
  tests/asistencias/postgres/test_attendance_deadline_postgres.py \
  tests/asistencias/postgres/test_attendance_enrollment_flow_postgres.py \
  tests/asistencias/postgres/test_automatic_attendance_postgres.py \
  tests/horarios_matriculas/postgres/test_schedule_sessions_postgres.py \
  tests/transversales/integracion/test_scoped_operations.py -q)
(cd frontend && node --test \
  tests/asistencias/interfaz/flujos.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

La migración 023 está vacía: los cuatro casos SQL generales y CP-M06-13 permanecen bloqueados hasta disponer del contrato SQL. Las pruebas de clase/cron se pueden verificar de forma independiente sin afirmar que comprueban cierre general.

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
