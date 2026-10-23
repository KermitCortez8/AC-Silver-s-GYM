# Corrección de los 12 hallazgos prioritarios

Fuente: [auditoría completa](auditoria-code-smells.md). La auditoría conserva enlaces al commit original; esta página describe las correcciones posteriores. Los hallazgos 13–42 permanecen como trabajo posterior, aunque algunas modificaciones necesarias también reducen partes de esos problemas. El PR se mantiene abierto y no se fusiona con `develop`.

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
4. Desplegar el backend y frontend de esta rama después de las migraciones. Las escrituras requieren `SUPABASE_SERVICE_ROLE_KEY`; una clave anónima no puede ejecutar estas RPC. Mantener esa clave exclusivamente en backend.

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
