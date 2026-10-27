# Feature Specification: Control de errores y conservación de estado

**Feature**: `001-control-errores` (contexto de Spec Kit; no cambia la rama Git).
**Created**: 2026-10-27.
**Status**: especificado; aceptación completa pendiente de las tareas abiertas.
**Input**: adoptar Spec Kit usando el control de errores existente como piloto.
Base: código del workspace, incluido el trabajo local sin commit sobre el
transporte HTTP y los identificadores de respuestas.

## Problema y alcance

Un fallo de conexión, una respuesta inválida o una recarga fallida pueden inducir
al personal o al cliente a perder un borrador, creer que guardó datos o repetir
una operación que ya llegó al servidor.

Esta especificación formaliza el contrato común de errores de la API y el
comportamiento del frontend al leer o modificar datos. Se aplica a los módulos
que usan esos mecanismos compartidos. Cada flujo conserva sus permisos y reglas
de negocio; su cobertura debe comprobarse antes de extender una conclusión a
todas las pantallas.

Quedan fuera nuevas reglas de membresía, cambios de permisos, nuevos endpoints,
reintentos automáticos, claves de idempotencia y cambios de proveedores.

## User Scenarios & Testing

### US1 — Conservar datos al consultar o guardar (Priority: P1)

El personal necesita conservar sus datos y borradores cuando falla una consulta,
un guardado o una eliminación. Evita pérdida de trabajo y falsos éxitos.
**Independent Test**: cargar inventario, simular una respuesta malformada y
comparar el estado anterior con el posterior. Criterios: ERR-001 a ERR-003.

**Acceptance Scenarios**:

1. **Dado** un registro válido, **cuando** llega su confirmación válida,
   **entonces** se publica el resultado confirmado.
2. **Dado** un catálogo y un borrador, **cuando** falla el guardado,
   **entonces** ambos se conservan y el usuario recibe el error.

### US2 — Entender los errores sin exponer datos privados (Priority: P1)

Clientes y personal necesitan un mensaje útil, conservando estados y códigos
que permiten recuperar el flujo. Criterios: ERR-006 a ERR-008.
**Independent Test**: provocar un error de campo y un fallo de proveedor en las
rutas del piloto; comprobar respuesta, mensaje y ausencia de secretos.

**Acceptance Scenarios**:

1. **Dada** una solicitud inválida, **cuando** llega `422`, **entonces** se
   identifican los campos afectados sin reflejar el valor privado enviado.
2. **Dada** una membresía requerida, **cuando** llega el error de negocio,
   **entonces** se conserva el estado `403` y el código recibido si existe.

### US3 — Evitar repetir una escritura de resultado incierto (Priority: P1)

El personal necesita distinguir una escritura rechazada de una cuya respuesta
se perdió. Criterios: ERR-004 y ERR-009.
**Independent Test**: bloquear el cuerpo de un `POST`, agotar el tiempo o cancelar
su espera, comprobar un solo envío y la indicación de resultado incierto.

**Acceptance Scenarios**:

1. **Dadas** cabeceras recibidas y cuerpo bloqueado, **cuando** vence el límite,
   **entonces** se informa de timeout sin reintentar el `POST`.
2. **Dada** una escritura enviada, **cuando** se cancela su espera,
   **entonces** se informa de cancelación y de que no se confirmó el resultado.

### US4 — Reconocer un guardado aunque falle la recarga (Priority: P2)

El entrenador necesita saber que su progreso ya fue guardado para evitar
registrarlo de nuevo. Criterio: ERR-005.
**Independent Test**: confirmar un progreso y hacer fallar solo la recarga.

**Acceptance Scenarios**:

1. **Dado** un progreso confirmado, **cuando** falla la recarga,
   **entonces** se informa del guardado y de la vista pendiente de actualizar.

### Edge Cases

- Respuesta `204`, cuerpo JSON truncado e identidad numérica inválida.
- Timeout antes de cabeceras o durante el cuerpo, incluidos cuerpos de error HTTP.
- Cancelación anterior al envío y cancelación durante una escritura enviada.
- Guardado confirmado con fallo exclusivo del refresco posterior.
- Diferenciar fallo del contrato de entrada y modelo interno inválido.

