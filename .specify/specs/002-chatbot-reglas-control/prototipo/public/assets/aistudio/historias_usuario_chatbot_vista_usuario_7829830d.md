# Historias de Usuario del Chatbot: Prototipo Vista Usuario (Principal / Cliente)

**Proyecto:** Sistema Web de Gestión Administrativa y Control de Clientes para Silver Gym Surco (SWGACSGYM)
**Módulo:** Chatbot (widget web con IA generativa)
**Versión:** 1.2 | **Fecha:** 05/11/2026

---

## 0. Alcance de este documento

Este documento cubre **solo el prototipo de la vista usuario**: las historias que funcionan igual para cualquier persona, con o sin sesión (alcance **Principal / Cliente**).

**Quedan fuera** (pertenecen al prototipo de la vista cliente, con sesión iniciada):

| Historia fuera de alcance | Motivo |
|---|---|
| HU-CB05 Consultar estado de mi membresía | Exclusiva del cliente |
| HU-CB06 Inscribirme en una actividad | Exclusiva del cliente |
| HU-CB07 Consultar y cancelar mis inscripciones | Exclusiva del cliente |
| HU-CB08 Agregar productos al carrito y generar solicitud de compra | Exclusiva del cliente |
| HU-CB09 Consultar estado de mi pedido | Exclusiva del cliente |
| HU-CB12 Privacidad de datos personales | Alcance "Cliente" en la tabla original |
| HU-CB04B Consultar productos (información detallada) | Detalle exclusivo del cliente |

**Corrección del comentario de Dennis sobre HU-CB04** (resuelto por Rodrigo): *"Debería ser para cliente. O dar una info general de los productos y ya en clientes los productos más detallados."*
En este prototipo, **HU-CB04 queda como información general** (nombre, categoría, imagen y disponibilidad). El detalle (precio, stock exacto, descripción y carrito) se desarrolla aparte para la vista cliente.

---

## 1. Contexto

- El chatbot es un **widget dentro de la web**. No existe en otros canales.
- Responde con **IA generativa (LLM)**. Las acciones las ejecuta el backend (FastAPI), nunca el modelo directamente.
- En esta vista el chatbot **solo informa y deriva**: no modifica datos de nadie.
- Administrador, recepcionista y entrenador **no usan el chatbot**.

---

## 2. Tecnología del frontend

| Aspecto | Definición |
|---|---|
| **Lenguaje** | **TypeScript** (compila a JavaScript), más HTML5 y CSS |
| **Framework en Google AI Studio** | **React** con TypeScript, que es lo que AI Studio suele generar. Confírmalo al abrir el proyecto. |
| **Framework de la arquitectura** | **Vue 3** (según el Documento de Arquitectura). Ver nota. |
| **Estilos** | Tailwind CSS |
| **Tipografías** | Oswald (títulos, etiquetas y botones, igual que la web) e Inter (texto) |
| **Backend** | API REST con JSON (FastAPI). En esta fase, datos simulados con `MockChatService` |

**Nota sobre React y Vue:** si AI Studio entrega React, el contrato de datos y la estructura de componentes se conservan, y migrar a Vue 3 consiste en reescribir las plantillas. Conviene avisar al equipo y decidir si el widget se integra como componente Vue o se monta aparte.

**Contrato de datos (TypeScript), reducido a este alcance:**

```ts
type ChatState =
  | 'ok' | 'rate_limited' | 'slow'
  | 'basic_mode' | 'session_expired' | 'forbidden';

type Block =
  | { type: 'text'; text: string }
  | { type: 'schedule_list'; items: ScheduleItem[] }          // HU-CB03
  | { type: 'product_basic_list'; items: ProductBasic[] }     // HU-CB04
  | { type: 'contact'; phone: string; whatsappUrl: string; attentionHours: string } // HU-CB10
  | { type: 'notice'; kind: 'rate_limit' | 'basic_mode' | 'session_expired'; text: string; retryInSeconds?: number };

interface ScheduleItem  { id: string; service: string; day: string; start: string; end: string; slotsLeft: number }
interface ProductBasic  { id: string; name: string; category: string; imageUrl?: string; available: boolean }

interface ChatResponse {
  blocks: Block[];
  quickReplies: { label: string; action: string }[];
  state: ChatState;
}
```

---

## 3. Resumen

