# MOD-05 · Horarios y matrículas

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Programar clases y permitir matrículas respetando cupos, identidad del cliente
y condiciones del horario y membresía.

## 2. User Story

**P1.** Como cliente con acceso habilitado, quiero matricularme en un horario
disponible y consultar/cancelar mis propias matrículas. Como personal autorizado,
quiero administrar horarios y matrículas sin sobrepasar sus cupos.

Prueba independiente: crear un horario con cupo limitado, matricular clientes
sintéticos, comprobar ocupación y cancelar una matrícula propia.

## 3. Acceptance Criteria

1. **CA-01.** Dado un horario activo, al consultar su catálogo se muestran sus
   datos de clase y cupos disponibles.
2. **CA-02.** Dado un cliente habilitado y un cupo disponible, al matricularlo
   se refleja en su horario; sin cupo o con matrícula duplicada se rechaza.
3. **CA-03.** Dado un cliente autenticado, al enviar otro `id_cliente` en el
   autoservicio se utiliza su identidad de sesión.
4. **CA-04.** Dada una matrícula ajena, al intentar cancelarla como cliente se
   deniega; una cancelación propia libera su plaza.
5. **CA-05.** Dada una persistencia sin RPC de matrícula, al guardar se informa
   fallo y no se realiza un INSERT sin locks.
6. **CA-06.** En el portal del cliente, al abrir o volver a una pestaña visible
   se consultan sus matrículas; mientras permanezca visible se actualizan cada
   30 segundos. El panel vuelve a consultar al navegar hacia él, sin reutilizar una
   respuesta anterior a un cambio de matrícula. Una lectura iniciada antes de
   guardar/cancelar no puede sobrescribir ese cambio confirmado.
7. **CA-07.** Cada matrícula reserva una sola `fecha_clase`. La programación se
   repite semanalmente, pero sus clientes y cupos no se trasladan a otra fecha.
   El mismo cliente puede reservar otras sesiones del mismo horario; el duplicado
   y el límite de cupos se comprueban por horario y fecha dentro de la transacción.
