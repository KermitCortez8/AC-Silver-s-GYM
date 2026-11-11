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
| CA-01 | [test_promocion_navidad.py](../../../backend/tests/planes_promociones/unitarias/test_promocion_navidad.py): `test_promociones_vigentes_publicas_and_autoapply`. |
| CA-02 | [test_promocion_cupos.py](../../../backend/tests/planes_promociones/unitarias/test_promocion_cupos.py). |
| CA-03 | [test_promocion_navidad.py](../../../backend/tests/planes_promociones/unitarias/test_promocion_navidad.py): `test_prevent_promocion_overlap`. |
| CA-04 | [test_admin_client_payment.py](../../../backend/tests/clientes/integracion/test_admin_client_payment.py): `test_admin_does_not_apply_unselected_promotion`, `test_invalid_promotion_does_not_create_client`. |
| CA-05 | [test_atomic_transactions_postgres.py](../../../backend/tests/transversales/postgres/test_atomic_transactions_postgres.py): `test_promotions_and_membership_association_survive_database_reload`; [test_membership_payments.py](../../../backend/tests/membresias_pagos/integracion/test_membership_payments.py). |

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

### Límites de formularios

Los nombres de planes y promociones y la palabra clave admiten hasta 50 caracteres.
El contrato HTTP de duración conserva el máximo de 50 caracteres. Descripción y beneficios admiten hasta 150. Los
formularios bloquean el exceso sin avisos ni contadores de longitud; el servidor
rechaza escrituras que excedan los límites.

Evidencia: [validación de límites](../validaciones/limites-formularios/validation.md).

### Formulario de planes

La duración se elige en un selector con 1, 7, 15, 30, 60, 90, 180 y 365 días;
las altas parten de 30 días. Al editar se agrega la duración guardada como opción
si no pertenece a las habituales, conservando su valor exacto al guardar sin
cambiarla (por ejemplo, `45 dias` o `1 mes`). Esa opción permanece disponible
mientras se edita, incluso si se selecciona otra y luego se desea volver.

Duración y precio comparten una fila en escritorio y se apilan en móvil. El precio
inicial está vacío y exige completar un importe; cero sigue siendo válido si se
introduce expresamente. Nombre, duración y precio muestran errores asociados al
campo. Descripción y beneficios se identifican como opcionales. Se conservan los
límites silenciosos de 50/150 caracteres y el bloqueo durante el guardado.

Evidencia: [validación del formulario](../validaciones/formulario-planes/validation.md).

### Gestión visual del catálogo

La pantalla administrativa utiliza tarjetas adaptables con estado, precio, duración,
descripción, beneficios y acciones de editar/eliminar. El resumen cuenta planes
registrados, activos e inactivos. La búsqueda local ignora tildes y consulta nombre,
duración, descripción y beneficios; se combina con los filtros de estado. El orden
puede ser por nombre o precio ascendente/descendente, conservando cero.

La carga muestra espera, conserva los datos disponibles ante error y permite
reintentar. Se distinguen catálogo vacío y búsqueda sin coincidencias. El borrado
mantiene confirmación y bloquea solicitudes duplicadas; solo retira la tarjeta
cuando el servidor lo confirma. No cambia permisos, precios guardados ni la
vigencia de las membresías contratadas. Ver [validación del diseño](../validaciones/diseno-membresias/validation.md).
