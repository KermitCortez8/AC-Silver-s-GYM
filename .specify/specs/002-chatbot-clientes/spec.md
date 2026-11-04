# Chatbot para acompañar el recorrido del cliente

**ID:** `002-chatbot-clientes` · **Fecha:** 2026-11-03 · **Estado:** Specs y prototipos; integración productiva pendiente.
**Petición:** conversación con IA y acciones guiadas con reglas, desde preregistro y acceso hasta horarios y matrícula.
**Contexto:** [análisis de la base](context.md). Contratos afectados: MOD-01 a MOD-05, enlazados allí.

## 1. Sprint Goal

Un asistente en español entiende mensajes libres sobre el gimnasio y acompaña los formularios y acciones existentes. La IA orienta y propone; las reglas del servidor deciden el acceso y la validez de los datos. Una matrícula requiere confirmación explícita en pantalla.

Este documento define el comportamiento del producto futuro. La entrega actual
incluye el plan, las [ECU de los tres casos de uso](casos-de-uso.md) y los
[prototipos para revisión conjunta](revision-prototipos.md). La demostración usa
datos y respuestas fijos, sin conexión a IA, autenticación, pagos o matrículas reales.

## 2. User Story

### US1 · Orientarme y preregistrarme (Priority: P1)

Como visitante, quiero preguntar por planes y cómo registrarme para completar el preregistro y continuar al pago en los formularios existentes.

**Prueba independiente:** sin sesión, consultar el catálogo, abrir registro con un plan válido y recibir orientación sobre pago/activación sin consultar datos privados.

**Escenarios:** se muestran planes vigentes reales; una solicitud de datos de otra persona se rechaza ofreciendo ayuda permitida.

### US2 · Ingresar y continuar con seguridad (Priority: P1)

Como cliente, quiero ayuda para ingresar y continuar mi recorrido, entendiendo qué hacer si mi cuenta espera activación o mi sesión expiró.

**Prueba independiente:** abrir acceso desde el chat y autenticar en el formulario; cerrar/cambiar sesión borra conversación, propuestas y respuestas pendientes.

**Escenarios:** el cliente habilitado accede a sus propias acciones; uno pendiente/vencido recibe orientación pública sin saltar controles ni revelar su estado privado a visitantes.

### US3 · Consultar horarios y matricularme (Priority: P2)

Como cliente habilitado, quiero buscar una clase y confirmar mi inscripción para matricularme en una fecha concreta con cupo disponible.

**Prueba independiente:** buscar una sesión, revisar el resumen, pulsar Confirmar matrícula y verificar la inscripción en Mi horario.

**Escenarios:** buscar no inscribe; un cupo agotado antes de confirmar produce rechazo del servidor; doble clic no crea dos matrículas.

## 3. Acceptance Criteria

1. **CA-01.** El panel acepta mensajes libres en español, muestra carga/error y propone solo acciones de una lista cerrada; una salida inválida del modelo no produce acciones.
2. **CA-02.** En modo público se usan ayuda aprobada y catálogos públicos actuales; registro abre el formulario existente conservando límites y flujo de pago/activación.
3. **CA-03.** El acceso usa los mecanismos existentes; las consultas privadas exigen sesión habilitada y cliente propio. Logout, cambio de usuario o expiración elimina memoria y descarta respuestas tardías.
4. **CA-04.** Para proponer matrícula se exige fecha concreta; las fechas relativas se interpretan en America/Lima y los datos de horarios provienen del backend. Buscar no reserva cupo.
5. **CA-05.** Solo el botón de confirmación sobre un resumen de servicio, fecha y hora envía matrícula. El servidor determina el cliente y revalida vigencia, horario, duplicidad y cupo mediante la operación existente.
6. **CA-06.** Se bloquean envíos repetidos en curso; un resultado incierto obliga a consultar inscripciones antes de ofrecer reintento. No se anuncia éxito sin matrícula verificada.
7. **CA-07.** Prompts, respuestas y acciones sugeridas no amplían permisos ni ejecutan SQL/URLs arbitrarias, cobros, activaciones o consultas ajenas. No se adjuntan al proveedor campos estructurados de identidad/pago ni secretos; se filtra texto libre y una entrada sensible detectada se resuelve localmente. No se registran mensajes, argumentos privados o secretos en logs.
8. **CA-08.** Mensaje máximo de 150 caracteres limitado al escribir/pegar y validado en servidor; existen límites compartidos de frecuencia/presupuesto, timeout y apagado del proveedor con alternativa guiada.
9. **CA-09.** El panel funciona en móvil/escritorio con teclado, conserva los formularios utilizables si la IA falla y tiene pruebas reproducibles sin llamadas externas.

