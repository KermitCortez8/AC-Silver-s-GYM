# Corrección de los 12 hallazgos prioritarios

Fuente: [auditoría completa](auditoria-code-smells.md). La auditoría conserva enlaces al commit original; esta página describe las correcciones posteriores. La primera intervención se limitó a los hallazgos 01–12. Las secciones posteriores y la [revisión de objetivos](revision-refactorizacion.md) registran avances adicionales; la numeración histórica no implica que todos los hallazgos 13–42 sigan intactos ni que estén todos cerrados.

| Hallazgo | Cambio implementado | Regresión que lo comprueba |
| --- | --- | --- |
| 01 | Escrituras de inventario, productos, imágenes y membresías requieren personal autorizado. Los pedidos y membresías se filtran por el cliente de la sesión; el actor de movimientos no sale del payload. | Acceso sin token 401, roles incorrectos 403, personal autorizado y aislamiento entre clientes. |
| 02 | Consecutivo global para usuarios, código visible persistido y estable tras cambiar de rol; marcas crecientes evitan reutilizar IDs borrados. | Tres roles con IDs diferentes, cambio de rol, recarga real y borrado seguido de nueva alta. |
| 03 | Lectura y escritura de cupos, usos, etiquetas y asociación de promoción a membresía. | Conversión de ida y vuelta, recarga de promoción y asociación de membresía desde PostgreSQL. |
| 04 | Campos comerciales, ubicación y observaciones de inventario; descripción y unidad de productos. | Conversión de ida y vuelta y recarga desde PostgreSQL. |
| 05 | Borrados esperados y confirmados antes de actualizar el estado local. | HTTP 500 conserva las filas; mientras la respuesta está pendiente no desaparecen; 204 confirma el borrado. |
| 06 | Reinicio de datos de negocio, errores y cachés; generación de sesión que rechaza resultados antiguos, incluso durante la lectura de JSON. | Logout, sustitución de sesión, consultas pendientes, tareas todavía en cola y guardados tardíos. |
| 07 | Operaciones monetarias en céntimos y redondeo decimal consistente en backend, carrito, registro, landing y promoción. | 79 − 10 % = 71.10; medio céntimo; descuento fijo; IGV y total. |
| 08 | Fecha y hora civil del gimnasio en `America/Lima`; UTC se conserva para instantes y cálculo de fechas civiles a mediodía. | Frontera de medianoche de Perú y comparación fecha/hora para el mismo instante. |
| 09 | Activación y previsiones usan la duración explícita del plan, en días; el nombre deja de determinar la vigencia. | Plan MENSUAL de 45 días, cruce de mes y activación idempotente. |
| 10 | Una RPC confirma inserciones, actualizaciones, borrados y detalles de venta en una transacción. Se retiró el sincronizador REST con compensaciones. No hay fallback inseguro si falta la RPC. | PostgreSQL revierte borrado, reemplazo de detalles y actualizaciones cuando falla una restricción. |
| 11 | Webhook Stripe y almacenamiento síncrono de imágenes se ejecutan en el pool de hilos. La imagen se lee con límite antes de almacenarla. | El webhook bloqueante permite que avance otra tarea del bucle de eventos; validación de subida existente. |
| 12 | Locks de tablas y comparación de instantáneas dentro de PostgreSQL; relectura/reintento ante conflicto; identidad creciente en la base. | Dos repositorios venden simultáneamente sin exceder stock y crean usuarios sin colisiones; instantánea obsoleta rechazada; RPC denegada a `anon`. |

## Aplicación de cambios de base de datos

1. Aplicar las migraciones anteriores requeridas por la aplicación, incluidas las RPC de matrícula y asistencia (002, 005, 006 y 013). No ejecutar archivos `*_rollback.sql` como migraciones normales.
2. Ejecutar `backend/migrations/014_preserve_business_fields.sql` en Supabase SQL Editor. Añade columnas y completa el código estable de los usuarios existentes; no cambia sus IDs numéricos.
3. Ejecutar `backend/migrations/015_atomic_gym_transactions.sql`. Crea el contador creciente y las RPC de lectura de identidades y confirmación transaccional. Se pueden ejecutar ambas migraciones nuevamente sin duplicar datos.
4. Ejecutar `backend/migrations/016_transaction_sequence_permissions.sql` como propietario de las secuencias en SQL Editor. Concede a `service_role` los permisos de lectura y avance de las secuencias de las tablas admitidas por la transacción; no concede permisos a `anon` ni `authenticated`. Es idempotente y no cambia filas de negocio.
5. Desplegar el backend y frontend de esta rama después de las migraciones. Las escrituras requieren `SUPABASE_SERVICE_ROLE_KEY`; una clave anónima no puede ejecutar estas RPC. Mantener esa clave exclusivamente en backend.