| ID | Historia | Contexto | Prioridad | Depende de |
|---|---|---|---|---|
| HU-CB01 | Consultar horario de apertura y cierre | Principal / Cliente | Must | HU-CB11, HU-CB17 |
| HU-CB02 | Consultar horario de atención | Principal / Cliente | Must | HU-CB01 |
| HU-CB03 | Consultar horarios y cupos de actividades | Principal / Cliente | Must | HU-CB11 |
| HU-CB04 | Consultar productos de la tienda (información general) | Principal / Cliente | Must | HU-CB11 |
| HU-CB10 | Derivar a un número de contacto | Principal / Cliente | Must | HU-CB02 |
| HU-CB11 | Permisos según vista y sesión | Principal / Cliente | Must | Ninguna |
| HU-CB13 | Lista cerrada de acciones permitidas | Principal / Cliente | Must | HU-CB11 |
| HU-CB14 | Límite de mensajes y frecuencia | Principal / Cliente | Should | Ninguna |
| HU-CB15 | Presupuesto de uso del LLM (modo básico) | Principal / Cliente | Should | HU-CB14 |
| HU-CB16 | Tiempos de espera y expiración | Principal / Cliente | Should | HU-CB10 |
| HU-CB17 | Protección ante manipulación del modelo | Principal / Cliente | Must | HU-CB11, HU-CB13 |

**Orden sugerido de implementación:** HU-CB11 → HU-CB17 → HU-CB13 → HU-CB01 → HU-CB02 → HU-CB03 → HU-CB04 → HU-CB10 → HU-CB14 → HU-CB16 → HU-CB15.

---

## 4. Historias de usuario

### HU-CB01: Consultar horario de apertura y cierre
**Como** usuario de la vista principal o cliente, **quiero** consultar el horario de apertura y cierre del gimnasio, **para** saber cuándo puedo asistir.
**Prioridad:** Must | **Depende de:** HU-CB11, HU-CB17

- **Escenario 1: Consulta normal.** **Dado** que el usuario está en cualquier vista, **cuando** pregunta por el horario de apertura o cierre, **entonces** el chatbot responde con los días y las horas vigentes.
- **Escenario 2: Feriado o cierre especial.** **Dado** que hay un cierre especial configurado para la fecha consultada, **cuando** el usuario pregunta, **entonces** el chatbot lo indica junto al horario habitual.
- **Escenario 3: Sin datos configurados.** **Dado** que no hay horario configurado, **cuando** el usuario pregunta, **entonces** el chatbot informa que no tiene la información y ofrece el contacto (HU-CB10), sin inventar horas.

### HU-CB02: Consultar horario de atención
**Como** usuario de la vista principal o cliente, **quiero** conocer el horario de atención de recepción y administración, **para** saber cuándo puedo hacer trámites.
**Prioridad:** Must | **Depende de:** HU-CB01

- **Escenario 1: Distinción de horarios.** **Dado** que el usuario pregunta por atención o trámites, **cuando** el chatbot responde, **entonces** diferencia el horario de atención del horario de apertura del gimnasio.
- **Escenario 2: Fuera de horario.** **Dado** que la consulta se hace fuera del horario de atención, **cuando** el chatbot responde, **entonces** informa que no hay atención en ese momento y cuándo se reanuda.

### HU-CB03: Consultar horarios y cupos de actividades
**Como** usuario de la vista principal o cliente, **quiero** ver los horarios de cada actividad con sus cupos disponibles, **para** elegir cuál me conviene.
**Prioridad:** Must | **Depende de:** HU-CB11

- **Escenario 1: Filtros.** **Dado** que el usuario pide los horarios de una actividad, **cuando** el chatbot responde, **entonces** muestra día, hora de inicio, hora de fin y cupos disponibles, y permite filtrar por actividad y día.
- **Escenario 2: Horario completo.** **Dado** que un horario no tiene cupos, **cuando** se muestra, **entonces** aparece como "Completo".
- **Escenario 3: Consulta sobre inscripción.** **Dado** que el usuario pregunta cómo inscribirse, **cuando** el chatbot responde, **entonces** le indica que la inscripción se hace con la sesión iniciada o con el personal de recepción, y ofrece el contacto (HU-CB10).

### HU-CB04: Consultar productos de la tienda (información general)
**Como** usuario de la vista principal o cliente, **quiero** ver qué productos ofrece la tienda del gimnasio, **para** saber qué hay antes de decidir comprar.
**Prioridad:** Must | **Depende de:** HU-CB11

