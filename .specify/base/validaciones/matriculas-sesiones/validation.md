# Control de errores de matrículas y asistencia por sesión

Fecha: 2026-10-30. Implementación directa por petición del usuario, sin activar
Spec Kit ni crear specs, planes o tareas. Contratos: MOD-05, MOD-06 y MOD-11.

## Síntoma y comportamiento corregido

La matrícula estaba vinculada solo al horario recurrente. `scheduleOccurrences`
proyectaba al cliente en todas las semanas posteriores al alta; los cupos y el
listado administrativo también se calculaban por horario sin separar sesiones.
La selección de un bloque futuro de asistencia consultaba el listado de hoy.

Cada matrícula guarda ahora `fecha_clase`, distinta de la fecha de alta. El cliente
solo aparece en esa sesión; otra semana requiere una matrícula explícita, con
identificador propio. Cupos y duplicados se validan por horario/fecha, conservando
los locks y RPC atómicos. Cancelar una sesión no afecta las demás reservas.
Se rechazan fechas imposibles, pasadas, incompatibles con el día del horario o
fuera de la vigencia de la membresía; la fecha de una matrícula persistida no se
puede mover mediante SQL: debe cancelarse y reservarse otra sesión.

El catálogo ofrece `ocupacion_por_fecha`. El calendario mantiene la recurrencia
de la programación, pero obtiene cupos e inscripción de cada fecha. La vista de
matrículas envía la fecha elegida al guardar y cancela el identificador de esa
sesión. Los clientes antiguos sin fecha explícita reservan solo la siguiente
sesión del día configurado, sin generar una inscripción permanente.

Asistencia consulta `/horarios/{id}/clientes?fecha=AAAA-MM-DD` y filtra matrículas
y registros por esa fecha. Al cambiar de semana se limpia la selección; las
respuestas de otra selección o fecha se descartan. Si falla la consulta, se
muestra el error y no los clientes de la selección anterior. Una entrada solo
puede usar una matrícula para el día actual del servidor de Perú, incluso
mediante una petición directa o la RPC. Las salidas pendientes conservan su
comportamiento y los registros históricos no se eliminan.

La confirmación de matrícula indica una sola sesión y enlaza su fecha. La cola
genera recordatorios únicamente para la fecha reservada; no renueva semanalmente
los avisos de una matrícula anterior. Se ajustaron las plantillas de backend y
Edge Function sin enviar correos reales.

## Migración y recuperación

[019_schedule_sessions.sql](../../../../backend/migrations/019_schedule_sessions.sql)
requiere el esquema existente y las migraciones por nombre:
`002_harden_schedule_enrollment.sql`, `006_schedule_email_notifications.sql` y
`018_attendance_schedule_exit_deadline.sql`, con sus dependencias previas.
Debe aplicarse antes de usar el nuevo backend. La ausencia de la nueva RPC se
informa como esquema pendiente, sin recurrir a INSERT parciales.

El backfill asigna a las matrículas históricas la primera sesión correspondiente
desde su fecha de alta; no toma la semana de despliegue ni renueva clientes.
Las filas sin fecha fiable permanecen sin sesión y no autorizan entradas. Se
conservan matrículas y visitas históricas. La migración se ejecutó repetidamente
en PostgreSQL real, incluida una fila histórica, sin cambiar la fecha ya asignada.

Recuperación: volver al backend anterior y restaurar las funciones/triggers desde
002/006/018, manteniendo la columna y sus datos. El índice antiguo de unicidad
por cliente/horario no puede restaurarse sin resolver primero las matrículas
válidas de ese cliente en distintas fechas. Toda la migración es transaccional.

## Comprobaciones reales

Dependencias Python en `/tmp/gym-weekly-venv`; clave de autenticación sintética.
PostgreSQL 16 en `gym-weekly-postgres`, contenedor desechable sin red, base
`gym_test` y credenciales sintéticas. `GYM_TEST_POSTGRES_CONTAINER` apuntó solo a
ese contenedor; no se utilizaron las bases ni contenedores de la aplicación.

