# AC Silver's GYM · instrucciones para Codex

Vue 3/Vite/Pinia y FastAPI/Supabase; frontend y backend contenerizados con Docker.
Trabajar en español desde el código. El proceso está en [.specify/](.specify/README.md).

## Contexto y reglas

Leer el [índice central](.specify/AGENTS.md), las [reglas comunes](.specify/.codex/rules/general.md),
[seguridad](.specify/.codex/rules/seguridad.md) y [pruebas](.specify/.codex/rules/testing.md).
Aplicar las reglas por rutas de [.codex/settings.json](.specify/.codex/settings.json).
Si existe `.specify/AGENTS.local.md`, leer sus preferencias complementarias.

## Consulta de base y activación de Spec Kit

Consultar [constitución](.specify/memory/constitution.md), [base 000](.specify/specs/000-base-implementada/spec.md),
[módulos](.specify/base/modulos/README.md), contratos, código y pruebas según el cambio.
Por indicación actual del usuario, resolver los pedidos directamente y no crear
specs, planes ni tareas ni iniciar el flujo Spec Kit hasta que lo pida expresamente.
Se pueden corregir referencias existentes necesarias al mantener la documentación.

Cuando el usuario active ese flujo, aplicar
[gym-spec-driven](.specify/.codex/skills/gym-spec-driven/SKILL.md) y seguir las etapas
oficiales y el [preámbulo único](.specify/.codex/preamble.md). Una consulta solo
analiza; la implementación autorizada continúa hasta verificar.

## Comprobaciones desde la raíz

```bash
python .specify/.codex/hooks/validate.py
python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage implement
python -B -m unittest discover -s .specify/tests -v
```

Seguir la [guía](.specify/guias/spec-driven.md). No modificar README principal salvo
petición explícita ni recrear docs/specs en la raíz. Conservar .github y los enlaces
nativos .agents/skills. Trabajar en esta sesión sin confirmaciones rutinarias ni agentes adicionales.