La tarea prepara los scripts y valida su ejecución local; **no aplica migraciones ni cambios de datos a producción**. No se debe desplegar solo el backend nuevo sobre una base sin 014/015: la operación falla y no recurre a escrituras parciales. Un rollback de código debe revisarse expresamente: reactivar el sincronizador anterior reintroduciría los problemas 10 y 12.

## Estrategia y límites

La solución conserva los contratos de la API y los flujos existentes, pero cambia deliberadamente las rutas internas que antes admitían llamadas sin permisos. Los clientes reciben únicamente sus propios pedidos. Las RPC de matrícula y asistencia conservan su protección específica.

La transacción general verifica la instantánea completa utilizada por el comando y bloquea sus tablas en un orden fijo. Favorece integridad sobre concurrencia de escrituras: todavía existen instantáneas amplias y lecturas completas, como documenta el hallazgo 22. Si tres intentos encuentran conflictos, se pide actualizar y reintentar; no se sobreescribe el trabajo de otra instancia. Los fallos ambiguos de red requieren refrescar antes de repetir una acción; no se reintentan automáticamente como conflictos SQL.

Las identidades pueden tener huecos después de un rollback, porque las secuencias PostgreSQL no se revierten. Es intencional: importa su unicidad y que una cuenta borrada no reutilice su identidad, no que la numeración sea continua. La configuración del gimnasio conserva su clave singleton `id_config=1`.

## Verificación local

Backend:

```bash
backend/.venv/bin/python -m pytest backend/tests/ -q
backend/.venv/bin/python -m flake8 backend/app backend/presentation backend/application backend/domain backend/infrastructure backend/tests --jobs=1 --select=E9,F63,F7,F82
```

Frontend (Node 22):

```bash
cd frontend
npm test
npm run build
```

PostgreSQL real, aislado y sin puertos publicados (requiere Docker):

```bash
docker run --rm -d --name gym-priority-postgres --network none \
  -e POSTGRES_PASSWORD=local-tests-only -e POSTGRES_DB=gym_test postgres:16-alpine
# Esperar a que pg_isready indique que el servidor está listo.
docker exec gym-priority-postgres pg_isready -U postgres -d gym_test
GYM_TEST_POSTGRES_CONTAINER=gym-priority-postgres \
  backend/.venv/bin/python -m pytest backend/tests/test_atomic_transactions_postgres.py -q
docker stop gym-priority-postgres
```

La suite SQL usa únicamente la base desechable `gym_test` y valida ese nombre antes de recrear el esquema. Sin la variable explícita, esas pruebas se omiten; no se conectan a Supabase ni utilizan credenciales de producción. El esquema de pruebas contiene las columnas y restricciones relevantes, pero no sustituye una validación de despliegue sobre una copia del esquema completo de la instalación.

Resultados finales:

- Backend en Docker con Python 3.12, sin red: **273 pruebas pasan** y lint seleccionado sin errores. Las pruebas SQL requieren la variable explícita y se ejecutaron aparte.
- PostgreSQL 16 real y desechable: **9 pruebas pasan**, incluidas atomicidad, permisos de RPC, concurrencia, persistencia de campos y backfill idempotente de códigos históricos.
- Frontend con Node 22 en Docker, sin red: **94 pruebas pasan**.
- Compilación Vite de producción y `git diff --check`: correctos.

El esquema de pruebas y los nuevos auxiliares se incluyen en el target Docker `test`, manteniéndolos fuera de la imagen de producción. La advertencia de deprecación existente de `httpx`/Starlette no impide la ejecución de las pruebas.

## Seis hallazgos de la revisión posterior a la refactorización

Estos seis casos amplían el seguimiento anterior; su numeración corresponde a la
revisión posterior de `4dcba89`, no a los 42 grupos de la auditoría original.

