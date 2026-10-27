# Implementation Plan: Control de errores y conservación de estado

**Feature**: `001-control-errores` | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

## Summary

Adoptar GitHub Spec Kit en el monorepositorio y usar el control de errores como
piloto. Formalizar el comportamiento existente, localizar evidencia y definir
las correcciones pendientes. Esta entrega instala el proceso y sus artefactos;
no modifica el comportamiento funcional de la aplicación.

## Technical Context

- **Language/Version**: Python 3.12+; JavaScript con Node.js 22+.
- **Primary Dependencies**: FastAPI, Pydantic, Vue 3, Pinia y Vite existentes.
- **Storage**: Supabase/PostgreSQL; sin cambios de esquema para este piloto.
- **Testing**: pytest, node:test, flake8 y compilación Vite existentes.
- **Target Platform**: navegador; backend Linux/Docker.
- **Project Type**: aplicación web con backend y frontend en el mismo repositorio.
- **Performance Goals**: sin objetivos nuevos; el transporte conserva 30 segundos
  predeterminados de espera de respuesta completa.
- **Constraints**: respetar trabajo local, contratos públicos y límites de capas;
  sin reintentos automáticos de escrituras ni acceso a proveedores de producción.
- **Scale/Scope**: cuatro historias y nueve requisitos `ERR-*`.
- **Toolchain**: Spec Kit 1.2.3, commit
  `5ea8b1cf0a38699340a38e00d02770308997d8c0`, instalación en `.tools/spec-kit`.

## Constitution Check

| Principio | Antes del diseño | Después del diseño |
| --- | --- | --- |
| I. Cuatro capas | Se reutilizan las capas existentes | Las futuras correcciones quedan asignadas a su capa. |
| II. Contratos | Sin cambios públicos ni migraciones | Se documenta el contrato actual y el cambio pendiente de cancelación frontend. |
| III. Errores observables | Hay criterios sobre estado, borrador e incertidumbre | ERR-009 distingue cancelación antes y después del envío. |
| IV. Evidencia | Pruebas existentes vinculadas | Tareas y registro separan pruebas ejecutadas de aceptación pendiente. |
| V. Adopción gradual | Un piloto acotado | No se añade otro framework de tests ni se reestructura la aplicación. |

No se identifican excepciones a la constitución en este diseño. Esta revisión
evalúa el plan; no afirma que todos los requisitos funcionales estén implementados.

## Project Structure

```text
.agents/skills/speckit-*/       Skills oficiales generadas para Codex
.specify/                     Scripts, plantillas, integración y workflow oficiales
.specify/memory/constitution.md
scripts/setup-spec-kit.sh     Instalación local reproducible
scripts/specify               Acceso a la CLI local
tools/spec-kit-requirements.txt
specs/001-control-errores/
  spec.md
  plan.md
  research.md
  data-model.md
  contracts/errors.md
  quickstart.md
  tasks.md
  verification.md
  checklists/requirements.md
backend/{domain,application,infrastructure,presentation}/
backend/tests/
frontend/src/{domain,application,infrastructure,presentation}/
frontend/tests/
```

## Diseño y responsabilidades

| Responsabilidad | Ubicación existente | Acción prevista |
| --- | --- | --- |
| Traducir errores HTTP | `backend/presentation/error_handlers.py` | Reutilizar; verificar estados y privacidad. |
| Validar contratos de entrada | `backend/domain/validation.py` y modelos | Reutilizar reglas actuales y sus tests. |
| Espera y cancelación | `frontend/src/infrastructure/services/httpTransport.js` | T013/T014: probar y corregir ERR-009 antes de cerrar el piloto. |
| Interpretar respuestas | `frontend/src/infrastructure/services/apiResponse.js` | Mantener estados y códigos; comprobar resultado incierto con respuesta inválida. |
| Conservar estado | `frontend/src/application/modules/` y `services/responseValidation.js` | Reutilizar y verificar confirmaciones e identidades. |
| Borradores y mensajes | `frontend/src/presentation/` | Verificar flujos reales y accesibilidad. |
| Guardado y refresco | `frontend/src/presentation/utils/refreshSavedView.js` | Reutilizar semántica de guardado confirmado. |

## Implementación y verificación

1. Instalar infraestructura oficial y conservarla sin personalizaciones internas.
2. Definir constitución, historias, requisitos, contrato y decisiones.
3. Ejecutar la base de pruebas existente y registrar resultados.
4. En una entrega funcional posterior, seguir las tareas abiertas por historia:
   prueba de regresión primero, cambio mínimo después y nueva evidencia al final.
5. Analizar consistencia y convergencia; mientras queden tareas de aceptación,
   mantener el piloto abierto.

Ver [tasks.md](tasks.md) para dependencias y [quickstart.md](quickstart.md) para
comandos. La aceptación no se automatiza mediante la mera presencia de archivos.

## Compatibilidad y actualización de la herramienta

Las dependencias SDD no se agregan a la aplicación ni a sus imágenes. La CLI queda
ignorada en Git; se versionan los requisitos fijados, las skills y los artefactos.
No se instala la extensión Git: no hay cambio de rama ni commit automático.
Al actualizar Spec Kit, generar primero en una carpeta temporal, revisar cambios
y preservar la constitución y specs. CI valida estructura del piloto con el script
oficial; los trabajos funcionales existentes siguen verificando la aplicación.

## Complexity Tracking

Sin excepciones. Se conservan las herramientas oficiales y los runners existentes.
