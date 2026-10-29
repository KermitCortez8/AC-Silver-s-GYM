# Backlog y alcance

## Entregado en la adopción documental

El objetivo de esta entrega es convertir código existente en contexto utilizable
por Codex y Spec Kit, no reconstruir módulos ni ejecutar una nueva refactorización.

| Elemento | Estado y evidencia |
| --- | --- |
| Instrucciones breves de Codex | Documentadas en [AGENTS.md](../../AGENTS.md). |
| Inventario de funcionalidades | Once contratos en [módulos](../base/modulos/README.md). |
| Siete componentes por spec | [Base 000](../specs/000-base-implementada/spec.md) y plantilla local. |
| Reglas transversales | Constitución, arquitectura, diseño, seguridad y DoD. |
| Flujo para próximos cambios | [Spec Driven](../guias/spec-driven.md), plantillas de plan y tareas. |
| Control automático documental | Validador local y workflow `spec-docs.yml`. |
| Herramientas y organización | [Índice central](../README.md), [estructura](../guias/estructura-codex.md) y [procedencia](../UPSTREAM.md). |

## Próximo sprint

No hay funcionalidad nueva, fechas, responsables ni prioridad de producto
aprobados. Las specs de cambios se crearán solo cuando el usuario active ese
flujo expresamente; mientras tanto se atienden los pedidos directamente.

## Candidatos que requieren alcance explícito

Los límites de [arquitectura](arquitectura.md) permiten proponer, por separado:

- Paginación de clientes, membresías y pedidos si el volumen la exige.
- Reducir cargas y bloqueos de tabla de transacciones si existe un caso medido.
- Continuar separando pantallas extensas sin cambiar contratos funcionales.

Son propuestas, no tareas comprometidas ni requisitos retroactivos. Los hallazgos
que se aporten deben contrastarse con el código y no amplían el alcance por sí solos.
