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

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_entry_without_enrollment_and_exit_use_server_clock`, `test_entry_requires_current_paid_membership`. |
| CA-02 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_open_entry_blocks_other_kind`, `test_capacity_is_shared_by_general_and_schedule_entries`, `test_stale_parallel_writes_cannot_exceed_capacity`. |
| CA-03 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_retries_do_not_duplicate_even_after_exit`. |
| CA-04 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_only_admin_can_register_general_visit`. |
| CA-05 | [test_scoped_operations.py](../../../backend/tests/test_scoped_operations.py): `test_dni_filter_cannot_override_the_session_client`, `test_history_passes_client_scope_to_persistence_and_hides_audit`. |
| CA-06 | [test_general_attendance.py](../../../backend/tests/test_general_attendance.py): `test_general_corrections_and_annulment_remain_audited`; [test_remaining_smells.py](../../../backend/tests/test_remaining_smells.py): `test_remote_summary_uses_counts_open_visits_and_eight_recent_records`. |

## 4. Technical Constraints

- API: [attendance_routes.py](../../../backend/presentation/routes/attendance_routes.py),
  bajo `/api/asistencia`: entrada, general/entrada, salida, historial, resumen,
  cliente, mi-semana, exportar, corrección y anulación.
- Aplicación: [attendance_service.py](../../../backend/application/services/attendance_service.py),
  reloj `America/Lima`; reglas y repositorios de asistencia especializados.
- SQL: `005_harden_attendance.sql`, después `013_general_attendance.sql`.
  Se reutiliza `ASISTENCIA`; visita general lleva `servicio='gimnasio'` y
  matrícula/horario nulos. No hay tabla separada de visitas generales.
- UI: `/admin/attendance` y `/user/attendance`,
  [AttendanceView.vue](../../../frontend/src/presentation/views/AttendanceView.vue),
  [UserAttendanceView.vue](../../../frontend/src/presentation/views/UserAttendanceView.vue).
  Pestañas por horario, gimnasio general e historial; componentes y composables propios.

## 5. Guardrails

No usar el reloj del navegador como autoridad de entrada. No equiparar permisos
de `staff` con `admin`. No confundir resumen especializado con carga de todo el
historial. No publicar auditoría al cliente ni mezclar fechas de clases semanales.

## 6. Edge Cases

- Entrada de clase fuera del día o intervalo del horario: rechazar; en su día
  se admite desde inicio inclusive hasta fin exclusivo.
- Reingreso general el mismo día tras cerrar: permitir con nueva identidad de solicitud.
- Salida pendiente de un día anterior: continúa contando como visita abierta.
- Actualización concurrente con versión antigua: informar conflicto sin sobrescribir.
- Rango de historial invertido, página inválida o tamaño mayor de 100: rechazar.
- Búsqueda reemplazada o vista desmontada: descartar respuesta obsoleta.

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