- **Escenario 1: Información general.** **Dado** que el usuario pregunta por productos, **cuando** el chatbot responde, **entonces** muestra solo nombre, categoría, imagen y disponibilidad (Disponible o Agotado).
- **Escenario 2: Datos reservados.** **Dado** que el usuario pide precio, stock exacto o descripción, **cuando** el chatbot responde, **entonces** indica que ese detalle se consulta con la sesión iniciada o en recepción, sin revelarlo.
- **Escenario 3: Producto agotado.** **Dado** que un producto no tiene stock, **cuando** se muestra, **entonces** aparece como "Agotado".
- **Escenario 4: Producto inexistente.** **Dado** que el producto consultado no existe, **cuando** el usuario pregunta, **entonces** el chatbot lo informa y no inventa productos.

### HU-CB10: Derivar a un número de contacto
**Como** usuario de la vista principal o cliente, **quiero** que el chatbot me derive a un número de contacto cuando no pueda resolver mi consulta, **para** recibir atención personalizada.
**Prioridad:** Must | **Depende de:** HU-CB02

- **Escenario 1: Solicitud del usuario.** **Dado** que el usuario pide hablar con una persona, **cuando** el chatbot responde, **entonces** muestra el número de contacto del gimnasio.
- **Escenario 2: Consulta no resuelta.** **Dado** que el chatbot no entiende la consulta tras un número configurable de intentos (ej. 2), **cuando** vuelve a fallar, **entonces** ofrece el contacto de forma proactiva.
- **Escenario 3: Fuera de horario.** **Dado** que es fuera del horario de atención, **cuando** deriva, **entonces** muestra el número e indica cuándo será atendido.
- **Escenario 4: Registro.** **Dado** que ocurre una derivación, **cuando** se completa, **entonces** se registra el motivo (solicitud del usuario, no entendido, acción no permitida, fuera de alcance).

### HU-CB11: Permisos según vista y sesión
**Como** administrador del gimnasio, **quiero** que el chatbot aplique permisos según la vista y la sesión, **para** que nadie acceda a información que no le corresponde.
**Prioridad:** Must | **Depende de:** ninguna

- **Escenario 1: Contenido público.** **Dado** que no hay sesión, **cuando** el usuario consulta, **entonces** el chatbot solo ofrece contenido público (HU-CB01, HU-CB02, HU-CB03, HU-CB04 y HU-CB10).
- **Escenario 2: Información personal.** **Dado** que el usuario pide información personal (membresía, inscripciones, pedidos), **cuando** el chatbot evalúa, **entonces** le indica que debe iniciar sesión y no entrega ningún dato.
- **Escenario 3: Datos de terceros.** **Dado** que alguien pide datos de otro cliente (por DNI, nombre o ID), **cuando** el chatbot valida, **entonces** rechaza, no confirma si esa persona existe y registra el intento.
- **Escenario 4: Sesión expirada.** **Dado** que el token expiró durante la conversación, **cuando** el usuario intenta algo que requiere sesión, **entonces** el chatbot pide iniciar sesión de nuevo.

### HU-CB13: Lista cerrada de acciones permitidas
**Como** administrador del gimnasio, **quiero** definir una lista cerrada de acciones que el chatbot puede ejecutar, **para** evitar acciones no autorizadas.
**Prioridad:** Must | **Depende de:** HU-CB11

- **Escenario 1: Acciones permitidas.** **Dado** un usuario en la vista, **cuando** pide una acción, **entonces** el chatbot solo ejecuta: consultar información pública y derivar a un contacto.
- **Escenario 2: Acciones prohibidas.** **Dado** que se pide eliminar o modificar datos, confirmar pagos, activar o congelar membresías, cambiar precios o editar datos de otros clientes, **cuando** el chatbot evalúa, **entonces** rechaza, explica que debe gestionarlo el personal y ofrece HU-CB10.
- **Escenario 3: Doble verificación en el backend.** **Dado** que el modelo solicita una acción, **cuando** llega al backend, **entonces** este valida que la acción esté en la lista permitida, aunque el modelo la haya aprobado.

### HU-CB14: Límite de mensajes y frecuencia
**Como** administrador del gimnasio, **quiero** limitar la cantidad y frecuencia de mensajes por usuario, **para** prevenir abuso y spam.
**Prioridad:** Should | **Depende de:** ninguna

