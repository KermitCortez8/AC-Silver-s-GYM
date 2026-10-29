# Implementation Plan: [CAMBIO]

**Branch:** `[NNN-nombre]` · **Date:** [FECHA] · **Spec:** `spec.md`.
**Input:** Spec y contratos de módulos afectados.
**Contexto consultado:** `context.md` (enlazar el archivo al completar el plan).
Completar su evaluación antes del plan y ejecutar
`python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage plan`.

## Summary

[Problema actual, comportamiento resultante y alcance técnico acotado.]

## Technical Context

| Aspecto | Decisión y evidencia |
| --- | --- |
| Lenguaje/dependencias | [Versiones del manifiesto; reutilizar el stack actual]. |
| Módulos/capas | [Áreas y archivos afectados]. |
| Almacenamiento | [Entidades, recursos y mecanismo atómico]. |
| Contratos | [Endpoints, modelos y permisos afectados]. |
| UI | [Componentes, estados de pantalla y temas si aplica]. |
| Integraciones | [Proveedor/configuración y forma de simular pruebas]. |
| Pruebas | [Suites relevantes y carencias que debe cubrir el cambio]. |
| Base reutilizada | [Módulos de context.md, componentes/servicios y archivos de prueba seleccionados]. |

## Constitution Check

Revisar `.specify/memory/constitution.md` antes de desglosar tareas.

- [ ] I: siete componentes y alcance basado en el sistema actual.
- [ ] II: capas y mecanismos existentes reutilizados.
- [ ] III: atomicidad, recursos e identidad conservados.
- [ ] IV: permisos y privacidad preservados.
- [ ] V: dinero, idempotencia y fechas de Perú preservados.
- [ ] VI: comprobaciones proporcionales y evidencia prevista.
- [ ] VII: contratos vivos que se actualizarán identificados.

## Project Structure

[Enumerar rutas reales de archivos a modificar/crear; no copiar un árbol genérico.]

## Diseño del cambio

1. [Estado actual y flujo propuesto].
2. [Reutilización de servicios/puertos/repositorios/componentes].
3. [Errores, concurrencia y casos borde por criterio].

## Datos y migraciones

[Indicar «No aplica» con razón si no hay cambios. En caso contrario: esquema
previo, migraciones por nombre, orden, mapeo, recuperación y prueba aislada.]

## Verificación y trazabilidad

| Criterio | Archivos | Prueba/comando | Evidencia esperada |
| --- | --- | --- | --- |
| CA-01 | [Rutas] | [Comando] | [Resultado binario] |

## Complexity Tracking

[Excepciones justificadas a la constitución o «Sin excepciones». Registrar
limitaciones reales y asuntos que requieren aclaración; no inventar decisiones.]
