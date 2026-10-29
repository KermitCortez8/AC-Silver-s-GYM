# MOD-10 · Paneles, configuración y coordinación

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Presentar resúmenes adecuados a cada rol y coordinar la carga de recursos del
frontend sin mezclar sesiones ni bloquear módulos por consultas ajenas.

## 2. User Story

**P1.** Como personal autorizado, quiero consultar indicadores y configurar el
aforo para operar el gimnasio. Como cliente o entrenador, quiero entrar a mi
panel y ver la información correspondiente a mi cuenta.

Prueba independiente: consultar indicadores con datos sintéticos de pagos y
vigencias y navegar entre secciones mientras una carga ajena permanece pendiente.

## 3. Acceptance Criteria

1. **CA-01.** Dado un resumen con membresías de distintos estados, solo se
   cuentan como activas las pagadas y vigentes; el panel distingue pendientes,
   activables y vencidas.
2. **CA-02.** Dadas fechas cerca del cambio de día UTC, el cálculo del panel
   usa el día de Perú, incluida la serie de siete días.
3. **CA-03.** Dada una consulta de una sección, se cargan sus recursos declarados
   sin refrescar indiscriminadamente todos los historiales.
4. **CA-04.** Dado un cambio de sesión o instancia de aplicación, los servicios
   y respuestas de una instancia no publican datos en otra sesión.
5. **CA-05.** Dada navegación dentro del panel, el indicador de módulo no espera
   indefinidamente una consulta pendiente de otra sección.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_review_regressions.py](../../../backend/tests/test_review_regressions.py): `test_summary_counts_only_paid_current_memberships_with_canonical_and_legacy_states`; [20-client-dashboard.test.js](../../../frontend/tests/20-client-dashboard.test.js). |
| CA-02 | [20-client-dashboard.test.js](../../../frontend/tests/20-client-dashboard.test.js). |
| CA-03 | [test_supabase_refresh.py](../../../backend/tests/test_supabase_refresh.py): `test_sections_load_only_needed_tables_and_preserve_other_sections`, `test_health_check_does_not_refresh_admin_histories`; [27-scoped-gym-modules.test.js](../../../frontend/tests/27-scoped-gym-modules.test.js). |
| CA-04 | [28-application-context.test.js](../../../frontend/tests/28-application-context.test.js) y [15-sync-resources.test.js](../../../frontend/tests/15-sync-resources.test.js). |
| CA-05 | [21-module-navigation.test.js](../../../frontend/tests/21-module-navigation.test.js). |

## 4. Technical Constraints

- API: [gym_routes.py](../../../backend/presentation/routes/gym_routes.py),
  `/api/gym/summary`, `/configuracion`, `/tickets` y `/horarios` bajo `/api/gym`.
  Resumen/configuración/tickets/horarios internos usan `admin/staff`.
- Reglas: [dashboard_rules.py](../../../backend/domain/services/dashboard_rules.py)
  y [schedules_rules.py](../../../backend/domain/services/schedules_rules.py).
  La configuración se mapea a `CONFIGURACION_GIMNASIO`.
- El resumen incluye clientes, membresías, asistencias del día, stock bajo,
  pedidos pagados pendientes, ventas y próximos vencimientos. El campo
  `aforo_dia` del resumen usa asistencias del día/capacidad: no equivale a las
  personas dentro que calcula el resumen especializado de asistencia.
- UI: [HomeView.vue](../../../frontend/src/presentation/views/HomeView.vue), paneles
  por rol y [TrainerOverviewView.vue](../../../frontend/src/presentation/views/TrainerOverviewView.vue).
- Coordinación: [gymModules.js](../../../frontend/src/application/services/gymModules.js),
  [moduleNavigation.js](../../../frontend/src/application/services/moduleNavigation.js),
  [bootstrap.js](../../../frontend/src/bootstrap.js), cachés y generación de sesión.

## 5. Guardrails

No sumar ventas impagas/canceladas como cobros válidos. No interpretar todos los
indicadores de aforo como ocupación instantánea. No convertir `/api/health` en
una carga de historiales. No introducir acceso HTTP/storage directamente en vistas.

## 6. Edge Cases

- Datos sin origen o estado de pago: mantener categoría desconocida sin inventar confirmación.
- Fallo parcial de refresco: conservar estado previo coherente y permitir reintento.
- Respuesta de sesión anterior: descartarla antes de publicar datos.
- Backend sin credenciales Supabase: health puede devolver 503; `/` solo acredita
  el proceso HTTP activo.
- Tickets y horarios históricos: existen operaciones de consulta/guardado,
  pero este inventario no acredita un módulo visual completo ni un SLA de atención.

## 7. Definition of Done

Verificar indicadores y cargas afectadas, aislamiento por sesión y permisos.
Para cambios de panel, revisar ambos temas y adaptación móvil. Actualizar este
contrato y cumplir el [DoD](../../docs/DoD.md).
