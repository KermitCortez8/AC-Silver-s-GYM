# Prueba de matrícula, asistencia administrativa y salida omitida

Fecha: 2026-11-09. No cambia las reglas de asistencia.

## Recorrido en la aplicación conectada

El cliente de la captura anterior ya estaba eliminado. El usuario seleccionó
expresamente la cuenta de prueba usada para membresías. Se verificaron identidad,
activación y membresía pagada vigente antes de crear un horario de prueba propio
con un cupo, sin editar horarios existentes.

- Cliente de prueba `SGCLI095`; sesión de cardio del 2026-11-09, 14:29–15:29,
  horario 24 y matrícula 45. La matrícula se realizó por HTTP autenticado tras
  iniciar sesión con la contraseña del cliente, usando su identidad de sesión.
- Entrada 17 a las 14:31:52. Se invocó el servicio de aplicación de asistencia
  con la cuenta administrativa activa resuelta de la base. No se usó inicio de
  sesión de administrador en navegador ni se fabricó un token administrativo.
- Reintentar la entrada devolvió el mismo registro. Otra entrada general fue
  rechazada por tener una visita sin salida.
- El navegador consultó el portal real del cliente: horario, entrada, salida
  vacía e historial coincidentes con la base. La API denegó registrar asistencia
  como cliente con 403 y no incluyó auditoría interna en su historial.
- Se conserva abierta la visita para revisión del usuario. Su plazo real es
  el 2026-11-09 a las **16:29, America/Lima**. No se alteraron fechas ni plazos
  remotos para fingir que ya había vencido. Las capturas y sesiones reales
  permanecen fuera del repositorio; no se guardan contraseñas ni tokens aquí.

## Comprobación acelerada y reproducible

[test_attendance_enrollment_flow_postgres.py](../../../../backend/tests/asistencias/postgres/test_attendance_enrollment_flow_postgres.py)
usa únicamente un PostgreSQL desechable con datos sintéticos. Instala las
migraciones de matrícula, sesiones y asistencia de clase, crea cuenta habilitada
y membresía vigente, matricula mediante RPC y registra la entrada administrativa
mediante `guardar_asistencia`, las mismas operaciones de persistencia del producto.

Comprueba primero que el límite guardado es fin de clase más una hora y que el
instante exacto todavía admite completar la visita. Solo en esa base se reduce
el plazo a dos segundos para ejecutar dos variantes:

- Reconciliación mediante RPC privada, sin requerir extensiones.
- Programación real de 022 cada diez segundos con pg_cron, sin consultas de
  aplicación que materialicen el estado; repetir la programación deja un trabajo.

En ambas, la visita queda `incompleta`, con salida/fecha de salida vacías, versión
1 y un único evento de Sistema. Sigue consumiendo aforo, bloquea otra visita y no
se duplica al reintentar la entrada. Una salida tardía posterior guarda hora real,
versión 2 y estado incompleto; libera aforo y tolera reintentos sin sobrescribirla.
Se comprobó también la proyección del registro remoto en el límite y un segundo
después mediante un reloj de lectura simulado, sin escribir en la base externa.

## Alcance y límites

Este recorrido verifica clases. No certifica la instalación del cron en Supabase
ni el cierre automático de visitas generales a las tres horas. La migración 023
del repositorio está vacía en la referencia consultada; no se usa como evidencia
para ese otro flujo. La base externa sí dispone de las columnas requeridas por
el backend actual. No se cambiaron migraciones, permisos, pagos o notificaciones.
No se enviaron correos como parte de esta prueba.

El nuevo módulo está incluido en el job SQL de PR. En PostgreSQL sin pg_cron
se omite explícitamente solo la variante cron; la variante RPC sigue verificando
el recorrido. Para comprobar cron localmente se usó PostgreSQL 16 con pg_cron,
sin puertos publicados y con red deshabilitada al arrancar el contenedor.

## Resultados

- Asistencia general/por horario, matrículas y sesiones en backend: **79 aprobadas**.
- PostgreSQL con pg_cron: **15 aprobadas** entre límites de clase, sesiones y el
  nuevo recorrido completo en sus dos variantes. Se comprobó la ejecución del
  trabajo automático, no solo la llamada directa a su función.
- PostgreSQL Alpine sin pg_cron, como en CI: **1 aprobada y 1 omitida** en el
  módulo nuevo; el recorrido RPC se ejecuta y solo se omite la variante cron.
- Flake8 crítico: **0 errores**. Validador documental: **90 archivos y 14 contratos**.
- Pruebas del flujo documental: **13 aprobadas**. `git diff --check`: correcto.
- Chromium con sesión y API reales: matrícula, consulta del horario e historial,
  salida pendiente, auditoría privada y rechazo de escritura del cliente correctos.
