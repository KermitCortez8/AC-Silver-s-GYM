# Casos de uso y ECU del chatbot

Fecha: 2026-11-03. Diseño para revisión con prototipos. El chatbot productivo
todavía no está implementado. [Spec general](spec.md) · [Guía de revisión](revision-prototipos.md).

## CU-CHAT-01 · Preregistro asistido

| Elemento de la ECU | Especificación |
| --- | --- |
| Actor principal | Visitante interesado en inscribirse. |
| Actor de apoyo | Asistente del gimnasio; formulario y pasarela existentes en la implementación futura. |
| Objetivo | Comprender la oferta y completar el preregistro mediante el formulario. |
| Disparador | El visitante pregunta por planes o pulsa «Quiero registrarme». |
| Precondiciones | Acceso público; catálogo disponible para mostrar una oferta. No requiere sesión. |
| Postcondición de éxito | Solicitud de preregistro preparada para continuar al pago. Confirmar el pago y activar la cuenta son pasos posteriores distintos. |
| Postcondición de fallo | No se crea una inscripción o cuenta activa por una respuesta del chat. El visitante conserva acceso al formulario. |

**Flujo principal**

1. El visitante abre el asistente y consulta los planes.
2. El asistente muestra tarjetas con nombre, duración y precio del catálogo.
3. El visitante selecciona un plan y pulsa «Abrir preregistro».
4. El sistema abre el formulario; los datos personales se completan allí.
5. El visitante revisa los datos y continúa al pago mediante el flujo existente.
6. El sistema diferencia solicitud pendiente, pago confirmado y activación administrativa.

**Flujos alternativos**

- A1. Catálogo indisponible: mostrar mensaje de indisponibilidad y enlace al registro; no inventar planes.
- A2. Formulario incompleto o inválido: conservar valores y señalar el campo; no continuar.
- A3. Pago cancelado/pendiente: conservar la solicitud según las reglas existentes, sin anunciar activación.
- A4. IA no disponible: botones de ayuda permiten continuar por el formulario.

**Reglas:** nombre/correo máximo 50, DNI 8 dígitos, teléfono 9; mensaje del chat máximo 150 sin contador/regla visible. No introducir identidad o credenciales en la conversación.

**Trazabilidad:** US1; CA-01, CA-02, CA-07, CA-08, CA-09. Prototipos P01–P03 en [demostración](prototipos/index.html#preregistro).

## CU-CHAT-02 · Acceso asistido

| Elemento de la ECU | Especificación |
| --- | --- |
| Actor principal | Cliente que desea ingresar. |
| Actor de apoyo | Asistente y autenticación existente. |
| Objetivo | Acceder al área autorizada y entender los impedimentos del acceso. |
| Disparador | Pulsar «Ya tengo una cuenta» o preguntar cómo ingresar. |
| Precondiciones | Formulario de acceso disponible. La elegibilidad se valida en servidor en la implementación futura. |
| Postcondición de éxito | Sesión de cliente habilitado y acceso a sus propias funciones. |
| Postcondición de fallo | No se abre el área privada; se ofrece orientación sin revelar datos ajenos. |

**Flujo principal**

1. El cliente solicita ayuda para ingresar.
2. El asistente dirige al formulario de acceso.
3. El cliente usa contraseña o Google fuera del chat.
4. El sistema valida credenciales, activación y membresía pagada/vigente.
5. Si está habilitado, muestra el panel y la acción «Ver horarios».
6. Al cerrar/cambiar sesión, borra conversación, selección y respuestas pendientes.

**Flujos alternativos**

- A1. Credenciales inválidas: permitir corregirlas sin abrir sesión.
- A2. Cuenta pendiente de activación: orientar al proceso vigente sin activar desde el chat.
- A3. Membresía vencida: indicar el impedimento dentro del flujo de acceso y mantener ayuda pública genérica.
- A4. Sesión expirada durante una consulta: descartar respuesta y solicitar ingreso.

**Reglas:** el servidor identifica al cliente; el texto del chat no establece identidad o permisos. No consultar solicitudes por DNI/correo en una API pública. No enviar contraseñas al modelo.

**Trazabilidad:** US2; CA-03, CA-07, CA-09. Prototipos P04–P06 en [demostración](prototipos/index.html#acceso).

## CU-CHAT-03 · Consulta y matrícula asistida en horarios

| Elemento de la ECU | Especificación |
| --- | --- |
| Actor principal | Cliente autenticado y habilitado. |
| Actor de apoyo | Asistente, consulta de sesiones y servicio de matrícula existente. |
| Objetivo | Encontrar una sesión e inscribirse con confirmación explícita. |
| Disparador | Preguntar por una clase o pulsar «Buscar horarios». |
| Precondiciones | Cuenta habilitada, membresía vigente y fecha/servicio seleccionados. |
| Postcondición de éxito | Una matrícula verificada para cliente, horario y fecha concretos; actualiza Mi horario. |
| Postcondición de fallo | No se anuncia inscripción ni se reintenta una escritura cuyo resultado se desconoce. |

**Flujo principal**

1. El asistente solicita servicio y fecha cuando falten.
2. El sistema consulta sesiones y muestra datos del backend en tarjetas.
3. El cliente selecciona una sesión; buscar o seleccionar no reserva cupo.
4. El sistema presenta servicio, fecha absoluta y hora para revisar.
5. El cliente pulsa «Confirmar matrícula».
6. El servidor vuelve a validar identidad, vigencia, duplicidad y cupo con la operación existente.
7. Solo con resultado verificado se muestra éxito y se actualiza Mi horario.

**Flujos alternativos**

- A1. Sin fecha/servicio o búsqueda ambigua: pedir precisión.
- A2. Cupo ocupado entre consulta y confirmación: mostrar rechazo y volver a horarios.
- A3. Doble clic: bloquear el envío en curso; conservar deduplicación de servidor.
- A4. Respuesta perdida: marcar resultado sin verificar y consultar inscripciones propias antes de ofrecer reintento.
- A5. Sesión vencida o fecha fuera de vigencia: rechazar la acción y dirigir al flujo correspondiente.

**Reglas:** fechas de negocio America/Lima; confirmación separada del texto de IA; el modelo solo consulta y propone. No hay matrícula autónoma, cobro o activación.

**Trazabilidad:** US3; CA-04, CA-05, CA-06, CA-07, CA-09. Prototipos P07–P10 en [demostración](prototipos/index.html#matricula).

## Qué demuestra la revisión

El prototipo permite revisar pantallas, navegación y respuestas simuladas ante
escenarios. No demuestra autenticación, pago, control de cupos en servidor,
cuotas distribuidas, privacidad del proveedor o comprensión real mediante IA.
Esos criterios siguen requiriendo implementación y pruebas del producto.
