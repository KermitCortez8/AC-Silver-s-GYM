# Feature Specification: Control del flujo de clientes

**ID / Feature Branch:** `001-control-flujo-clientes` · **Created:** 2026-10-29.
**Status:** Backend y frontend implementados y verificados localmente · **Input:** revisión y corrección del flujo completo solicitada por el usuario.
**Contexto:** [context.md](context.md). Base: [000](../000-base-implementada/spec.md).
**Módulos afectados:** MOD-01, MOD-02, MOD-03, MOD-05 y MOD-06, enlazados en contexto.

## 1. Sprint Goal

Corregir errores reproducibles de registro, clientes, membresías, horarios y asistencias,
y dejar un control de regresión del recorrido completo sobre la base existente.

## 2. User Story

### US1 · Registro y administración coherentes (Priority: P1)

Como personal autorizado quiero registrar, cobrar, activar y mantener clientes sin ocultar
fallos ni alterar compras confirmadas. Prueba independiente: alta sintética, reintento,
pago, activación repetida y rechazo de edición destructiva.

**Acceptance Scenarios:** Dado un registro pendiente, al pagar sigue pendiente de activación;
al activar dos veces conserva fechas. Ante un fallo de borrado, la API informa el error.
Ante un fallo al verificar el pago, la pantalla permite consultar la misma sesión;
la ficha refleja el pago y la activación confirmados sin envíos repetidos.

### US2 · Horarios y asistencia coherentes (Priority: P1)

Como administrador quiero horarios utilizables y entradas solo con vigencia válida.
Prueba independiente: crear horario, matricular, entrar/salir, cancelar y vencer con reloj fijo.

**Acceptance Scenarios:** Dado un horario inválido, al guardarlo se rechaza sin escritura;
dada una membresía inválida, al registrar asistencia no se consume aforo.

## 3. Acceptance Criteria

1. **CA-01.** El registro público repetido con credenciales correctas reutiliza cliente, membresía e importe; credenciales o DNI diferentes no permiten reutilizar un alta ajena.
2. **CA-02.** El borrado administrativo propaga fallos de persistencia como 503 y errores de identificador como 400; solo devuelve 204 cuando el comando termina.
3. **CA-03.** Una edición de membresía pagada, activa o vencida se rechaza sin modificar importe, fechas, pago ni propietario; una pendiente solo se edita para su cliente y conserva el ciclo pendiente.
4. **CA-04.** La confirmación nunca sustituye un importe guardado cero por el precio actual; rechaza pagos positivos para esa compra y conserva los reintentos de pagos válidos.
5. **CA-05.** Los horarios rechazan días inexistentes y horas con texto sobrante o segundos que alteran la duración; las horas admitidas se guardan en formato de 24 horas utilizable por asistencia.
6. **CA-06.** La asistencia rechaza membresías con fechas ausentes o inválidas, impagas, futuras o vencidas, con la misma regla de vigencia que autenticación.
7. **CA-07.** Un recorrido integrado verifica registro, pago, activación idempotente, matrícula, aforo, entrada/salida, cancelación y vencimiento; las suites existentes conservan permisos y privacidad.
8. **CA-08.** Si falla la verificación de pago, la pantalla distingue error, pendiente y verificado; permite reintentar sin nuevo cobro, rechaza confirmaciones de otro cliente y descarta respuestas de rutas anteriores.
9. **CA-09.** La confirmación manual bloquea envíos repetidos mientras está en curso; al activar se actualiza el diálogo con el cliente confirmado y desaparece la acción de activación pendiente.

| Criterio | Evidencia prevista o ejecutada |
| --- | --- |
| CA-01 | [Pruebas](../../../backend/tests/test_admin_client_payment.py) y [verificación](quickstart.md). |
| CA-02 | [Pruebas](../../../backend/tests/test_client_flow_control.py) y [verificación](quickstart.md). |
| CA-03 | [Pruebas](../../../backend/tests/test_client_flow_control.py) y [verificación](quickstart.md). |
| CA-04 | [Pruebas](../../../backend/tests/test_client_flow_control.py) y [verificación](quickstart.md). |
| CA-05 | [Pruebas](../../../backend/tests/test_client_flow_control.py) y [verificación](quickstart.md). |
| CA-06 | [Pruebas](../../../backend/tests/test_client_flow_control.py) y [verificación](quickstart.md). |
| CA-07 | [Pruebas](../../../backend/tests/test_client_flow_control.py) y [verificación](quickstart.md). |
| CA-08 | [Frontend](../../../frontend/tests/36-client-flow-control.test.js). |
| CA-09 | [Frontend](../../../frontend/tests/36-client-flow-control.test.js). |

### Functional Requirements

- **FR-001:** Mantener registro, identidad y propagación de errores (CA-01, CA-02).
- **FR-002:** Proteger ciclo e importes contratados (CA-03, CA-04).
- **FR-003:** Validar horarios y vigencia de asistencia (CA-05, CA-06).
- **FR-004:** Mantener control integrado reproducible y suites de regresión (CA-07).
- **FR-005:** Controlar errores y acciones repetidas en las pantallas de pago y clientes (CA-08, CA-09).

### Key Entities

CLIENTES, MEMBRESIA, HORARIOS_SERVICIO, MATRICULAS_HORARIO y ASISTENCIA existentes;
no se añaden tablas ni estados de negocio.

### Success Criteria

- **SC-001:** Cada CA dispone de evidencia local ejecutada, distinguiendo omisiones externas.
- **SC-002:** Las regresiones reproducen los defectos y pasan tras la corrección.

## 4. Technical Constraints

Reutilizar FastAPI/Pydantic, Vue/Pinia y las cuatro capas. Mantener los comandos con
recursos, RPC especializadas y transacción general. Fechas de America/Lima, vigencia
inclusiva e importes en céntimos existentes. No alterar los permisos HTTP.

## 5. Guardrails

Conservar el diseño actual; corregir sus estados y acciones. Sin nuevas funcionalidades, migraciones, despliegues, correos ni cobros reales.
La revisión cubre el código local y pruebas sintéticas; no certifica producción.
Mantener compatibilidad de lectura histórica y reintentos idempotentes.

## 6. Edge Cases

| Caso borde | Respuesta esperada | Criterio |
| --- | --- | --- |
| Checkout falla tras alta | Reintentar sin duplicar | CA-01 |
| Base indisponible al borrar | 503, conservar error visible | CA-02 |
| Identificador de membresía ajena | Rechazar sin transferir compra | CA-03 |
| Descuento deja importe cero | No cobrar precio de catálogo | CA-04 |
| Día inventado / hora parcial | Rechazar antes de guardar | CA-05 |
| Fecha inválida / último día | Rechazar inválida, admitir último día | CA-06 |
| Reintento / aforo lleno | Sin duplicar / sin exceder capacidad | CA-07 |

### Assumptions

Se interpretan activación y control conforme a los contratos existentes. Las compras
cero no habilitan un nuevo flujo gratuito: se conserva el rechazo de cobros no positivos.
No se necesita aclaración de producto para corregir estas inconsistencias.

## 7. Definition of Done

- [x] Criterios cubiertos por regresiones y recorrido integrado.
- [x] Plan, tareas, contratos y evidencia actualizados.
- [x] Hooks y suites pertinentes ejecutados, con límites declarados.
