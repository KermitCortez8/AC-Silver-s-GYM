# Base implementada de AC Silver's GYM

**ID:** `000-base-implementada` · **Fecha:** 2026-10-29.
**Estado:** inventario retrospectivo documentado; validación operativa no certificada.
**Referencia:** código y pruebas de `fc1577e` (`Mejora Sprint 2.5`).
**Entrada:** convertir los módulos existentes en base para Spec Driven con Codex.

No representa una feature nueva ni una lista de tareas para reconstruir el
sistema. Sus contratos detallados están en [docs/modulos](../../base/modulos/README.md).

## 1. Sprint Goal

Contar con una base verificable del producto ya construido para que Codex pueda
especificar cambios futuros sin deducir funcionalidades a partir de informes de errores.

## 2. User Story

**P1.** Como persona que mantiene el proyecto con Codex, quiero consultar el
comportamiento existente por módulo para definir cambios acotados conservando
sus reglas, integraciones y permisos.

**Prueba independiente:** desde `AGENTS.md`, localizar un módulo, seguir sus
fuentes y criterios, y redactar un cambio usando la plantilla de siete componentes.

**Escenario:** dado el código actual, cuando se consulta un contrato de módulo,
entonces se identifican su valor, comportamiento, restricciones, casos borde,
criterios y evidencias sin tomar un hallazgo histórico como alcance nuevo.

## 3. Acceptance Criteria

1. **CA-01.** El acceso con contraseña/Google, las cuentas internas y el límite
   de sesión se describen con sus fuentes y restricciones existentes.
2. **CA-02.** El registro de clientes y el ciclo pago/activación/vencimiento de
   membresías distinguen identidad, origen, importe guardado e historial.
3. **CA-03.** Planes, promociones, horarios y matrículas documentan sus permisos,
   fechas, cupos y mecanismos de persistencia existentes.
4. **CA-04.** Asistencias y rutinas documentan aforo, privacidad, auditoría,
   asignación, ejercicios y actor autenticado.
5. **CA-05.** Inventario y tienda distinguen reserva/stock de venta, movimientos,
   pedidos, checkout, cancelación e imágenes.
6. **CA-06.** Paneles, configuración y notificaciones identifican reglas,
   coordinación y dependencias de operación externa sin certificar despliegue.
7. **CA-07.** La base tiene índice para Codex, constitución, plantillas de siete
   componentes, plan/tareas y validación documental reproducible.
8. **CA-08.** Los informes históricos de errores conservan su contenido y están
   separados de los contratos funcionales y del alcance de futuros cambios.

| Criterio | Evidencia documental verificable |
| --- | --- |
| CA-01 | [MOD-01](../../base/modulos/01-identidad-acceso.md). |
| CA-02 | [MOD-02](../../base/modulos/02-clientes.md) y [MOD-03](../../base/modulos/03-membresias-pagos.md). |
| CA-03 | [MOD-04](../../base/modulos/04-planes-promociones.md) y [MOD-05](../../base/modulos/05-horarios-matriculas.md). |
| CA-04 | [MOD-06](../../base/modulos/06-asistencias.md) y [MOD-07](../../base/modulos/07-rutinas-progreso.md). |
| CA-05 | [MOD-08](../../base/modulos/08-inventario.md) y [MOD-09](../../base/modulos/09-tienda-pedidos.md). |
| CA-06 | [MOD-10](../../base/modulos/10-paneles-configuracion.md) y [MOD-11](../../base/modulos/11-notificaciones.md). |
| CA-07 | [AGENTS.md](../../../AGENTS.md), [constitución](../../memory/constitution.md), [flujo](../../guias/spec-driven.md), [validador](../../.codex/hooks/validate.py). |
| CA-08 | [Índice documental vigente](../../base/README.md). Los informes históricos fueron retirados por petición del usuario. |

### Requisitos funcionales de esta base

- **FR-001:** Cada área implementada tiene un contrato con los siete componentes.
- **FR-002:** Cada criterio enlaza una evidencia localizada y distingue código de prueba.
- **FR-003:** El siguiente cambio puede derivar spec, plan y tareas reutilizando la base.
- **FR-004:** Las limitaciones de herramientas, configuración y verificación son explícitas.

### Entidades del producto documentadas

Clientes/usuarios, planes/promociones/membresías, horarios/matrículas, asistencias,
rutinas/progreso, inventario/movimientos/productos, pedidos/detalles y colas de
notificación. Los documentos enlazan sus reglas y persistencia; no añaden tablas.

### Resultados medibles de la adopción

- **SC-001:** Once áreas del índice tienen su contrato completo.
- **SC-002:** Todos los contratos y la spec base incluyen siete secciones obligatorias.
- **SC-003:** Cada `CA-*` tiene una fila de evidencia y sus rutas locales existen.
- **SC-004:** El validador documental termina sin errores; no se deriva de ello
  una métrica de rendimiento, cobertura funcional o disponibilidad en producción.

## 4. Technical Constraints

Reutilizar Vue 3, Vite, Pinia, Vue Router, FastAPI/Pydantic, Supabase/PostgreSQL,
Stripe, Google y Resend tal como están integrados. Mantener cuatro capas,
ensamblaje explícito, operaciones con recursos y RPC atómicas. El detalle está
en [arquitectura](../../docs/arquitectura.md), [diseño](../../docs/diseno.md) y
[seguridad](../../.codex/rules/seguridad.md).

La estructura `.specify/memory`, `.specify/templates/overrides` y `specs/` se
prepara para GitHub Spec Kit. La instalación del CLI/skills no se simula; el
flujo directo con Codex usa `AGENTS.md` y los documentos.

## 5. Guardrails

No modificar comportamiento de la aplicación como efecto de documentarla. No
ejecutar migraciones o envíos/cobros reales para levantar el inventario. No
reemplazar informes de errores ni considerarlos backlog aprobado. No afirmar
que un módulo está desplegado o probado recientemente por localizar su código.
No trasladar hooks/configuración de Claude a nombres que Codex no reconoce.

## 6. Edge Cases

- Falta configuración de proveedor o migración: documentar la dependencia sin
  atribuirle funcionamiento remoto verificado.
- Código y relato histórico divergen: describir lo comprobable y señalar el límite.
- Funcionalidad parcial o endpoint sin pantalla completa: explicitar esa cobertura.
- Prueba solo con doble: identificarla como evidencia disponible; no como prueba
  real de concurrencia SQL o entrega externa.
- Futuro cambio con contrato diferente: especificar la diferencia en otra carpeta
  y actualizar el documento vivo del módulo.

## 7. Definition of Done

Esta adopción se cierra al completar CA-01…CA-08, comprobar enlaces/secciones y
verificar que el diff mantiene el código y los informes históricos intactos.
No requiere reejecutar pruebas de producto para un cambio solo documental.
El cierre de futuras funcionalidades se rige por [DoD](../../docs/DoD.md).
La comprobación de esta entrega y sus límites constan en [validation.md](validation.md).
