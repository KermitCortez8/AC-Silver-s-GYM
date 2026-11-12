# Plan de pruebas · MOD-01 · Identidad y acceso

**ID:** PP-MOD-01 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
29 CT (10 backend y 19 frontend) y 6 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Acceso, Google, revocación, identidad estable y navegación.

Actores: Personal admin/staff/trainer y clientes activos, inactivos, pendientes y vencidos; identidad Google simulada.

Datos de partida: Cuentas de dos clientes y dos roles; token emitido antes de desactivar; consulta demorada durante logout; Google verificado por doble.

Dependencias y orden: MOD-03 para las condiciones de acceso; MOD-10 y transversales para aislamiento y sesiones.

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
| Ingreso y revocación de cuentas internas | [CP-M01-01](casos-de-uso.md) · CA-01 | P1 | Antes de desactivar hay sesión; después se deniegan ambos accesos sin publicar datos. |
| Acceso condicionado por membresía y activación | [CP-M01-02](casos-de-uso.md) · CA-02 | P1 | Ninguna variante concede sesión privada solo por tener el indicador de cuenta activo. |
| Autenticación y vinculación Google con cuenta desactivada | [CP-M01-03](casos-de-uso.md) · CA-03 | P1 | Ambos intentos respetan la desactivación; Google no restablece el acceso. |
| Cierre/cambio de sesión y descarte de datos antiguos | [CP-M01-04](casos-de-uso.md) · CA-05 | P1 | Se vacían datos/colas de C1 y su respuesta tardía no modifica la sesión de C2. |

### Pruebas PostgreSQL y concurrencia

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Identidad estable al cambiar rol o recrear usuarios | [CP-M01-05](casos-de-uso.md) · CA-04 | P1 | El cambio de rol conserva el ID y el alta posterior no reutiliza el ID eliminado. |

### Pruebas de interfaz y navegación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Navegación pública y restricciones del panel | [CP-M01-06](casos-de-uso.md) · CA-06 | P1 | La landing sigue accesible; no cambia el rol ni concede panel ajeno; la caducidad conserva el motivo en login. |

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
  tests/identidad_acceso/unitarias/test_security_utils.py \
  tests/membresias_pagos/integracion/test_membership_expiration.py \
  tests/transversales/integracion/test_review_regressions.py \
  tests/transversales/postgres/test_atomic_transactions_postgres.py -q)
(cd frontend && node --test \
  tests/identidad_acceso/integracion/public-navigation.test.js \
  tests/identidad_acceso/integracion/session-validation.test.js \
  tests/identidad_acceso/unitarias/decode-jwt.test.js \
  tests/identidad_acceso/unitarias/default-membership.test.js \
  tests/identidad_acceso/unitarias/format-user-data.test.js \
  tests/identidad_acceso/unitarias/invalid-email.test.js \
  tests/identidad_acceso/unitarias/user-role.test.js \
  tests/identidad_acceso/unitarias/valid-email.test.js \
  tests/identidad_acceso/unitarias/valid-user.test.js \
  tests/transversales/integracion/navigation-stores.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

El acceso real a Google y la configuración del proveedor no se acreditan con el doble. El permiso se contrasta en API además del router.

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