- **Escenario 1: Límite por minuto y por día.** **Dado** un máximo configurado (ej. 10 por minuto y 100 por día), **cuando** el usuario lo supera, **entonces** el chatbot no procesa el mensaje, bloquea el campo de texto y muestra el tiempo restante.
- **Escenario 2: Longitud máxima.** **Dado** un límite de longitud por mensaje, **cuando** se supera, **entonces** el chatbot pide acortar el mensaje.
- **Escenario 3: Visitantes.** **Dado** que el visitante no tiene identidad, **cuando** se aplica el límite, **entonces** se controla por sesión o IP con un límite más estricto que el del cliente.

### HU-CB15: Presupuesto de uso del LLM
**Como** administrador del gimnasio, **quiero** definir un presupuesto máximo de consumo del modelo, **para** controlar los costos.
**Prioridad:** Should | **Depende de:** HU-CB14

- **Escenario 1: Configuración.** **Dado** un tope diario o mensual de tokens o costo, **cuando** se guarda, **entonces** el chatbot lo aplica a todas las conversaciones.
- **Escenario 2: Alerta al 80%.** **Dado** que se alcanza el 80%, **cuando** se detecta, **entonces** se notifica al administrador.
- **Escenario 3: Tope al 100%.** **Dado** que se alcanza el 100%, **cuando** llega un mensaje, **entonces** el chatbot pasa a **modo básico** (opciones rápidas y derivación) sin llamar al modelo.
- **Escenario 4: Límite por usuario.** **Dado** un tope por usuario, **cuando** un usuario lo alcanza, **entonces** solo ese usuario pasa a modo básico.

### HU-CB16: Tiempos de espera y expiración
**Como** usuario de la vista principal o cliente, **quiero** recibir una respuesta o un aviso en un tiempo acotado, **para** no quedar esperando indefinidamente.
**Prioridad:** Should | **Depende de:** HU-CB10

- **Escenario 1: Tiempo de respuesta.** **Dado** que el modelo no responde dentro de un tiempo configurable (ej. 15 s), **cuando** se agota, **entonces** el chatbot muestra un mensaje de reintento y ofrece el contacto.
- **Escenario 2: Inactividad.** **Dado** que el chat está inactivo por un tiempo configurable, **cuando** expira, **entonces** se cierra la conversación y, si el usuario tenía sesión y el token venció, se pide iniciar sesión.

### HU-CB17: Protección ante manipulación del modelo
**Como** administrador del gimnasio, **quiero** que el chatbot resista intentos de manipular sus instrucciones, **para** que no revele información interna ni ejecute acciones no autorizadas.
**Prioridad:** Must | **Depende de:** HU-CB11, HU-CB13

- **Escenario 1: Instrucciones internas.** **Dado** que el usuario pide ver o ignorar las instrucciones del sistema, **cuando** el chatbot responde, **entonces** se niega y vuelve a su función.
- **Escenario 2: Suplantación de rol.** **Dado** que el usuario afirma ser administrador o recepcionista, **cuando** el chatbot evalúa, **entonces** no cambia sus permisos, porque dependen solo de la sesión autenticada.
- **Escenario 3: Fuera de alcance.** **Dado** que el usuario pregunta algo ajeno al gimnasio, **cuando** el chatbot responde, **entonces** indica que solo atiende consultas del gimnasio.
- **Escenario 4: Contenido ofensivo.** **Dado** que el usuario envía lenguaje ofensivo, **cuando** el chatbot responde, **entonces** mantiene un tono respetuoso y, si persiste, ofrece el contacto.

---

## 5. Cómo aporta cada historia al prototipo

| Historia | Opción rápida o estado | Componente del prototipo |
|---|---|---|
| HU-CB01 | "Horario del gimnasio" | `BotMessage` con tarjeta de horarios |
| HU-CB02 | "Horario de atención" | `BotMessage` con horario de atención |
| HU-CB03 | "Actividades y cupos" | `ScheduleCard` (informativa, con etiqueta Completo, sin botón de inscribirse) |
| HU-CB04 | "Productos de la tienda" | `ProductCardBasic` (nombre, categoría, imagen, disponibilidad) |
| HU-CB10 | "Hablar con una persona" | `ContactCard` (WhatsApp y horario de atención) |
| HU-CB11 | Estado A y E | Rechazo de datos personales y tarjeta de sesión expirada |
| HU-CB13 | Estado A (Restringido) | Respuesta de acción no permitida con `ContactCard` |
| HU-CB14 | Estado B (Límite) | `NoticeBanner` con cuenta regresiva y campo de texto bloqueado |
| HU-CB15 | Estado D (Modo básico) | `NoticeBanner` "Asistente en modo básico" con opciones rápidas |
| HU-CB16 | Estado C (Demora) | `TypingIndicator` y mensaje con "Reintentar" y "Hablar con una persona" |
| HU-CB17 | Transversal | Respuestas de rechazo con `BotMessage` |

