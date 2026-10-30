# Contexto del cambio

Fecha: 2026-10-29. El generador prepara este documento;
Codex completa el análisis antes de planificar. No acredita ejecución de pruebas.

## Base obligatoria

- [AGENTS.md](../../../AGENTS.md).
- [Constitución](../../memory/constitution.md).
- [Base implementada](../../specs/000-base-implementada/spec.md).
- [Índice de módulos](../../base/modulos/README.md).
- [Arquitectura](../../docs/arquitectura.md).
- [Diseño](../../docs/diseno.md).
- [Seguridad](../../.codex/rules/seguridad.md).
- [DoD](../../docs/DoD.md).
- [Reglas por rutas](../../.codex/rules/README.md).

## Módulos afectados

- **MOD-01**: [Identidad](../../base/modulos/01-identidad-acceso.md).
- **MOD-02**: [Clientes](../../base/modulos/02-clientes.md).
- **MOD-03**: [Membresías](../../base/modulos/03-membresias-pagos.md).
- **MOD-05**: [Horarios](../../base/modulos/05-horarios-matriculas.md).
- **MOD-06**: [Asistencias](../../base/modulos/06-asistencias.md).

## Código y pruebas existentes

- [Clientes](../../../backend/application/services/clients_service.py): alta, reintentos y borrado.
- [Reglas de membresía](../../../backend/domain/services/memberships_rules.py): pago, edición y activación.
- [Horarios](../../../backend/domain/services/schedules_rules.py): validación y cupos.
- [Asistencia](../../../backend/application/services/attendance_service.py): entrada y vigencia.
- [Ciclo compartido](../../../backend/domain/services/membership_lifecycle.py): fechas y estados.
- [Rutas](../../../backend/presentation/routes/clients_routes.py) y [errores](../../../backend/presentation/error_handlers.py).
- [Registro/pagos](../../../backend/tests/test_admin_client_payment.py),
  [vigencia](../../../backend/tests/test_membership_expiration.py),
  [matrículas](../../../backend/tests/test_schedule_enrollment.py),
  [asistencia](../../../backend/tests/test_general_attendance.py),
  [matriz HTTP](../../../backend/tests/test_module_error_control.py).

## Restricciones que se deben contrastar

Permisos admin/staff en clientes y solo admin al escribir asistencia; identidad desde sesión.
Conservar importe guardado y pago separado de activación. Cuatro capas y comandos
existentes; sin nueva persistencia ni cambios SQL. Regla temporal compartida America/Lima.
Pruebas locales sin proveedores. Reglas api, datos, frontend, automatización y comunes leídas.

## Evaluación específica del cambio

El borrado captura toda excepción y comunica éxito falso. La edición genérica de membresía
reemplaza el registro e importe, permitiendo perder pago y transferir identidad.
La confirmación cambia cero por catálogo; la asistencia compara textos de fechas;
el parser de horarios acepta coincidencias parciales y el día solo exige texto no vacío.
Reutilizar http_error, membership_current, validadores y repositorios actuales.
Verificar primero regresiones, luego backend completo, frontend, build y hooks SDD.
La corrección en frontend requiere evidencia visual en navegador con API simulada.

## Revisión adicional de frontend

[PaymentView](../../../frontend/src/presentation/views/PaymentView.vue) mantiene el título
Confirmando al fallar y no permite reintento. [Acciones de clientes](../../../frontend/src/presentation/composables/clients/useClientMembershipActions.js)
no bloquea dobles confirmaciones manuales y no actualiza viewingClient al activar.
Reutilizar useClientPayments y el mismo diálogo. Pruebas de composables, SSR y navegador
con transportes simulados; no se contactan proveedores reales.