## Requirements

Los IDs `ERR-*` son los requisitos funcionales estables de este piloto. Se
conservan para mantener trazabilidad con la propuesta inicial.

### Functional Requirements

### ERR-001 — Confirmación válida

Una lectura válida publica los datos recibidos. Un guardado con registro de
respuesta publica ese registro solo tras validar la estructura e identidad que
requiere el recurso. Un `204` previsto por el contrato se acepta sin exigir JSON.

**Dado** un borrado permitido con respuesta `204`, **cuando** se procesa la
respuesta, **entonces** no se intenta interpretar un cuerpo JSON inexistente.

Para recursos con identidad numérica positiva, se aceptan enteros seguros mayores
que cero o cadenas de dígitos decimales equivalentes, incluidos ceros iniciales.
Se rechazan booleanos, contenedores, espacios, exponentes, fracciones, cero,
negativos y valores fuera del rango seguro de JavaScript. Esta regla no redefine
los códigos alfanuméricos de usuario o cliente.

### ERR-002 — Lectura fallida

Una lectura rechazada o malformada no sustituye los últimos datos válidos, comunica
el fallo y libera el indicador de carga aplicable. No se presenta como lista vacía
ni se registra como actualización correcta de caché.

**Dado** un historial de inventario cargado, **cuando** la siguiente consulta
devuelve una estructura inválida, **entonces** el historial anterior permanece
disponible y la consulta termina con error.

### ERR-003 — Escritura rechazada o respuesta inválida

Un guardado o borrado rechazado no publica un éxito ni incorpora o elimina datos
locales como si estuviera confirmado. El formulario conserva el borrador cuando
corresponda. Una respuesta inválida no demuestra que el servidor haya revertido
una escritura: se debe consultar el estado antes de repetir una operación dudosa.

**Dado** un catálogo de rutinas cargado, **cuando** un guardado devuelve una
identidad inválida, **entonces** se rechaza la respuesta y el catálogo local
permanece igual.

### ERR-004 — Espera limitada y escritura sin confirmación

El transporte usa un límite predeterminado de 30 segundos, configurable, que
cubre la recepción del cuerpo completo en las solicitudes JSON/texto actuales.
No reintenta escrituras automáticamente.

**Dado** un `POST` cuyas cabeceras llegan pero cuyo cuerpo queda bloqueado,
**cuando** vence el límite, **entonces** se produce `request_timeout`, la
escritura queda marcada con `outcomeUnknown = true`, se realiza un único envío
y el mensaje indica actualizar los datos antes de repetirla.

Un fallo de conexión produce `network_error`; en escrituras también expresa que
el resultado no está confirmado. El formato de error ante cancelación se recoge
en ERR-009: cancelar la espera no demuestra una reversión del servidor.

### ERR-005 — Guardado confirmado y recarga fallida

Una recarga posterior fallida no convierte un guardado confirmado en un guardado
rechazado. Se informa de ambos resultados y se evita inducir un segundo envío.

**Dado** un progreso de rutina confirmado, **cuando** falla la recarga de la
ficha, **entonces** el diálogo de guardado se cierra, se libera el indicador y
se informa de que el progreso se registró pero la vista no pudo actualizarse.

### ERR-006 — Estados HTTP y códigos de negocio

La API mantiene los siguientes estados. El frontend conserva el estado recibido
y el código de negocio cuando la respuesta incluye uno.

| Situación | HTTP |
| --- | --- |
| Validación de negocio | 400 |
| Sesión ausente o inválida | 401 |
| Permiso insuficiente o membresía requerida | 403 |
| Entidad inexistente | 404 |
| Conflicto de asistencia, matrícula o pedido | 409 |
| Solicitud que incumple el esquema | 422 |
| Error inesperado o modelo interno inválido | 500 |
| Persistencia o proveedor no disponible | 503 |

