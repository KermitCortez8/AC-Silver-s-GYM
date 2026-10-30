# MOD-06 · Asistencias

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Controlar entradas y salidas por clase o gimnasio general con aforo compartido,
auditoría administrativa e historial privado del cliente.

## 2. User Story

**P1.** Como administrador, quiero registrar entradas/salidas y corregir errores
con trazabilidad para controlar el aforo. Como cliente, quiero consultar mis
visitas y calendario sin acceder a datos de otras personas.

Prueba independiente: registrar una visita general de cliente habilitado,
cerrarla, reingresar y consultar su historial desde dos sesiones diferentes.

## 3. Acceptance Criteria

1. **CA-01.** Dado un cliente activado con membresía pagada y vigente, al
   registrar entrada general con DNI y `request_id` válido se usa el reloj del servidor.
2. **CA-02.** Dada una entrada abierta, no se admite otra para el mismo cliente;
   las entradas generales y de clase comparten aforo.
3. **CA-03.** Dado un reintento con el mismo `request_id`, se devuelve la visita
   previa sin duplicarla, incluso si ya se cerró.
4. **CA-04.** Dado un actor `staff`, `trainer` o `user`, al intentar registrar
   asistencia general se rechaza; solo `admin` escribe/corrige/anula.
5. **CA-05.** Dado un cliente autenticado, al consultar historial paginado,
   semana o exportación solo recibe sus datos y no la auditoría interna.
6. **CA-06.** Dada una corrección/anulación, se conserva auditoría y control de
   versión; el resumen utiliza conteos, visitas abiertas y recientes.
7. **CA-07.** Al alcanzar o superar la hora de fin de una clase en Perú, una
   nueva entrada se rechaza con «La hora de esta clase ya pasó. No se puede
   registrar la asistencia.»; la consulta deshabilita la entrada y no se guarda
   asistencia. Una salida pendiente sigue permitida.
8. **CA-08.** La pestaña por horarios reutiliza el calendario semanal del módulo
   de horarios, con agenda móvil, colores por servicio, cupos y filtro por día.
   Seleccionar un bloque muestra solo sus matrículas activas, con cliente, DNI,
   entrada, salida, estado y acciones individuales para la fecha seleccionada.
   Cada sesión consulta sus propios clientes; al cambiar de semana se limpia la
   selección. Las entradas siguen usando el día y reloj actual del servidor de Perú.
9. **CA-09.** La entrada se admite desde el inicio inclusive hasta el fin exclusivo
   de la clase en su día. Fuera del intervalo, se muestra el motivo y se rechaza
   cualquier intento en el servidor sin guardar asistencia. La matrícula debe
   corresponder exactamente a la fecha de entrada; una de otra semana no autoriza.
10. **CA-10.** Pasada más de una hora desde el término original de la clase, una
   visita sin salida figura como incompleta y muestra un aviso. El administrador
   puede guardar la salida real; si es tardía, permanece incompleta. Exactamente
   en el límite de una hora aún puede completarse. Historial y exportación admiten
   el filtro de incompletas sin ampliar el acceso de una sesión de cliente.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_entry_without_enrollment_and_exit_use_server_clock`, `test_entry_requires_current_paid_membership`. |
| CA-02 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_open_entry_blocks_other_kind`, `test_capacity_is_shared_by_general_and_schedule_entries`, `test_stale_parallel_writes_cannot_exceed_capacity`. |
| CA-03 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_retries_do_not_duplicate_even_after_exit`. |
| CA-04 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_only_admin_can_register_general_visit`. |
| CA-05 | [test_scoped_operations.py](../../../backend/tests/test_scoped_operations.py): `test_dni_filter_cannot_override_the_session_client`, `test_history_passes_client_scope_to_persistence_and_hides_audit`. |
| CA-06 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_general_corrections_and_annulment_remain_audited`; [test_remaining_smells.py](../../../backend/tests/test_remaining_smells.py): `test_remote_summary_uses_counts_open_visits_and_eight_recent_records`. |
| CA-07 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_expired_class_rejects_entry_and_explains_why`, `test_expired_class_api_returns_error_without_saving`, `test_transaction_revalidates_class_expiration`, `test_schedule_retry_and_exit_still_work_after_class_end`; [29-view-flows.test.js](../../../frontend/tests/29-view-flows.test.js): error y actualización de ficha tras vencer la clase. |
| CA-08 | [test_schedule_attendance.py](../../../backend/tests/test_schedule_attendance.py): `test_tabla_y_lista_solo_incluyen_matriculas_activas_del_horario`, permisos y recorrido HTTP; [29-view-flows.test.js](../../../frontend/tests/29-view-flows.test.js): calendario compartido, cupos, filtro, selección, bloqueo al guardar y descarte de respuestas obsoletas. |
| CA-09 | [test_schedule_attendance.py](../../../backend/tests/test_schedule_attendance.py): `test_lista_informa_si_la_entrada_esta_dentro_del_horario`; [test_attendance_deadline_postgres.py](../../../backend/tests/test_attendance_deadline_postgres.py): `test_rpc_rechaza_clase_terminada_sin_guardar`. |
| CA-10 | [test_schedule_attendance.py](../../../backend/tests/test_schedule_attendance.py): límites, cambio de día, historial privado, persistencia y cambio de horario; [test_attendance_deadline_postgres.py](../../../backend/tests/test_attendance_deadline_postgres.py): RPC, auditoría, límite inclusivo y migración repetible. |

