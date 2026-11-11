# Plan de pruebas · MOD-02 · Clientes

**ID:** PP-MOD-02 · **Versión:** 1.0 · **Estado:** preparado para ejecución.
Aplica el [plan general](../plan-de-pruebas.md). El catálogo propio contiene
102 CT (66 backend y 36 frontend) y 9 escenarios CP.
Estos recuentos describen el alcance; los resultados del catálogo son históricos.

## Objetivo, actores y preparación

Verificar: Búsqueda, alta, edición, preregistro, reconciliación y borrado con historial.

Actores: Visitante, admin y staff en las operaciones que permite la API.

Datos de partida: C1 y C2 con IDs/DNI distintos, plan activo y promoción; solicitud temporal impaga, pagada, en proceso e incierta; cliente con matrícula/progreso y venta pagada.

Dependencias y orden: MOD-01, MOD-03 y MOD-04 antes del recorrido de alta; MOD-05/07/09 para dependencias de borrado.

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
| Resolución y búsqueda de identidad del cliente | [CP-M02-01](casos-de-uso.md) · CA-03 | P1 | Se respeta la prioridad de identificación y nunca se devuelve C2 por una coincidencia ajena. |

### Pruebas de integración

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Registro administrativo sin pago | [CP-M02-02](casos-de-uso.md) · CA-01 | P1 | Se crea un cliente administrativo y una membresía EN_TRAMITE/PENDIENTE, sin activación ni pago inventado. |
| Edición conservando identidad, origen y fecha | [CP-M02-03](casos-de-uso.md) · CA-02 | P1 | Solo cambian campos personales; se conservan código, origen y fecha de registro. |
| Recuperación de alta tras error de checkout | [CP-M02-04](casos-de-uso.md) · CA-04 | P1 | Se reutilizan alta e importe guardados; no aparece un segundo cliente ni una segunda membresía. |
| Preregistro público privado antes del pago | [CP-M02-05](casos-de-uso.md) · CA-07 | P1 | Existe únicamente solicitud temporal privada; no se crean cliente/membresía ni se publica una identidad temporal como cliente. |
| Caducidad y reconciliación de solicitudes | [CP-M02-06](casos-de-uso.md) · CA-07 | P1 | Se archiva/libera cupo una sola vez solo cuando corresponde; el pago incierto o en proceso conserva la solicitud y nunca elimina un cliente pagado. |

### Pruebas PostgreSQL y concurrencia

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Borrado de cuenta conservando ventas y comprador | [CP-M02-07](casos-de-uso.md) · CA-05 | P1 | En éxito se retira la cuenta y sus dependencias aplicables, conservando venta/comprador/líneas/stock; ante fallo se revierte todo; C2 permanece. |
| Conversión de preregistro concurrente e idempotente | [CP-M02-08](casos-de-uso.md) · CA-07 | P1 | Se convierte una sola vez; no duplica cliente/pago; una transacción fallida no deja entidades parciales y puede reintentarse. |

### Pruebas de interfaz y navegación

| Funcionalidad | Caso / criterio | Prioridad | Resultado de aceptación |
| --- | --- | --- | --- |
| Catálogos remotos, borrador e importe histórico | [CP-M02-09](casos-de-uso.md) · CA-06 | P1 | Solo se ofrecen opciones válidas; no hay precios locales de reemplazo; se conserva el borrador y el contrato histórico al editar. |

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
  tests/clientes/integracion/test_admin_client_payment.py \
  tests/clientes/integracion/test_preregistration_gateway.py \
  tests/clientes/integracion/test_public_preregistrations.py \
  tests/clientes/postgres/test_client_deletion_postgres.py \
  tests/clientes/postgres/test_public_preregistrations_postgres.py \
  tests/clientes/unitarias/test_clients_lookup.py \
  tests/transversales/integracion/test_review_regressions.py \
  tests/transversales/integracion/test_scoped_operations.py -q)
(cd frontend && node --test \
  tests/clientes/interfaz/client-catalog.test.js \
  tests/clientes/interfaz/client-flow-control.test.js \
  tests/clientes/interfaz/formularios.test.js \
  tests/clientes/unitarias/client-directory.test.js \
  tests/clientes/unitarias/client-identity.test.js \
  tests/clientes/unitarias/find-client.test.js \
  tests/clientes/unitarias/normalizers.test.js)
```

Los comandos se ejecutan desde la raíz con el entorno previamente preparado.
Para una prueba aislada, usar `command` del JSON desde el componente indicado.
Cuando una selección incluya SQL, establecer `GYM_TEST_POSTGRES_CONTAINER` solo
para el contenedor desechable. No ejecutar suites SQL concurrentes que reutilicen
la misma base: sus fixtures preparan y truncan tablas.

## Evidencia, límites y cierre

Borrado con ventas requiere 025 en la base aislada. El registro público no debe aparecer como cliente antes de verificar pago. No expirar una solicitud con resultado de pago incierto.

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