**Dada** una respuesta `403` con `detail.code = membership_expired`, **cuando**
el frontend la interpreta, **entonces** conserva `403`, el código y el mensaje.

El contrato existente admite `detail` como texto, como objeto con `code` y
`message`, o como lista de problemas de validación. No se introduce otro sobre
de respuesta como parte de este piloto.

### ERR-007 — Errores sin datos privados

Un `422` incluye solo `loc`, `msg` y `type` por problema. No refleja el valor
enviado ni el contexto del validador. Los errores inesperados devuelven mensajes
genéricos, sin detalles del proveedor ni del estado interno. `SchemaNotReady`
conserva su indicación accionable de migración pendiente.

**Dada** una credencial con tipo incorrecto, **cuando** la API responde `422`,
**entonces** el cuerpo no contiene el secreto enviado ni atributos `input` o `ctx`.

### ERR-008 — Validación de formulario

Los problemas de campos se muestran en español y se asocian al campo cuando
corresponde. Los formularios afectados conservan el borrador y los atributos de
accesibilidad de error. Las reglas de cada campo se mantienen en el
[documento de validaciones](../../docs/control-errores-modulos.md); cualquier
cambio futuro de esas reglas debe tener su propio criterio verificable.

**Dado** un cliente con un correo rechazado por la API, **cuando** el formulario
recibe el problema asociado a `correo`, **entonces** muestra el error en ese campo
y conserva los demás valores introducidos.

### ERR-009 — Cancelación y resultado de escritura

Cancelar antes del envío produce `request_cancelled` sin enviar la solicitud y
sin marcar resultado incierto. Cancelar la espera después de invocar el transporte
de una escritura conserva ese código, marca `outcomeUnknown = true` y advierte
consultar el estado antes de repetirla. No se realiza ningún reintento automático.
La cancelación de una lectura no marca una escritura incierta.

**Dada** una escritura enviada con cuerpo pendiente, **cuando** el usuario
cancela, **entonces** recibe el aviso de cancelación con resultado incierto.

**D-01 resuelta en el diseño:** se adopta esta semántica conservadora. El código
actual todavía no la implementa; las tareas T013 y T014 siguen abiertas.

### Key Entities

- Resultado remoto: datos, estructura, identidad y confirmación de una operación.
- Error: mensaje y, cuando aplica, estado HTTP, código, campos y resultado incierto.
- Estado de la interfaz: últimos datos válidos, borrador e indicador de carga.

## Success Criteria

- **SC-001**: todos los escenarios de ERR-001 a ERR-009 tienen evidencia concreta
  o una tarea abierta; solo se declara aceptación completa cuando todos se cumplen.
- **SC-002**: ningún escenario de lectura/escritura fallida del piloto pierde el
  último estado válido ni publica un éxito ficticio.
- **SC-003**: las escrituras de los escenarios de espera agotada o cancelación
  posterior al envío realizan un único intento e informan del resultado incierto.
- **SC-004**: los errores de validación y proveedor evaluados no reflejan los
  secretos sintéticos introducidos en sus pruebas.
- **SC-005**: los flujos de progreso evaluados diferencian guardado confirmado y
  recarga fallida sin generar otro guardado.

## Assumptions

Se reutilizan autenticación, reglas y proveedores actuales. Los 30 segundos son
el valor predeterminado existente, no una garantía de rendimiento del servidor.
El piloto usa datos sintéticos y no necesita migraciones. La adopción instala y
define el proceso; los cambios funcionales pendientes quedan en `tasks.md`.

## Trazabilidad y cierre

La matriz ejecutada y sus límites están en [verification.md](verification.md).
Las pruebas existentes se reutilizan; los criterios nuevos no se declaran
satisfechos por esos resultados. El orden de trabajo está en [tasks.md](tasks.md).

La instalación y definición del proceso están completas. La aceptación del
piloto sigue abierta hasta completar T007, T009, T010, T013 y T014 y reconciliar
los resultados en T018. No se cambian API, base de datos ni lógica funcional
como parte de instalar Spec Kit. CI añade únicamente una comprobación estructural
de sus documentos.
