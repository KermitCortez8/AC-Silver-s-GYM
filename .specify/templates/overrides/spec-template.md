# Feature Specification: [NOMBRE DEL CAMBIO]

**ID / Feature Branch:** `[NNN-nombre]` · **Created:** [FECHA].
**Status:** Draft · **Input:** "$ARGUMENTS".
**Módulos afectados:** [MOD-XX y enlace a su contrato vivo].
**Base consultada:** [rutas concretas de código/pruebas y comportamiento actual].
**Contexto obligatorio:** `context.md`, preparado por el generador oficial y completado
con el análisis de comportamiento, reutilización y pruebas del cambio.

Eliminar todos los marcadores antes de dar por completa la especificación.
La spec describe el cambio solicitado; no ordena reconstruir la base `000`.

## 1. Sprint Goal

[Valor observable que debe existir al terminar. Alcance explícito del cambio.]

## 2. User Story

### User Scenarios & Testing

### US1 · [Recorrido principal] (Priority: P1)

Como [QUIÉN], quiero [QUÉ], para [PARA QUÉ].

**Why this priority:** [Valor de este recorrido].
**Independent Test:** [Acción que demuestra el recorrido por sí mismo].

**Acceptance Scenarios:**

1. **Given** [Estado], **When** [Acción], **Then** [Resultado observable].
2. **Given** [Error relevante], **When** [Acción], **Then** [Respuesta esperada].

[Añadir US2/US3 solo si aportan recorridos necesarios e independientemente verificables.]

## 3. Acceptance Criteria

1. **CA-01.** Dado [Estado], cuando [Acción], entonces [Resultado binario].
2. **CA-02.** Dado [Estado], cuando [Acción], entonces [Resultado binario].

| Criterio | Evidencia prevista o ejecutada (ruta local) |
| --- | --- |
| CA-01 | [Prueba existente, prueba a crear o procedimiento manual reproducible]. |
| CA-02 | [Prueba existente, prueba a crear o procedimiento manual reproducible]. |

### Requirements

### Functional Requirements

- **FR-001:** El sistema debe [Comportamiento exigido, vinculado a CA-01].

### Key Entities

- [Entidad y relación afectada, o justificación de que no cambian datos].

### Success Criteria

### Measurable Outcomes

- **SC-001:** [Resultado medible del cambio, sin inventar cifras de producción].

## 4. Technical Constraints

- **Stack y capas:** [Piezas actuales a conservar].
- **Reutilización:** [Servicios, puertos, componentes y operaciones concretos].
- **Contratos:** [API, permisos, datos, fechas, dinero y compatibilidad afectados].
- **Persistencia:** [Recursos declarados, RPC, migraciones y recuperación si aplica].
- **Dependencias:** [Configuración externa y precondiciones comprobables].

Las decisiones de implementación detalladas se derivan a `plan.md`.

## 5. Guardrails

- [Qué queda fuera de alcance].
- [Comportamiento existente que se debe preservar y cómo se comprobará].
- [Qué no ejecutar, cambiar o asumir durante este trabajo].

## 6. Edge Cases

| Caso borde | Respuesta esperada | Criterio |
| --- | --- | --- |
| [Condición límite concreta] | [Resultado observable] | CA-02 |

### Assumptions

[Suposiciones con fundamento. Resolver las que cambien la aceptación antes de implementar.]

## 7. Definition of Done

- [ ] Los criterios están verificados y enlazan evidencia real.
- [ ] Las comprobaciones aplicables de `.specify/docs/DoD.md` pasan o se declaran sus límites.
- [ ] Se actualizaron plan, tareas y contratos vivos afectados.
- [ ] No quedan supuestos de comportamiento sin resolver ni tareas requeridas abiertas.
