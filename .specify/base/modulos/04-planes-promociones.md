# MOD-04 · Planes y promociones

Estado: implementado según código y pruebas de referencia. Contrato vivo.

## 1. Sprint Goal

Publicar la oferta de planes y promociones y aplicar descuentos válidos con sus
restricciones de fechas, planes y cupos.

## 2. User Story

**P1.** Como visitante o cliente, quiero consultar planes y promociones vigentes
para elegir mi inscripción. Como administrador, quiero configurar promociones;
como personal autorizado, quiero mantener los planes sin alterar compras anteriores.

Prueba independiente: crear oferta sintética, consultar su visibilidad pública
y registrar inscripciones hasta agotar el límite promocional.

## 3. Acceptance Criteria

1. **CA-01.** Dada una promoción vigente aplicable, al consultarla por el flujo
   público se publica/aplica según las reglas actuales de vigencia y plan.
2. **CA-02.** Dada una promoción con límite, al agotarlo no se concede otro cupo.
3. **CA-03.** Dadas promociones incompatibles por solapamiento, al guardarlas
   se rechaza el conflicto contemplado por las reglas.
4. **CA-04.** Dado un registro administrativo sin promoción seleccionada, al
   cobrar no se aplica otra automáticamente; una inválida impide el alta.
5. **CA-05.** Dados campos de promoción y su asociación a membresía, al guardar
   y recargar no se pierden ni se reemplaza el importe histórico contratado.

| Criterio | Evidencia existente |
| --- | --- |
| CA-01 | [test_promocion_navidad.py](../../../backend/tests/test_promocion_navidad.py): `test_promociones_vigentes_publicas_and_autoapply`. |
| CA-02 | [test_promocion_cupos.py](../../../backend/tests/test_promocion_cupos.py). |
| CA-03 | [test_promocion_navidad.py](../../../backend/tests/test_promocion_navidad.py): `test_prevent_promocion_overlap`. |
| CA-04 | [test_admin_client_payment.py](../../../backend/tests/test_admin_client_payment.py): `test_admin_does_not_apply_unselected_promotion`, `test_invalid_promotion_does_not_create_client`. |
| CA-05 | [test_atomic_transactions_postgres.py](../../../backend/tests/test_atomic_transactions_postgres.py): `test_promotions_and_membership_association_survive_database_reload`; [test_membership_payments.py](../../../backend/tests/test_membership_payments.py). |

## 4. Technical Constraints

- API: [memberships_routes.py](../../../backend/presentation/routes/memberships_routes.py)
  para `/api/planes-membresia`; [promotions_routes.py](../../../backend/presentation/routes/promotions_routes.py)
  para `/api/promociones` y `/api/promociones/vigentes-publico`.
- Reglas compartidas en [memberships_rules.py](../../../backend/domain/services/memberships_rules.py).
  Entidades `PLANES_MEMBRESIA`, `PROMOCIONES` y asociación desde `MEMBRESIA`.
- Duración del plan configurada en días/meses/años; la implementación convierte
  meses en 30 días y años en 365. No inferir meses naturales.
- UI: [MembershipPlansView.vue](../../../frontend/src/presentation/views/MembershipPlansView.vue),
  [PromotionsView.vue](../../../frontend/src/presentation/views/PromotionsView.vue) y
  [publicCatalog.js](../../../frontend/src/application/services/publicCatalog.js).
- Consultas públicas; planes editables por `admin/staff`, promociones solo por `admin`.

## 5. Guardrails

No cambiar permisos por compartir la pantalla administrativa. No convertir
el caso de Navidad de una prueba en una promoción obligatoria de producción.
No reescribir importes de membresías ya contratadas al editar un plan.

## 6. Edge Cases

- Fecha fuera de vigencia, plan no aplicable o cupo agotado: no conceder el beneficio.
- Duración cero o con formato inválido: rechazar la configuración.
- Campo opcional histórico ausente: normalizarlo y preservar cero cuando sea válido.
- Oferta editada después de una compra: conservar descuento e importe guardados
  en esa membresía y su historial.
- Formularios de clientes: cargar el catálogo remoto antes de habilitar el alta;
  no ofrecer planes locales ante error o catálogo vacío. Filtrar las promociones
  por plan, inicio, fin, estado y cupos. La edición de datos personales conserva
  los valores contratados, incluso si ya no forman parte de la oferta activa.

## 7. Definition of Done

Verificar los criterios afectados, consultas públicas, permisos y límites de
fechas/cupos; si cambia persistencia, comprobar recarga. Actualizar el contrato
y cumplir el [DoD](../../docs/DoD.md).
