---
name: gym-spec-driven
description: Analiza, diseña e implementa funcionalidades de AC Silver's GYM consultando su base, módulos, reglas y pruebas. Úsala para nuevas funcionalidades o cambios de comportamiento del gimnasio, incluso pedidos en lenguaje natural. Una pregunta de viabilidad solo analiza; una petición de implementación recorre Spec Kit hasta verificar el resultado. No aplica a tareas ajenas al repositorio.
---

# Spec Driven sobre la base del gimnasio

Leer el [preámbulo compartido](../../preamble.md), [AGENTS raíz](../../../../AGENTS.md),
[índice de módulos](../../../base/modulos/README.md), contratos, código y pruebas.
La base 000 describe lo existente y no se reimplementa. Los informes de errores
no añaden alcance autorizado. Usar las reglas de settings.json según las rutas.

## Consulta

Si preguntan cómo encaja una idea, consultar fuentes y explicar viabilidad,
reutilización, dependencias y dudas sin crear features o código.

## Implementación

1. Crear o continuar una sola feature con speckit-specify y el generador oficial.
   El generador prepara contexto y spec. Completar context.md leyendo contratos
   y fuentes, y spec.md con siete componentes. Clarificar ambigüedades reales.
2. Ejecutar speckit-plan; su script comprueba spec y contexto antes de escribir
   plan.md. El plan enlaza el contexto y define pruebas por criterio.
3. Ejecutar speckit-tasks y speckit-analyze. Aplicar el perfil de revisor indicado
   en settings.json; resolver hallazgos con las etapas correspondientes.
4. Ejecutar speckit-implement. Sus prerrequisitos comprueban los artefactos y la
   trazabilidad. Reutilizar servicios, puertos, componentes y pruebas existentes.
5. Ejecutar speckit-converge y completar tareas del alcance que falten. Aplicar
   el perfil de auditor antes del cierre, en esta misma sesión. Actualizar módulos
   y documentos afectados y registrar resultados reales en validation.md.
6. Ejecutar el hook de cierre, el validador global y las pruebas aisladas según
   el preámbulo. Las suites del producto dependen del alcance y del DoD.

Las especificaciones viven exclusivamente en .specify/specs/. Los perfiles no
abren agentes. No publicar, cobrar, enviar correos ni desplegar por invocar esta
skill. No afirmar pruebas o comprobaciones externas que no se ejecutaron.
