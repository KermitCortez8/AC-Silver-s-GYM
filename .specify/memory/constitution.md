# Constitución de AC Silver's GYM

Versión: **1.1.0** · Adoptada: **2026-10-29** · Última modificación: **2026-10-29**.

Esta constitución codifica decisiones observables en el repositorio y las reglas
de documentación solicitadas en esta adopción. No certifica el estado de producción.

## I. Especificar cambios sobre la base existente

Cada cambio funcional parte del [inventario](../specs/000-base-implementada/spec.md)
y del contrato de su módulo. La spec incluye Sprint Goal, User Story, Acceptance
Criteria, Technical Constraints, Guardrails, Edge Cases y Definition of Done.
Los criterios son numerados y verificables. Ningún informe de errores constituye
por sí solo autorización para ampliar el alcance.

Antes de planificar o programar una funcionalidad, registrar en `context.md`
los módulos, fuentes consultadas, reglas afectadas, piezas a reutilizar y pruebas
elegidas. El plan debe enlazar ese contexto y las tareas cubrir todos los criterios.
Una pregunta informativa consulta la misma base sin iniciar cambios no pedidos.

## II. Respetar capas y reutilizar mecanismos

Se mantienen presentación, aplicación, dominio e infraestructura en ambos
componentes. Dominio y aplicación no importan implementaciones externas del
backend; los ensamblajes conectan puertos y adaptadores. El frontend obtiene sus
servicios por instancia de Pinia. Reutilizar fachadas y componentes existentes;
una reorganización mayor necesita alcance explícito en su propia spec.

## III. Persistir operaciones completas

Las mutaciones declaran recursos. Usar las RPC especializadas de matrículas y
asistencia y `commit_gym_transaction` para las demás operaciones soportadas.
Una RPC ausente o un conflicto no habilitan escrituras REST parciales. Mantener
la identidad estable y los campos de negocio en mappers y recargas. Todo cambio
SQL debe identificar precondiciones, orden y procedimiento de recuperación.

## IV. Autorizar en el servidor

Mantener los permisos de cada endpoint y el alcance del cliente autenticado.
El navegador no determina el actor de una operación, el pago confirmado ni la
identidad del cliente de autoservicio. Las claves privadas permanecen en el
servidor. No registrar secretos, tokens o respuestas sensibles de proveedores.

## V. Preservar reglas económicas y temporales

Usar los mecanismos actuales de dinero y redondeo; conservar el importe de la
compra, incluso si vale cero. La verificación Stripe comprueba la sesión,
importe, metadatos y modo. Pagar y activar son pasos distintos para membresías.
Las fechas de negocio usan `America/Lima`; la vigencia incluye el día final.
Mantener idempotencia y consistencia de stock ante reintentos.

## VI. Verificar con evidencia proporcional

Reutilizar las pruebas relevantes y añadir regresión cuando cambie una regla.
Registrar comandos y resultados reales. PostgreSQL real utiliza un contenedor
desechable explícito; una prueba omitida no se informa como aprobada. Las
revisiones visuales requieren evidencia propia cuando cambie la interfaz.
Para documentación, ejecutar el validador documental.

## VII. Mantener contratos vivos

Actualizar documentos de módulos junto con cambios de comportamiento. Separar
implementado, propuesto y no verificado. El [DoD](../docs/DoD.md) define el cierre;
las plantillas locales trasladan estos principios a specs, planes y tareas.

## Gobierno y cambios

El plan de cada feature declara su cumplimiento o las excepciones justificadas.
Un cambio de principio actualiza versión, fecha y documentos afectados. Registrar
la razón en el propio cambio; no atribuir decisiones a retrospectivas inexistentes.
En discrepancias, la petición explícita del usuario y la evidencia concreta guían
la actualización; una plantilla no crea nuevos requisitos de producto.

La versión 1.1.0 incorpora contexto obligatorio y trazabilidad por etapa como
parte del [flujo de trabajo disponible](../guias/spec-driven.md).
