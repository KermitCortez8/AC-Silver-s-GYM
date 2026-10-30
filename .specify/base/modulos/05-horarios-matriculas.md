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

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_schedule_enrollment.py](../../../backend/tests/test_schedule_enrollment.py): `test_schedule_catalog_includes_exercise_and_available_slots`. |
| CA-02 | [test_schedule_enrollment.py](../../../backend/tests/test_schedule_enrollment.py): `test_enrollment_moves_class_to_client_schedule_and_respects_capacity`. |
| CA-03 | [test_schedule_enrollment.py](../../../backend/tests/test_schedule_enrollment.py): `test_user_routes_always_use_client_from_authenticated_session`. |
| CA-04 | [test_schedule_enrollment.py](../../../backend/tests/test_schedule_enrollment.py): `test_client_can_only_cancel_own_enrollment`. |
| CA-05 | [test_schedule_enrollment.py](../../../backend/tests/test_schedule_enrollment.py): `test_enrollment_requires_atomic_rpc_before_writing`; [test_enrollment_errors.py](../../../backend/tests/test_enrollment_errors.py). |

## 4. Technical Constraints

- API: [gym_routes.py](../../../backend/presentation/routes/gym_routes.py),
  `/api/gym/horarios-publicos`, `/horarios-servicio` y `/matriculas` bajo `/api/gym`.
- Reglas: [schedules_rules.py](../../../backend/domain/services/schedules_rules.py).
  Datos `HORARIOS_SERVICIO`, `MATRICULAS_HORARIO`, clientes, membresías y catálogo.
- Repositorio especializado:
  [schedule_enrollment_repository.py](../../../backend/infrastructure/repositories/schedule_enrollment_repository.py).
  Dependencias SQL en `002_harden_schedule_enrollment.sql` y `006_schedule_email_notifications.sql`.
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

## 6. Edge Cases

- Horario inactivo, cliente sin membresía admitida, duplicado o aforo lleno:
  rechazar conforme a la regla y conservar el significado del error HTTP.
- Cruce de semana, mes o fecha UTC: representar la fecha de Perú en calendario y correo.
- Correo fallido tras matrícula confirmada: conservar matrícula y aviso pendiente.
- Eliminación de cliente: liberar capacidad junto con sus dependencias; ver MOD-02.

## 7. Definition of Done

Verificar cupos, identidad, cancelación, errores de almacenamiento y calendario
con [test_schedule_calendar.py](../../../backend/tests/test_schedule_calendar.py),
[11-schedule-enrollment.test.js](../../../frontend/tests/11-schedule-enrollment.test.js)
y [13-schedule-calendar.test.js](../../../frontend/tests/13-schedule-calendar.test.js)
según el cambio. Cumplir el [DoD](../../docs/DoD.md).

### Validación de horarios (feature 001)

Al guardar se exige un día de lunes a domingo y una hora completa; se rechaza texto
sobrante, AM/PM fuera de 1–12 y segundos no cero. Las horas admitidas se guardan
como HH:MM de 24 horas para su uso por asistencia. Se mantiene lectura de AM/PM
histórico y duración de 60 o 120 minutos.
Regresiones y recorrido de cupos/cancelación en
[test_client_flow_control.py](../../../backend/tests/test_client_flow_control.py).