| Comando / procedimiento | Resultado |
| --- | --- |
| `python -m pytest tests/ -q` desde backend con el contenedor de pruebas | 655 aprobados, 0 fallos, 0 omitidos |
| `python -m pytest tests/test_schedule_sessions.py tests/test_schedule_attendance.py -q` | 31 aprobados tras el ajuste final del aviso de entrada futura |
| `python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` desde backend | 0 errores |
| `npm test` desde frontend | 270 aprobados, 0 fallos, 0 omitidos |
| `npm run build` desde frontend | Compilación correcta |
| `deno check supabase/functions/schedule-emails/index.ts` | Correcto |
| `deno test supabase/tests/` | 7 aprobados |
| Chromium/Playwright con API y sesiones sintéticas locales | Reserva por fecha, cancelación aislada, listas distintas entre semanas, entrada futura bloqueada y fallo de consulta sin clientes anteriores; 0 errores de página y sin desbordamiento horizontal |
| `python .specify/.codex/hooks/validate.py` | Documentación válida: 61 archivos, 13 contratos |
| `python -B -m unittest discover -s .specify/tests -v` | 13 aprobados |
| `git diff --check` | Sin errores de espacios |

La suite completa pasó después de corregir fixtures antiguos que representaban
matrículas sin fecha. Las nuevas regresiones SQL prueban concurrencia del último
cupo, duplicados por sesión, cancelación aislada, rechazo de asistencia de otra
semana, migración repetible, permisos privados y recordatorios por fecha.
Las pruebas frontend verifican también respuestas fuera de orden para el mismo
horario en dos semanas y rechazan un listado con fecha distinta de la solicitada.

Las verificaciones documentales, de scripts y espacios se ejecutan con
`python .specify/.codex/hooks/validate.py`,
`python -B -m unittest discover -s .specify/tests -v` y `git diff --check`.

## Evidencia visual propia

Ruta real `/user/schedule`: una matrícula el 2 de noviembre, semana siguiente
vacía, reserva explícita del 9, cancelación de esa reserva y conservación de la
primera. Ruta `/admin/attendance`: Ana solo el 2 y Luis solo el 9, con entrada
futura deshabilitada. Los días son sintéticos; el reloj del navegador se fijó
para reproducir el recorrido.

- [Matrícula en la semana original](evidence/matricula-semana-original.png).
- [Otra semana vacía después de cancelar solo su reserva](evidence/matricula-otra-semana-vacia.png).
- [Asistencia de la fecha original](evidence/asistencia-fecha-original.png).
- [Mismo horario en otra semana con otro cliente](evidence/asistencia-otra-semana.png).
- [Consulta por fecha en móvil claro](evidence/asistencia-fecha-movil.png).
- [Resultados](evidence/browser-results.json) y [script reproducible](evidence/browser-review.cjs).

Escritorio: 1440×1100, oscuro. Móvil: 390×844, claro. Iniciar Vite con
`VITE_AUTH_API_BASE_URL=/api`; se usó el puerto local 5174 porque 5173 ya estaba
ocupado. Ejecutar `GYM_FRONTEND_URL=http://127.0.0.1:5174 node
.specify/base/validaciones/matriculas-sesiones/evidence/browser-review.cjs`.
Playwright está fuera del repositorio; se puede indicar su módulo mediante
`GYM_PLAYWRIGHT_MODULE`. Deno también se instaló fuera del producto.

## Límites

Supabase remoto no se modificó y no se desplegó el producto ni la Edge Function.
La migración 019 queda pendiente de aplicarse en el entorno de la aplicación.
El navegador usa respuestas sintéticas; las reglas y la persistencia se prueban
por separado con backend y PostgreSQL real. No se enviaron correos ni se contactó
con proveedores de pago. Persisten avisos conocidos de Starlette/httpx, Pinia,
rutas sintéticas y antigüedad de Browserslist; no impiden las verificaciones.
El contenedor de pruebas y el Vite local de revisión se detuvieron al terminar.
