# Procedencia y adaptaciones de Spec Kit

Se instaló `specify-cli==1.2.5` y se generó el scaffolding oficial de Codex con
skills y scripts Bash, sin eventos nativos. La integración instalada y
predeterminada es Codex. La versión sigue fijada en integrations/requirements.txt.

## Recursos oficiales

- scripts/bash y las plantillas base proceden de Spec Kit 1.2.5. Los hashes
  originales se conservan en integrations/speckit.manifest.json.
- Diez skills speckit-* proceden de la integración oficial. Su contenido local
  referencia un solo preámbulo en .codex/preamble.md; ya no se copia en cada skill.
  Se conservan los ajustes de rutas y de metadata de compatibilidad para Codex.
- integrations/codex.manifest.json conserva hashes originales como procedencia,
  no como afirmación de identidad con las skills adaptadas.
- La licencia original está en [UPSTREAM-LICENSE](UPSTREAM-LICENSE).

## Adaptaciones mantenidas

[project-overrides.json](integrations/project-overrides.json) registra hashes de
origen y actuales para cada recurso upstream modificado:

1. Generador y resolvedor usan .specify/specs sin alias raíz y normalizan punteros
   heredados, conservando operaciones de lectura sin persistencia.
2. El generador prepara context.md desde el override local sin sobrescribir análisis.
3. setup-plan ejecuta el hook de contexto/spec antes de escribir plan.md.
4. check-prerequisites --require-tasks ejecuta el mismo hook para implementación.
5. Las plantillas base de plan/tareas resuelven los overrides del proyecto.

El hook único [.codex/hooks/validate.py](.codex/hooks/validate.py), settings,
context-template, contratos, reglas, perfiles y skill gym-spec-driven son recursos
del proyecto. Los perfiles y reglas se aplican a las etapas mediante el preámbulo.
No son permisos ni eventos nativos de Codex. Los enlaces .agents/skills mantienen
el descubrimiento nativo y .github queda separada.

Se retiraron sdd.py, base/modules.json, el hook intermediario check-stage.py y
el workflow CLI alternativo no utilizado. La documentación histórica conserva
comandos y resultados ejecutados en su momento; sus enlaces a implementaciones
retiradas apuntan al sucesor o al índice vigente. Para trabajar usar únicamente
la [guía actual](guias/spec-driven.md), no reproducir comandos de esos registros.

## Actualización

Generar el nuevo scaffolding fuera del repositorio, comparar scripts/skills y
conservar constitución, contratos y overrides. Reaplicar ruta única, contexto
y llamadas al hook; actualizar hashes locales y ejecutar las pruebas aisladas.
No usar init --force sobre las skills adaptadas sin revisar el diff.
El entorno local del CLI es opcional para las comprobaciones del proyecto.

## Fuentes de procedencia

- [Spec Kit 1.2.5](https://github.com/github/spec-kit/releases/tag/v1.2.5).
- [Instalación](https://github.com/github/spec-kit/blob/v1.2.5/docs/installation.md).
- [Integración Codex](https://github.com/github/spec-kit/blob/v1.2.5/docs/integrations/codex.md).
- [Skills de Codex](https://learn.chatgpt.com/docs/build-skills).
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Las fuentes se consultaron durante la integración de 2026-10-29. La lectura de
reglas y fuentes debe realizarla la sesión; los archivos y sus checks no prueban
comprensión ni la ejecución de pruebas de producto.