**Opciones rápidas de este prototipo (5):** Horario del gimnasio, Horario de atención, Actividades y cupos, Productos de la tienda, Hablar con una persona.

---

## 6. Prompt de ajuste para Google AI Studio

Pégalo en el proyecto del prototipo para recortarlo a este alcance:

```
Ajusta el prototipo del chatbot de Silver Gym Surco para que cubra SOLO la "vista usuario": lo que puede usar cualquier persona, con o sin sesión. Todo en TypeScript. No cambies el estilo visual existente.

ALCANCE
- Mantén solo estas 5 opciones rápidas: "Horario del gimnasio", "Horario de atención", "Actividades y cupos", "Productos de la tienda", "Hablar con una persona".
- Elimina o desactiva todo lo exclusivo del cliente: MembershipCard, "Mi membresía", "Inscribirme en una actividad", "Mis inscripciones", "Ver tienda y carrito", "Estado de mi pedido", ConfirmationCard, SuccessCard de inscripción, carrito y pedidos. Esas pantallas se harán en otro prototipo.
- El encabezado muestra siempre "Silver" y el subtítulo "Asistente virtual con IA" (sin "Hola, Juan").
- Conserva el aviso discreto "Inicia sesión para consultar tu membresía e inscribirte • Iniciar sesión".

CAMBIOS EN TARJETAS
- ScheduleCard: informativa. Quita el botón "Seleccionar" y muestra solo actividad, día, hora, cupos y la etiqueta "Completo" cuando no hay cupos. Si el usuario pregunta cómo inscribirse, el bot responde que se hace con la sesión iniciada o con recepción y muestra el botón de contacto.
- ProductCardBasic: imagen, nombre, categoría y etiqueta "Disponible" (verde) o "Agotado" (gris). Sin precio, sin descripción y sin stock exacto. Si el usuario pide esos datos, el bot indica que se consultan con la sesión iniciada o en recepción.

ESTADOS ESPECIALES (mismo panel y estilo que el resto, sin marco de celular ni barra de estado)
A) Acción no permitida o dato personal: mensaje del bot más ContactCard con botón "Abrir WhatsApp".
B) Límite de mensajes: aviso con cuenta regresiva y campo de texto bloqueado.
C) Demora de más de 15 s: "Está tardando más de lo normal…" con botones Reintentar y Hablar con una persona.
D) Modo básico: franja gris "Asistente en modo básico" con las 5 opciones rápidas y el botón de contacto.
E) Sesión expirada: tarjeta con botón "Iniciar sesión".

CONTRATO DE DATOS
- Reduce Block a: text, schedule_list, product_basic_list, contact y notice. Reduce ChatState a: ok, rate_limited, slow, basic_mode, session_expired y forbidden.
- MockChatService mantiene latencia simulada de 600 a 1200 ms y datos coherentes con la web: horario "Lunes a Sábado" (sin domingos).
- Conserva DEMO_MODE para forzar cada estado especial.

Mantén accesibilidad WCAG 2.1 AA, objetivos táctiles de al menos 44 px y diseño responsive de 360 a 1440 px.
```

---

## 7. Decisiones pendientes

| # | Tema | Propuesta actual | A confirmar con |
|---|---|---|---|
| 1 | ¿El **precio** de los productos es público? | No: queda como detalle para la vista cliente | Equipo y administración del gimnasio |
| 2 | ¿Qué incluye la "info general" de productos? | Nombre, categoría, imagen y disponibilidad | Dennis y Rodrigo |
| 3 | Framework del frontend | React si AI Studio lo genera; la arquitectura define Vue 3 | Equipo |
| 4 | HU-CB12 (privacidad) | Fuera de este prototipo por ser alcance "Cliente" | Equipo |
| 5 | Valores configurables | Horarios, número de contacto, límites de mensajes, presupuesto y tiempos de espera | Gimnasio |