| Caso | Corrección | Verificación |
| --- | --- | --- |
| 1. Acceso de personal inactivo | Una política compartida comprueba el estado al emitir y recuperar sesiones, y antes de vincular Google. Normalizar o editar un usuario conserva su desactivación. | Contraseña, Google vinculado y sin vincular, token emitido antes de desactivar, rutas protegidas y recarga SQL. |
| 2. Autor de progreso falsificable | La ruta asigna el autor desde la sesión verificada, aunque el navegador envíe otro `id_usuario` o lo omita. | Peticiones HTTP con autor falsificado y ausente guardan al entrenador autenticado. |
| 3. Fecha de alta reemplazada al editar | El dominio conserva `fecha_registro` del registro existente y asigna la fecha de negocio solo al crear o cuando falta. La normalización también conserva el campo. | Cambio de día, fecha manipulada en el payload y edición con recarga desde PostgreSQL. |
| 4. Desglose de pedido perdido | El subtotal se reconstruye con los importes de las líneas persistidas, en céntimos. El IGV es la diferencia con el total guardado, sin consultar precios ni tasas actuales. | Ida y vuelta con redondeos y recarga SQL de un pedido de 10 + 1,80 = 11,80. |
| 5. Cascada de cliente incompleta | El comando incluye matrículas, progreso y horarios de servicio en la misma transacción; elimina los datos dependientes y recalcula los cupos. | Aislamiento entre clientes, claves foráneas restrictivas, liberación de cupos y rollback SQL si falla el borrado del cliente. |
| 6. Membresías activas contadas como cero | El resumen reutiliza `membership_current`, que exige estado activo, pago confirmado y fechas vigentes. Usa el mismo reloj de negocio para la asistencia diaria. | Estados canónico y antiguo, membresías impagas, vencidas y futuras, y último día de vigencia. |

Las regresiones están en [test_review_regressions.py](../backend/tests/test_review_regressions.py)
y los contratos reales de persistencia en
[test_atomic_transactions_postgres.py](../backend/tests/test_atomic_transactions_postgres.py).
Se mantienen las pruebas anteriores; sus fixtures de personal autorizado ahora
declaran explícitamente una cuenta activa y un actor autenticado.

Verificación local: 371 pruebas de backend, 13 pruebas de PostgreSQL aislado y
121 pruebas de frontend pasan. El lint Python seleccionado y `git diff --check`
también pasan. Las 13 pruebas SQL se omiten en la ejecución ordinaria y se
ejecutaron aparte con `GYM_TEST_POSTGRES_CONTAINER`.

Estos cambios no requieren nuevas migraciones. Para ventas históricas sin líneas
de detalle se conserva el total conocido; no se inventa un desglose fiscal que no
puede recuperarse. La comprobación de estado de sesiones usa la política de
refresco existente del repositorio (TTL de cinco segundos). Las pruebas SQL se
ejecutan exclusivamente en PostgreSQL desechable, sin cambios en producción.

## Cuatro grupos de smells persistentes

| Grupo | Cambio implementado | Evidencia |
| --- | --- | --- |
| Recursos demasiado amplios | Los comandos de horarios y tienda declaran sus dependencias por operación. Guardar una rutina pasa de once recursos a uno. El catálogo auxiliar de nombres de pedidos no reemplaza la instantánea de productos en caché. | Un fallo de asistencia no impide guardar rutinas; una escritura concurrente real de asistencia no causa conflicto en ese comando; lectura auxiliar de nombres conserva la pareja estado/instantánea anterior. |
| Lecturas completas en resumen y matrícula | El resumen consulta conteos, visitas abiertas y ocho entradas recientes. Matricular carga cinco recursos, conservando la RPC atómica. | Con 2.501 registros históricos cerrados el resumen no llama al historial paginado; conserva visitas de la noche anterior y excluye anulaciones. Matrícula funciona sin consultar inventario. |
| Vistas extensas y registro duplicado | Clientes y tienda extraen diálogos y composables de edición, pagos e imágenes. Registrar por código delega en el registro por ID. | Pruebas de edición, stock, activación y errores; renderizado SSR de los diálogos y galería. Los scripts de las vistas pasan de 600 a 227 y de 449 a 205 líneas, respectivamente. |
| Adaptadores globales mutables | Instalación explícita por Pinia, configuración copiada e inmutable y servicios que capturan su propietario y sus adaptadores. | Dos aplicaciones conservan configuración y transportes distintos; cerrar la sesión B no invalida A; cerrar A rechaza sus respuestas pendientes, incluso construyendo su gateway cuando B está activa. |