## 4. Technical Constraints

- API: [attendance_routes.py](../../../backend/presentation/routes/attendance_routes.py),
  bajo `/api/asistencia`: entrada, general/entrada, salida, historial, resumen,
  cliente, mi-semana, exportar, corrección y anulación.
  Solo `admin` consulta `/horarios` y `/horarios/{id}/clientes` para controlar asistencia.
  Este último acepta `fecha=AAAA-MM-DD`, con validación civil; devuelve solo las
  matrículas de esa sesión. Sin parámetro consulta el día actual.
- Aplicación: [attendance_service.py](../../../backend/application/services/attendance_service.py),
  reloj `America/Lima`; reglas y repositorios de asistencia especializados.
- SQL: `005_harden_attendance.sql`, después `013_general_attendance.sql` y
  [018_attendance_schedule_exit_deadline.sql](../../../backend/migrations/018_attendance_schedule_exit_deadline.sql).
  [019_schedule_sessions.sql](../../../backend/migrations/019_schedule_sessions.sql)
  agrega la reserva por fecha y revalida esa fecha dentro de `guardar_asistencia`.
  Se reutiliza `ASISTENCIA`; visita general lleva `servicio='gimnasio'` y
  matrícula/horario nulos. No hay tabla separada de visitas generales.
  `limite_salida` conserva fecha/hora de fin más una hora en cada nueva visita de clase;
  `salida_tardia` se calcula en la RPC y se conserva al recargar.
- UI: `/admin/attendance` y `/user/attendance`,
  [AttendanceView.vue](../../../frontend/src/presentation/views/AttendanceView.vue),
  [UserAttendanceView.vue](../../../frontend/src/presentation/views/UserAttendanceView.vue).
  Pestañas por horario, gimnasio general e historial; componentes y composables propios.
  Por horario utiliza [AttendanceScheduleRoster.vue](../../../frontend/src/presentation/components/attendance/AttendanceScheduleRoster.vue)
  con [ExcelScheduleGrid.vue](../../../frontend/src/presentation/components/ExcelScheduleGrid.vue)
  y [useScheduleRoster.js](../../../frontend/src/presentation/composables/attendance/useScheduleRoster.js).
  El registro general mantiene la búsqueda por DNI.

## 5. Guardrails

No usar el reloj del navegador como autoridad de entrada. No equiparar permisos
de `staff` con `admin`. No confundir resumen especializado con carga de todo el
historial. No publicar auditoría al cliente ni mezclar fechas de clases semanales.

## 6. Edge Cases

- Entrada de clase fuera del día o intervalo del horario: rechazar; en su día
  se admite desde inicio inclusive hasta fin exclusivo.
- El límite es la hora de fin; antes del inicio se informa cuándo se habilita.
  Una clase terminada sin entrada queda sin registro; no se crea una visita
  ni se persiste una inasistencia automática. Las horas enviadas por el navegador
  no permiten registrar una nueva entrada fuera del intervalo.
- Reingreso general el mismo día tras cerrar: permitir con nueva identidad de solicitud.
- Salida pendiente de un día anterior: continúa contando como visita abierta.
- Una incompleta sin salida continúa consumiendo aforo hasta registrar la salida
  real; el vencimiento no inventa una salida. Su estado se calcula al consultar,
  sin depender de un cron ni de que una pantalla permanezca abierta.
- El plazo usa el horario guardado al entrar y puede cruzar medianoche. Editar
  o desactivar la clase no cambia el límite de visitas ya registradas.
- La migración 018 asigna un límite a visitas de clase abiertas usando el horario
  existente al migrar. Las visitas cerradas históricas conservan su clasificación.
- Actualización concurrente con versión antigua: informar conflicto sin sobrescribir.
- Rango de historial invertido, página inválida o tamaño mayor de 100: rechazar.
- Búsqueda reemplazada o vista desmontada: descartar respuesta obsoleta.
- Mismo horario en otra semana: filtrar por `fecha_clase`, tanto en el listado
  administrativo como en `mi-semana`. Una respuesta de otra fecha se descarta en
  el frontend; un fallo de carga no muestra los clientes de la selección anterior.

## 7. Definition of Done

Verificar privacidad, aforo, reintentos, auditoría, reloj y paginación afectados.
Para cambios de UI, reutilizar [29-view-flows.test.js](../../../frontend/tests/29-view-flows.test.js)
y registrar revisión visual. Cumplir el [DoD](../../docs/DoD.md).

### Vigencia compartida (feature 001)

La selección de membresía en asistencia reutiliza membership_current, igual que
autenticación: exige pago confirmado y fechas civiles válidas con día final inclusivo.
Fechas ausentes o imposibles no autorizan entradas ni consumen aforo.
Regresiones y recorrido integrado en
[test_client_flow_control.py](../../../backend/tests/test_client_flow_control.py).

Verificación del aviso de clase terminada y sus límites en
[validation.md](../validaciones/asistencias/validation.md).
