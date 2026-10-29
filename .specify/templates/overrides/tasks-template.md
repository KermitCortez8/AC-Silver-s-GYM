# Tasks: [CAMBIO]

**Input:** `spec.md`, `plan.md` y contratos afectados.
Leer `context.md`. Antes de código ejecutar
`python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage implement`.
**Formato:** `- [ ] TNNN [USn] Descripción con ruta y criterio CA-NN`.
Añadir una prueba de regresión si cambia una regla; reutilizar la existente
cuando ya demuestre el criterio. No crear pruebas que solo repitan implementación.

## Preparación

- [ ] T001 Leer base y contratos afectados; contrastar el estado actual con código.
- [ ] T002 Revisar spec/plan/constitución y resolver dudas que afecten a los criterios.

## US1 · [Recorrido principal]

- [ ] T003 [US1] [Añadir/adaptar comprobación de CA-01 en ruta concreta].
- [ ] T004 [US1] [Implementar CA-01 en ruta concreta reutilizando el mecanismo actual].
- [ ] T005 [US1] [Cubrir caso borde CA-02 en ruta concreta].

## Cierre

- [ ] T006 Ejecutar comprobaciones pertinentes de `.specify/docs/DoD.md` y registrar resultados.
- [ ] T007 Actualizar contrato vivo y documentos transversales afectados.
- [ ] T008 Revisar todos los CA, plan/tareas y casos borde; conservar evidencia de cierre.
- [ ] T009 Completar `validation.md`, actualizar módulos afectados y ejecutar
  `python .specify/.codex/hooks/validate.py --feature NNN-nombre --stage close` y `python .specify/.codex/hooks/validate.py` y las pruebas de `.specify/tests/`.

## Dependencias y secuencia

[Indicar dependencias reales. No marcar tareas como paralelas cuando comparten
archivos, estado o decisiones pendientes.]

## Evidencia de ejecución

| Fecha | Comando/procedimiento | Resultado | Criterios | Límites |
| --- | --- | --- | --- | --- |
| [Fecha] | [Comando real] | [Resultado real, no anticipado] | [CA-NN] | [Omisiones/fallos] |

Marcar tareas completas solo después de realizar y verificar su resultado.