Regresiones específicas:
[test_remaining_smells.py](../backend/tests/test_remaining_smells.py),
[26-stock-edit-forms.test.js](../frontend/tests/26-stock-edit-forms.test.js) y
[28-application-context.test.js](../frontend/tests/28-application-context.test.js).

Verificación de esta revisión (Python 3.14, Node 24 y PostgreSQL 16): **378 pruebas
de backend pasan**, con **14 SQL omitidas** en la ejecución ordinaria; las **14
SQL pasan por separado** en una base desechable. Las **128 pruebas de frontend**,
la compilación Vite, el lint Python seleccionado y `git diff --check` pasan.
Para reproducir backend se necesita `AUTH_SECRET_KEY` de al menos 32 bytes;
se utilizó una clave sintética exclusiva del proceso de pruebas. No se requieren
nuevas migraciones por estos cuatro cambios.

El resumen evita transferir el historial cerrado, pero los conteos exactos aún
tienen coste en PostgreSQL y las visitas abiertas pueden paginarse en el
transporte. Las instantáneas generales y otros listados siguen siendo completos
por recurso. La extracción de dos vistas tampoco cierra por sí sola el hallazgo
28 para todas las pantallas. El dictamen y estos límites se detallan en la
[revisión de objetivos](revision-refactorizacion.md).

## Seguimiento de las vistas de asistencia y del entrenador

Se separaron los flujos de `AttendanceView.vue` y
`TrainerRoutineMonitorView.vue` en componentes y composables específicos. Las
vistas conservan navegación y ensamblaje. La asignación directa y por diálogo
comparten el guardado, y la pantalla y el diálogo de ejercicios comparten un solo
temporizador. Los detalles y medidas antes/después están en la
[revisión de objetivos](revision-refactorizacion.md#seguimiento-responsabilidades-de-las-vistas).

La suite [29-view-flows.test.js](../frontend/tests/29-view-flows.test.js) cubre los
contratos sensibles a la extracción: búsquedas obsoletas, reintentos de entrada,
guardados pendientes, errores de refresco, conservación del borrador y edición
desde los componentes extraídos. No se modificó el backend para esta extracción.
Verificación: **137 pruebas de frontend pasan**, compilación Vite de producción y
`git diff --check` correctos.

## Permiso de secuencias detectado con la configuración real

Durante la comprobación visual se verificaron las lecturas reales de salud,
catálogo y resumen de asistencia. Al intentar crear las cuentas de prueba
autorizadas, la RPC falló con `42501: permission denied for sequence
USUARIO_id_usuario_seq`. La transacción revirtió el alta; no se creó la cuenta.
La migración 015 consulta las secuencias y llama a `setval` bajo `SECURITY INVOKER`,
pero no concedía los permisos correspondientes.

La migración 016 añade esos permisos únicamente para `service_role` y las
secuencias asociadas a las tablas admitidas por la RPC. La prueba SQL reproduce
el fallo sin `UPDATE`, comprueba el rollback, aplica 016 dos veces y verifica el
alta y el avance de identidad. Comprueba también que no se amplían los permisos
de otras secuencias ni de los roles del navegador. El esquema de pruebas dejó
de conceder todos los permisos de secuencia por adelantado, porque ocultaba esta
carencia de la migración. **Las 15 pruebas SQL pasan en PostgreSQL 16 aislado.**

El archivo está preparado y validado localmente. Su aplicación en Supabase
requiere SQL Editor o una conexión con permisos de propietario; la clave REST de
los `.env` no permite ejecutar `GRANT`. El estado de la comprobación visual se
registra por separado en [comprobacion-visual.md](comprobacion-visual.md).

Con las cuentas existentes proporcionadas posteriormente por el usuario se
completaron el acceso normal y la revisión visual de lecturas y diálogos en ambas
pantallas. No se crearon usuarios ni se guardaron cambios en datos de negocio.
Esto permite cerrar la comprobación visual de lectura; el fallo de alta sigue
requiriendo la aplicación de 016.
