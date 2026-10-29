# Índice de trabajo de Codex

El flujo Spec Kit se activa solo cuando el usuario lo indique expresamente.
Mientras tanto, consultar la base y resolver los pedidos sin generar specs,
planes o tareas. Este directorio concentra el Spec Driven de AC Silver's GYM. Mantener un archivo
por tema y conservar las rutas que necesita Spec Kit. El punto nativo de entrada
está en [AGENTS.md raíz](../AGENTS.md).

| Tema | Fuente |
| --- | --- |
| Identidad, comandos y distribución | [README central](README.md). |
| Principios y base construida | [Constitución](memory/constitution.md), [base 000](specs/000-base-implementada/spec.md) y [módulos](base/modulos/README.md). |
| Reglas comunes y por rutas | [Índice](.codex/rules/README.md), [generales](.codex/rules/general.md), [seguridad](.codex/rules/seguridad.md) y [pruebas](.codex/rules/testing.md). |
| Arquitectura y UI | [Arquitectura](docs/arquitectura.md), [diseño](docs/diseno.md). |
| Forma de trabajo y cierre | [Flujo](guias/spec-driven.md), [guía práctica](guias/guia-spec-driven-chatbot.md), [DoD](docs/DoD.md). |
| Alcance y acuerdos | [Backlog](docs/Backlog.md), [acciones](docs/RETRO_ACTIONS.md). |
| Configuración y verificaciones | [settings.json](.codex/settings.json), [hooks](.codex/hooks/README.md). |
| Revisión y auditoría | [Perfiles](.codex/agents/README.md). |
| Flujos repetibles | [Skill de entrada](.codex/skills/gym-spec-driven/SKILL.md) y etapas `speckit-*` en `.codex/skills/`. |
| Equivalencia con el mapa solicitado | [Estructura para Codex](guias/estructura-codex.md). |

Leer reglas generales, seguridad y pruebas antes de trabajar; seleccionar las
demás reglas según las rutas afectadas. Si existe `AGENTS.local.md`, leerlo como
preferencias complementarias sin secretos; se mantiene ignorado por Git y no
sustituye la constitución, el alcance pedido ni las instrucciones compartidas.

Para cambios dentro de esta carpeta, conservar los hashes upstream registrados,
los overrides y el descubrimiento nativo de skills. Ejecutar el hook global y las pruebas aisladas cuando
cambie el flujo; para documentación basta el validador documental. No modificar
el README principal salvo petición explícita ni recrear alias raíz.