| Criterio | Evidencia prevista; todavía no ejecutada |
| --- | --- |
| CA-01 | [Escenario E1](quickstart.md#e1-conversación-y-esquema) |
| CA-02 | [Escenario E2](quickstart.md#e2-preregistro-y-acceso) |
| CA-03 | [Escenario E3](quickstart.md#e3-identidad-y-limpieza) |
| CA-04 | [Escenario E4](quickstart.md#e4-horarios-y-fechas) |
| CA-05 | [Escenario E5](quickstart.md#e5-matrícula-confirmada) |
| CA-06 | [Escenario E6](quickstart.md#e6-concurrencia-y-resultado-incierto) |
| CA-07 | [Escenario E7](quickstart.md#e7-abuso-y-privacidad) |
| CA-08 | [Escenario E8](quickstart.md#e8-límites-y-caída-del-proveedor) |
| CA-09 | [Escenario E9](quickstart.md#e9-accesibilidad-y-regresión) |

### Functional Requirements

- **FR-001:** conversación con salida estructurada y acciones permitidas (CA-01, CA-07).
- **FR-002:** orientación pública con datos reales y navegación al preregistro/acceso (CA-02).
- **FR-003:** identidad del servidor y memoria aislada por sesión (CA-03).
- **FR-004:** consulta por fecha y matrícula confirmada (CA-04, CA-05, CA-06).
- **FR-005:** límites, privacidad y funcionamiento degradado (CA-07, CA-08, CA-09).

### Key Entities

Turno efímero, acción validada, selección de sesión y cuota técnica compartida. No se crean otras entidades de cliente, pago o matrícula. Detalles en [modelo](data-model.md).

### Measurable Outcomes

Los nueve escenarios pasan con proveedor falso, sin pagos/correos reales. Cero escrituras de negocio desde herramientas del modelo y cero consultas privadas con identidad tomada del texto. Todas las matrículas propuestas necesitan confirmación y resultado verificable del backend.

### Revisión del diseño con prototipos

US1 corresponde a CU-CHAT-01 / P01–P03; US2 a CU-CHAT-02 / P04–P06;
US3 a CU-CHAT-03 / P07–P10. El [prototipo navegable](prototipos/index.html)
muestra la Spec resumida junto a cada recorrido. La [matriz de revisión](revision-prototipos.md)
relaciona cada pantalla con sus CA. Validar el prototipo no acredita los criterios
que requieren servidor, proveedor o concurrencia reales.
La [relación con las cinco tareas de programación](programacion-prototipos.md)
identifica reglas, IA, interfaz y conexiones con los servicios actuales. La barra
de programación del prototipo muestra las tareas que corresponden a cada recorrido.

## 4. Technical Constraints

Conservar Vue/Pinia y FastAPI/Supabase, capas e inyección de adaptadores. Separar endpoints público/privado, herramientas de lectura y confirmación humana. La IA es una integración backend; sus claves nunca son `VITE_*`. Reutilizar la RPC de matrícula y los flujos de identidad, preregistro y pagos.

Memoria conversacional efímera. Cuotas en almacenamiento compartido con actualización atómica y acceso exclusivo del backend. Integración habilitada por configuración tras elegir proveedor/modelo y presupuesto. Sin entrenamiento, embeddings o base vectorial en este alcance.

## 5. Guardrails

Solo preregistro, acceso, planes/promociones, horarios e inscripción propia. Preguntas ajenas reciben redirección breve a esos temas. Fuera: administración, consejos médicos, tienda, cambios de membresía, cancelaciones y envío de notificaciones desde el chat.

No adjuntar al modelo campos de DNI, teléfono, correo, nombres personales, contraseñas, tokens, checkout IDs o tarjetas. Filtrar patrones sensibles en texto libre y resolver localmente entradas detectadas o sospechosas, dirigiendo al formulario. No prometer anonimización infalible del texto; limitación explícita en [decisiones](research.md). La aplicación muestra datos privados y confirmaciones fuera de la prosa generada.

No consultar preregistros por DNI/correo mediante API pública ni prometer activación al pagar. No contratar servicios, activar claves, desplegar o ejecutar transacciones reales durante la planificación.

## 6. Edge Cases

| Caso | Respuesta prevista | Criterio |
| --- | --- | --- |
| Mensaje vacío/excesivo o instrucciones para saltar reglas | Validar esquema y alcance; sin ejecución | CA-01, CA-07, CA-08 |
| Catálogo caído o promoción agotada | Informar indisponibilidad; no inventar oferta | CA-02 |
| Sesión vencida durante respuesta | Descartar respuesta/propuesta y abrir acceso | CA-03 |
| «Mañana» cerca de medianoche o servicio ambiguo | Reloj Lima; pedir precisión cuando falte | CA-04 |
| Propuesta antigua o cupo ocupado | Recargar datos y revalidar al confirmar | CA-05 |
| Doble clic, dos pestañas o pérdida de red | Bloquear/reconciliar y deduplicar en backend | CA-06 |
| Enlace externo o ID inventado por IA | Rechazar salida y no habilitar acción | CA-07 |
| Cuota agotada o proveedor caído | Ayuda guiada y enlaces originales | CA-08, CA-09 |

### Assumptions

Primera versión web en español para visitantes/clientes; sin WhatsApp, voz o historial persistente. Los límites operativos del plan son valores iniciales configurables. Proveedor/modelo y presupuesto se concretan en T001 antes de habilitar la integración. Se conservan las reglas actuales de activación y membresía.

## 7. Definition of Done

- [ ] CA-01 a CA-09 pasan y enlazan evidencia ejecutada.
- [ ] Implementación, pruebas y contratos vivos están completos.
- [ ] Se verifica UI, permisos, concurrencia y límites compartidos.
- [ ] Logs sin mensajes/secretos; proveedor sin campos privados estructurados y filtros de texto verificados con datos centinela.
- [ ] La falta de IA conserva la guía y los formularios originales.
