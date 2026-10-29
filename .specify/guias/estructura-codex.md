# Estructura para Codex y Spec Kit

Se conserva la estructura solicitada en la imagen, adaptando CLAUDE.md a
AGENTS.md y .claude a .codex dentro de .specify. Cada elemento tiene una función
en las etapas oficiales; no se mantiene un segundo motor de comandos.

## Documentos del equipo

`docs/` contiene únicamente [arquitectura](../docs/arquitectura.md),
[diseño](../docs/diseno.md), [DoD](../docs/DoD.md), [Backlog](../docs/Backlog.md)
y [RETRO_ACTIONS](../docs/RETRO_ACTIONS.md). Los contratos del producto están en
[base/modulos](../base/modulos/README.md) y las guías en guias.
Las features se guardan en specs cuando se solicita ese flujo.

## Componentes conservados y su uso

| Elemento de la imagen | Adaptación y uso en Spec Kit |
| --- | --- |
| Índice breve | [AGENTS.md](../AGENTS.md), enlazado por la entrada nativa de la raíz. |
| Configuración personal | AGENTS.local.md, ignorado, leído como complemento; [ejemplo](../AGENTS.local.md.example). |
| Reglas por tema/ruta | [rules](../.codex/rules/README.md): se consultan antes de especificar o modificar esas rutas. |
| Ajustes | [settings.json](../.codex/settings.json): reglas, artefactos requeridos y perfiles por etapa. |
| Hooks | [validate.py](../.codex/hooks/validate.py): validador único usado directamente por scripts oficiales y CI. |
| Agentes | [revisor y auditor](../.codex/agents/README.md): revisión durante analyze y antes del cierre en esta sesión. |
| Skills | [entrada del gimnasio](../.codex/skills/gym-spec-driven/SKILL.md) y diez etapas oficiales con un [preámbulo único](../.codex/preamble.md). |

## Qué se eliminó

Se retiraron el runner sdd.py, el inventario paralelo base/modules.json, el
hook intermediario check-stage.py y el workflow CLI alternativo no utilizado.
La implementación del validador quedó en hooks/validate.py; no hay una copia en
scripts. Las skills referencian el preámbulo en lugar de copiar su contenido.

Los scripts oficiales mantienen creación, numeración, selección y resolución
de plantillas. Crean el contexto desde una plantilla; Codex lo completa leyendo
los contratos existentes. La revisión de permisos, datos y alcance sigue siendo
responsabilidad de la sesión, con pruebas reales según el DoD.

## Integración y límites

`setup-plan.sh` ejecuta el hook antes de crear plan.md; los prerrequisitos con
--require-tasks lo ejecutan antes de continuar con implementación/análisis.
El cierre tiene su comprobación directa. Los ajustes los consume el hook y las
instrucciones de las skills; no son configuración nativa de permisos de Codex.
Los perfiles son instrucciones de revisión y no crean procesos o subagentes.

La entrada raíz AGENTS.md y los enlaces .agents/skills mantienen el descubrimiento.
El archivo personal se lee por indicación del índice; no sustituye instrucciones
compartidas ni contiene secretos. Las rutas de Spec Kit memory, templates,
scripts, specs e integrations conservan su ubicación. .github permanece separada;
no se recrean carpetas ni enlaces docs/specs en la raíz.

## Archivos locales

.venv contiene el CLI opcional y queda ignorado. La configuración local del
explorador oculta el entorno y las cachés; el hook evita crear bytecode. No se
traslada el entorno virtual ni se modifican dependencias de backend/frontend.
Las pruebas de integración verifican scripts y hook sin instalar el CLI ni
usar proveedores. Los comandos están en la [guía](spec-driven.md).

Fuentes de compatibilidad: [AGENTS.md oficial](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[configuración de Codex](https://learn.chatgpt.com/docs/config-file/config-reference)
y [hooks nativos](https://learn.chatgpt.com/docs/hooks). Los mecanismos locales
anteriores se distinguen de esos eventos y permisos nativos. Procedencia:
[UPSTREAM](../UPSTREAM.md).
