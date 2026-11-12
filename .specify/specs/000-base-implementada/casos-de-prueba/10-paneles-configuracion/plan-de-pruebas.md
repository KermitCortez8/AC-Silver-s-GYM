# Plan de pruebas · MOD-10 · Paneles y configuración

**ID:** PP-MOD-10 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
41 CT (18 backend y 23 frontend) y 6 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Indicadores, fechas, configuración, recursos por sección y sesiones aisladas.

Actores: Panel correspondiente a cada rol; resumen/configuración internos para admin/staff.

Datos de partida: Membresías pagadas, impagas, futuras y vencidas; cambio de día UTC/Lima; capacidad cero; dos instancias Pinia y consultas pendientes de secciones diferentes.

Dependencias y orden: Datos controlados de MOD-02/03/06/08/09; aislamiento/errores compartidos.

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
| Fechas y serie de siete días en Lima | [CP-M10-01](casos-de-uso.md) · CA-02 | P1 | Agrupación usa America/Lima y conserva exactamente las fechas de negocio esperadas. |

### Pruebas de integración

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Indicadores por pago, activación y vigencia | [CP-M10-02](casos-de-uso.md) · CA-01 | P1 | Solo las pagadas vigentes se cuentan activas; pendientes/activables/vencidas se distinguen. |
| Consultas por sección, health y fallos parciales | [CP-M10-03](casos-de-uso.md) · CA-03 | P1 | Cada sección lee sus dependencias, health no materializa historiales y el fallo conserva estado previo sin invalidar áreas ajenas. |
| Aislamiento de aplicaciones, servicios y sesiones | [CP-M10-04](casos-de-uso.md) · CA-04 | P1 | Los servicios/respuestas siguen su instancia; no se mezclan transportes ni datos de sesión. |
| Validación y conservación de configuración | [CP-M10-05](casos-de-uso.md) · CA-01, CA-03 | P1 | Se informa error sin convertir cero en uno ni guardar una configuración parcial; permanece el último valor válido. |

### Pruebas de interfaz y navegación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Navegación con consultas o transiciones lentas | [CP-M10-06](casos-de-uso.md) · CA-05 | P2 | La consulta ajena no bloquea el módulo; finalización vieja no cierra transición nueva y se limpian temporizadores. |

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
  tests/paneles_configuracion/integracion/test_supabase_refresh.py \
  tests/transversales/integracion/test_module_error_control.py \
  tests/transversales/integracion/test_review_regressions.py -q)
(cd frontend && node --test \
  tests/paneles_configuracion/integracion/application-context.test.js \
  tests/paneles_configuracion/integracion/module-navigation.test.js \
  tests/paneles_configuracion/integracion/scoped-gym-modules.test.js \
  tests/paneles_configuracion/integracion/sync-resources.test.js \
  tests/paneles_configuracion/unitarias/client-dashboard.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

Distinguir aforo del día del resumen general de ocupación instantánea de asistencia. Health saludable no acredita datos ni casos funcionales.

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