8. **CA-08.** Cancelar una matrícula libera solo su sesión. Se rechazan fechas
   imposibles, pasadas, de otro día de semana o fuera de la vigencia de membresía.
   Una reserva de una semana no impide reservar la siguiente.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_schedule_enrollment.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_schedule_catalog_includes_exercise_and_available_slots`. |
| CA-02 | [test_schedule_enrollment.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_enrollment_moves_class_to_client_schedule_and_respects_capacity`. |
| CA-03 | [test_schedule_enrollment.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_user_routes_always_use_client_from_authenticated_session`. |
| CA-04 | [test_schedule_enrollment.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_client_can_only_cancel_own_enrollment`. |
| CA-05 | [test_schedule_enrollment.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_enrollment.py): `test_enrollment_requires_atomic_rpc_before_writing`; [test_enrollment_errors.py](../../../backend/tests/horarios_matriculas/integracion/test_enrollment_errors.py). |
| CA-06 | [module-error-control.test.js](../../../frontend/tests/transversales/integracion/module-error-control.test.js): respuestas anteriores a guardar/cancelar y lecturas fuera de orden; [revisión del portal](../validaciones/horarios-cliente/validation.md): foco, intervalo, navegación y conservación ante errores. |
| CA-07 | [test_schedule_sessions.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_sessions.py), [test_schedule_sessions_postgres.py](../../../backend/tests/horarios_matriculas/postgres/test_schedule_sessions_postgres.py), [schedule-calendar.test.js](../../../frontend/tests/horarios_matriculas/unitarias/schedule-calendar.test.js). |
| CA-08 | Las mismas regresiones y el [recorrido visual por sesiones](../validaciones/matriculas-sesiones/validation.md). |

## 4. Technical Constraints

- API: [gym_routes.py](../../../backend/presentation/routes/gym_routes.py),
  `/api/gym/horarios-publicos`, `/horarios-servicio` y `/matriculas` bajo `/api/gym`.
- `GET /api/gym/matriculas/cliente?dni=…` busca un DNI exacto para `admin` o
  `staff` y devuelve solo ID, nombre y DNI. El selector usa `GET /matriculas`
  con `incluir_asistencias=false`. La API conserva la respuesta con asistencia
  por defecto y mantiene el alcance de la sesión del cliente.
- `GET` y `PUT /api/gym/horarios-servicio/configuracion` requieren `admin` o
  `staff`. El cuerpo contiene `hora_inicio` (HH:MM de Lima),
  `duracion_minutos` (60 o 120) y `cupos` (entero positivo).
- Reglas: [schedules_rules.py](../../../backend/domain/services/schedules_rules.py).
  Datos `HORARIOS_SERVICIO`, `MATRICULAS_HORARIO`, clientes, membresías y catálogo.
- Repositorio especializado:
  [schedule_enrollment_repository.py](../../../backend/infrastructure/repositories/schedule_enrollment_repository.py).
  Dependencias SQL en `002_harden_schedule_enrollment.sql`, `006_schedule_email_notifications.sql`
  y [019_schedule_sessions.sql](../../../backend/migrations/019_schedule_sessions.sql).
  Las altas envían `fecha_clase`; un cliente antiguo sin fecha reserva únicamente
  la siguiente sesión del día configurado. El catálogo incluye `ocupacion_por_fecha`.
- UI: [ServiceSchedulesView.vue](../../../frontend/src/presentation/views/ServiceSchedulesView.vue),
  [EnrollmentView.vue](../../../frontend/src/presentation/views/EnrollmentView.vue),
  `/admin/service-schedules`, `/admin/enrollment`, `/user/schedule`.
- Calendarios/fechas: [scheduleCalendar.js](../../../frontend/src/domain/utils/scheduleCalendar.js)
  y [scheduleEnrollment.js](../../../frontend/src/domain/utils/scheduleEnrollment.js).

## 5. Guardrails

No permitir cancelaciones ajenas ni confiar en el DNI enviado como identidad de
autoservicio. No reducir cupos por debajo de matrículas activas ni eliminar un
horario con matrículas activas. No sustituir la RPC por escrituras parciales.
No confundir una recurrencia semanal con una asistencia de otra fecha.
El día del horario no se puede cambiar mientras tenga sesiones pendientes;
reducir cupos valida la mayor ocupación de sus sesiones futuras, sin sumarlas.

## 6. Edge Cases

- Horario inactivo, cliente sin membresía admitida, duplicado o aforo lleno:
  rechazar conforme a la regla y conservar el significado del error HTTP.
- Calendario, agenda, lista semanal y exportación abarcan el lunes a domingo
  completo, aunque haya fechas de otro mes o año. El selector de mes muestra
  cada semana que toca ese mes. Se usa la fecha de Perú en calendario y correo.
- Matrículas históricas: asignar una sola fecha desde `fecha_matricula` y el día
  configurado, nunca desde el día de despliegue. Sin fecha fiable, no autorizar
  entrada ni trasladar el cliente a una semana nueva. Las visitas guardadas se conservan.
- Correo fallido tras matrícula confirmada: conservar matrícula y aviso pendiente.
  La confirmación se guarda en la cola transaccional y su envío se intenta
  en segundo plano después de responder al navegador.
- Eliminación de cliente: liberar capacidad junto con sus dependencias; ver MOD-02.
- La actualización automática se detiene al ocultar o desmontar la vista y no
  interrumpe una operación de matrícula ni el selector abierto. Si falla una consulta,
  se conserva el último horario válido y se muestra el error existente.

## 7. Definition of Done

Verificar cupos, identidad, cancelación, errores de almacenamiento y calendario
con [test_schedule_calendar.py](../../../backend/tests/notificaciones/integracion/test_schedule_calendar.py),
[schedule-enrollment.test.js](../../../frontend/tests/horarios_matriculas/unitarias/schedule-enrollment.test.js)
y [schedule-calendar.test.js](../../../frontend/tests/horarios_matriculas/unitarias/schedule-calendar.test.js)
según el cambio. Cumplir el [DoD](../../docs/DoD.md).

### Validación de horarios (feature 001)

Al guardar se exige un día de lunes a domingo y una hora completa; se rechaza texto
sobrante, AM/PM fuera de 1–12 y segundos no cero. Las horas admitidas se guardan
como HH:MM de 24 horas para su uso por asistencia. Se mantiene lectura de AM/PM
histórico y duración de 60 o 120 minutos.
Regresiones y recorrido de cupos/cancelación en
[test_client_flow_control.py](../../../backend/tests/transversales/integracion/test_client_flow_control.py).

### Límites de formularios

El código editable del día y la búsqueda general admiten hasta 50 caracteres.
La entrada adicional se bloquea sin avisos ni contadores de longitud. Horas,
fechas, cupos y opciones del catálogo conservan su validación específica.

Evidencia: [validación de límites](../validaciones/limites-formularios/validation.md).

### Configuración y parámetros

En Horarios por servicio, la tabla guarda los valores iniciales compartidos de
hora de inicio, duración y cupos. La atención es de lunes a viernes de 06:00 a
22:00, y sábado y domingo de 07:00 a 18:00, en hora de Lima. Las clases nuevas o
editadas deben empezar y terminar dentro de la franja de su día. El formulario
**Nuevo horario** adapta la hora inicial al día elegido manteniendo la duración.
El valor compartido de inicio y duración debe caber en una jornada de lunes a
viernes.

La vista consulta primero el catálogo de horarios. El editor abre de inmediato
y consulta las rutinas y los parámetros que necesita. Si llegan parámetros
mientras el usuario edita, solo completan los valores iniciales que todavía no
haya modificado. Ante una hora fuera de atención, el editor muestra la franja
del día y el intervalo solicitado, conserva el formulario y evita el envío.

Matrículas carga el catálogo al entrar. En el panel interno, la búsqueda añade
una consulta por DNI y otra para las matrículas de ese cliente. «Mis horarios»
carga el catálogo y las matrículas de la sesión. Su propia actualización de foco
y visibilidad se suspende mientras el selector está abierto. En escritorio,
seleccionar otra clase actualiza el resaltado sin reconstruir la cuadrícula.
Los avisos de Matrículas y «Mis horarios» se superponen al calendario y se
pueden cerrar. Dentro del selector, los avisos de alta, cancelación, error o
exportación aparecen sobre el modal activo.

La [migración 028](../../../backend/migrations/028_parametros_horarios.sql)
añade los parámetros a `CONFIGURACION_GIMNASIO` y crea la tabla si falta.
Se aplica en el esquema del gimnasio con `commit_gym_transaction` ya instalada
y se puede reejecutar. Los valores iniciales son 06:00, 60 minutos y 10 cupos.
Si la tabla se acaba de crear, el primer guardado conserva los valores de
aforo predeterminados de 30 personas en total y 10 por hora. Si se revierte el
código, se pueden conservar la tabla y sus datos para un despliegue posterior.

Evidencia en [test_schedule_settings.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_settings.py).
Persistencia y permisos en [test_atomic_transactions_postgres.py](../../../backend/tests/transversales/postgres/test_atomic_transactions_postgres.py).
Editor y errores en [editor-horario.test.js](../../../frontend/tests/horarios_matriculas/interfaz/editor-horario.test.js).

### Retiro de horarios fuera de atención

La [migración 029](../../../backend/migrations/029_horario_atencion.sql) se aplica
después de `019_schedule_sessions.sql` y de instalar `commit_gym_transaction`
y `gym_identity_counters`. Elimina de `HORARIOS_SERVICIO` las filas fuera de
la franja que carecen de matrículas y asistencias, y mantiene inactivas las filas
vinculadas. Ante referencias adicionales declaradas por el esquema, usa la
desactivación. El catálogo omite los horarios retirados y el historial conserva
sus referencias. El respaldo previo de `HORARIOS_SERVICIO` permite recuperar
filas eliminadas si se revierte el cambio. La migración es transaccional y
repetible. Se verifica en
[test_schedule_sessions_postgres.py](../../../backend/tests/horarios_matriculas/postgres/test_schedule_sessions_postgres.py).

### Sala de cada clase

El editor exige elegir una sala del listado fijo al crear un horario o
completar uno pendiente. La sala se guarda con el horario semanal y se muestra
en el calendario, la selección de clases para matrícula y la exportación.
La lista ofrece `Sala de Fuerza 1`, `Sala de Fuerza 2` y `Sala de cardio`.
En la lista administrativa, los horarios previos sin sala figuran como
**Por asignar**. Una actualización de la API que omite la sala conserva la que
ya está asignada. Si su nombre quedó fuera del listado, el editor abre con
la selección vacía para que el personal elija la sala correspondiente.

La [migración 030](../../../backend/migrations/030_sala_horario_servicio.sql)
añade `sala` a `HORARIOS_SERVICIO` en el esquema con el RPC
`commit_gym_transaction` instalado. Se puede ejecutar de nuevo y la columna
se puede conservar si se revierte la versión de la aplicación. La API devuelve
`sala` en horarios públicos, horarios por servicio y matrículas. Se verifica
en [test_schedule_rooms.py](../../../backend/tests/horarios_matriculas/integracion/test_schedule_rooms.py).
