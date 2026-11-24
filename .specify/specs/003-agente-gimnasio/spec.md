# Agente de atención del gimnasio · alcance verificable de v1

**ID:** `003-agente-gimnasio` · **Implementación:** `levano/agenteAgente.v1` · **Pruebas:** `levano/agenteAgente.v1-pruebas` · **Revisión:** 2026-11-19.
**Estado:** implementado en estas ramas, todavía no integrado en `develop`. La batería automatizada usa dobles de prueba; hay una prueba Playwright de lectura del catálogo real de Supabase y una comprobación manual previa de Groq. No se ha certificado un despliegue público.
**Fuentes:** [contexto](context.md), [contrato HTTP](contracts/agente-publico.md), [batería](qa-v1-bateria.md) y [validación](validation.md).

## 1. Sprint Goal

Un visitante pregunta en español por planes, clases e información pública del gimnasio. El backend consulta catálogos actuales o fichas públicas revisadas y compone la respuesta factual. El modelo solo selecciona una herramienta permitida cuando la consulta lo necesita. La v1 debe orientar sin inventar precios u horarios, revelar datos privados, cobrar o crear registros.

## 2. User Story

### US1 · Consultar planes y clases (P1)

Como visitante, quiero preguntar por planes o clases para decidir si me registro o consulto un horario.

**Prueba independiente:** con catálogos de prueba conocidos, preguntar por un plan y una clase; comprobar que las respuestas corresponden a los datos consultados y permiten abrir la pantalla pública pertinente.

1. Dado un plan público, cuando pregunto por él, entonces recibo su nombre, precio y duración actuales.
2. Dada una clase activa, cuando pregunto por horarios, entonces recibo los horarios publicados.
3. Dado un catálogo vacío o no disponible, cuando pregunto, entonces el agente reconoce que no puede confirmar la información.

### US2 · Conversar y pedir ayuda sin operaciones privadas (P1)

Como visitante, quiero recibir orientación sin que el agente revele datos privados o ejecute operaciones que requieren identificación y confirmación.

**Prueba independiente:** pedir una matrícula, un cobro o datos de otro cliente; comprobar que no hay escritura ni revelación de información privada. Saludar, agradecer y preguntar algo claramente ajeno al gimnasio; comprobar la respuesta y el límite de la conversación.

### US3 · Entender el registro y preparar una recuperación (P1)

Como visitante, quiero saber cómo registrarme y qué hacer si no puedo entrar a mi cuenta, sin compartir mis datos personales en el chat público.

**Prueba independiente:** pedir instrucciones de registro y verificar el enlace a `/registro`; pedir recuperación y comprobar que correo, DNI y teléfono quedan solo en el navegador y no se envían al backend ni al dueño.

## 3. Acceptance Criteria

1. **CA-01.** Planes. Si hay planes públicos, una pregunta por ellos devuelve nombre, precio y duración obtenidos de `GymService`, más un enlace a Registro. Al cambiar el catálogo, cambia la respuesta; no hay precios fijos en el prompt.
2. **CA-02.** Horarios y hechos. Una pregunta explícita por horarios del gimnasio consulta las clases públicas activas, sin depender de que Groq elija una herramienta. Se muestran los horarios actuales por actividad; si se pide una actividad concreta, se filtran las demás. Si no hay horarios para ella, no se inventan. El modelo no aporta cifras ni redacta la respuesta factual: el backend la arma desde el resultado consultado.
3. **CA-03.** Operaciones privadas. Pedir matrícula, cobro, cancelación, activación o datos de otra persona no ejecuta la operación ni consulta datos privados; se orienta al visitante hacia los controles de la plataforma.
4. **CA-04.** Fallos y ausencia de datos. Si Groq falla o no selecciona una herramienta, el agente consulta el catálogo público para preguntas reconocibles sobre planes u horarios. Un catálogo vacío devuelve una respuesta sin cifras inventadas. La API informa indisponibilidad cuando falla el catálogo o falta una consulta de respaldo.
5. **CA-05.** Datos sensibles. El chat intercepta los patrones probados de correo, DNI, teléfono, contraseña y tarjeta antes de llamar al proveedor; el formulario de recuperación no incorpora esos datos al historial ni al mensaje HTTP. Esta protección requiere una revisión adicional para datos personales no cubiertos por los patrones actuales.
6. **CA-06.** Herramientas cerradas. Un mensaje del usuario no puede cambiar permisos. El backend valida nombre y argumentos de la herramienta elegida por el modelo; rechaza una operación, tema o intención no permitidos sin ejecutarlos.
7. **CA-07.** Contexto mínimo. Cada conversación recibe un identificador opaco y conserva solo el tema público reciente durante 30 minutos en memoria del proceso. Dos identificadores no comparten ese tema; no se guarda el texto completo de la conversación en el backend.
8. **CA-08.** Prueba repetible. Los casos normales, de error y de abuso se ejecutan con proveedor y catálogo controlados sin pagos, correos ni llamadas reales. Una prueba opcional y separada compara el horario mostrado con la lectura pública actual de Supabase.
9. **CA-09.** Información pública revisada. Preguntas sobre actividades, primera visita, principiantes, ubicación, registro, acceso o cupos devuelven la ficha pública aprobada y su enlace. Un tema desconocido o argumentos adicionales se rechazan.
10. **CA-10.** Conversación acotada. Saludos y cortesías breves reciben respuestas naturales sin llamada al proveedor; una pregunta de negocio que contiene un saludo conserva su intención. Ante un tema claramente ajeno, el agente redirige con cortesía; una segunda pregunta ajena recibe una invitación más directa a volver al gimnasio. Una pregunta ambigua pide más detalle.
11. **CA-11.** Recuperación local. Pedir recuperación abre un formulario para correo, DNI y teléfono. Completarlo no envía una solicitud al backend ni al dueño, no restablece la cuenta y no muestra esos datos en el historial. Al cerrar el chat se borra el borrador local.
12. **CA-12.** Guía de registro. Preguntar cómo registrarse devuelve pasos basados en la página de Registro y un enlace a ella. La instrucción directa de inscribir o pagar no inicia ese flujo.
13. **CA-13.** Cuota actual. El proveedor tiene una cuota global por proceso de 10 selecciones por minuto y 100 por día UTC. Cuando se agota, el catálogo atiende las consultas reconocibles y las demás reciben HTTP 429. La cuota se contabiliza por instancia.

| Criterio | Evidencia |
| --- | --- |
| CA-01 | Catálogos cambiantes en [pruebas de flujo](../../../backend/tests/agente/test_agent_flow.py). |
| CA-02 | Horarios y lectura pública en [batería](qa-v1-bateria.md). |
| CA-03 | Operaciones privadas en [pruebas de flujo](../../../backend/tests/agente/test_agent_flow.py). |
| CA-04 | Fallos y estados visibles en [pruebas HTTP](../../../backend/tests/agente/test_agent_http.py). |
| CA-05 | Datos sensibles en [pruebas de interfaz](../../../frontend/tests/e2e/simuladas/agent.spec.js). |
| CA-06 | Herramientas cerradas en [pruebas de flujo](../../../backend/tests/agente/test_agent_flow.py). |
| CA-07 | Aislamiento y expiración en [pruebas de flujo](../../../backend/tests/agente/test_agent_flow.py). |
| CA-08 | Casos aislados y lectura real en [matriz y resultados](qa-v1-bateria.md). |
| CA-09 | Fichas públicas en [pruebas de flujo](../../../backend/tests/agente/test_agent_flow.py). |
| CA-10 | Cortesías y redirección en [pruebas de flujo](../../../backend/tests/agente/test_agent_flow.py). |
| CA-11 | Recuperación local en [pruebas de interfaz](../../../frontend/tests/e2e/simuladas/agent.spec.js) y [recorrido conectado](../../../frontend/tests/e2e/integracion/agent-flow.spec.js). |
| CA-12 | Guía de registro en [pruebas de flujo](../../../backend/tests/agente/test_agent_flow.py). |
| CA-13 | Cuota por proceso en [pruebas HTTP](../../../backend/tests/agente/test_agent_http.py). |

### Requisitos funcionales

- **FR-001:** Consultar planes y horarios publicados y componer la respuesta factual desde los resultados (CA-01, CA-02, CA-04).
- **FR-002:** Ofrecer enlaces a pantallas públicas, sin registrar clientes ni realizar operaciones privadas (CA-03, CA-09, CA-12).
- **FR-003:** Interceptar patrones de datos sensibles y validar herramientas, temas e intenciones (CA-05, CA-06, CA-11).
- **FR-004:** Mantener el tema reciente aislado y responder con cortesía o redirección cuando corresponda (CA-07, CA-10).
- **FR-005:** Ejecutar pruebas aisladas y una comprobación de lectura pública separada; limitar las llamadas al proveedor por proceso (CA-08, CA-13).

### Entidades y resultados medibles

Turno de conversación, selección de herramienta, tema temporal y respuesta basada en datos públicos. No se crean entidades de cliente, matrícula, recuperación o pago en esta entrega.

- **SC-001:** En los casos con catálogo controlado, cada importe y horario afirmado coincide con el dato de entrada; el caso de lectura real coteja al menos un horario actual con Supabase.
- **SC-002:** En los casos automatizados de privacidad y abuso se observan cero llamadas al proveedor con datos sensibles y cero escrituras de negocio; la recuperación no envía los datos del formulario.
- **SC-003:** Los recorridos de interfaz se pueden repetir en Chromium, Firefox y WebKit, con resultados y límites registrados en [validación](validation.md) y [batería](qa-v1-bateria.md).

## 4. Technical Constraints

- Mantener presentación Vue, ruta FastAPI, aplicación, dominio e infraestructura. La interfaz envía una consulta; el backend decide qué herramienta puede ejecutarse y arma la respuesta factual.
- Reutilizar `GymService` para planes y horarios públicos. El modelo selecciona una herramienta permitida y el backend lee los datos. Las consultas reconocibles de planes y horarios tienen un respaldo directo en el catálogo. La guía de registro se entrega desde una ficha revisada.
- La información general proviene de fichas públicas revisadas en `public_gym_knowledge.py`. Revisarlas cuando cambien Landing o las preguntas frecuentes; no hay indexación del repositorio ni RAG en v1.
- Groq se usa en el backend como **selector de herramientas**, con modelo `openai/gpt-oss-120b`. Su clave no se expone en `VITE_*`. Este SPEC no crea ni modifica variables de entorno.
- El endpoint público recibe un mensaje de 1 a 500 caracteres y un identificador de conversación opcional de hasta 64. El backend conserva solo el tema reciente durante 30 minutos en memoria. El formulario de recuperación mantiene un borrador solo en el navegador.
- La cuota de 10 llamadas por minuto y 100 por día UTC es atómica solo dentro de un proceso. Una cuota distribuida y una revisión adicional de privacidad son necesarias antes de tráfico público real.
- Las operaciones de cuenta, pagos, matrículas y datos de terceros siguen en las rutas privadas con sus permisos existentes. La app local `agent_readonly_app.py` expone únicamente el chat y tres lecturas públicas para demostrar el flujo sin arrancar trabajos de fondo.
- El [SPEC anterior](../002-chatbot-clientes/spec.md) y los prototipos de Rodrigo son referencias de experiencia; no prueban esta integración ni se fusionaron a la rama.

## 5. Guardrails

- El modelo puede seleccionar solo herramientas y categorías conversacionales de una lista cerrada. La selección no concede permisos; el dominio valida su nombre y argumentos antes de consultar información.
- El chat no cobra, activa membresías, matricula, cancela, modifica precios, restablece cuentas ni consulta datos de terceros.
- Los patrones sensibles probados se bloquean antes del proveedor. No exponer claves, tokens, datos de pago o respuestas crudas del proveedor. El filtro actual no garantiza detectar cualquier dato personal o intento de inyección; su ampliación requiere pruebas propias.
- No usar datos fijos del prompt como fuente de verdad de precios, cupos u horarios actuales. Las fichas estáticas se revisan contra páginas públicas cuando estas cambien.
- Aislar pagos, correos y proveedores en la batería automatizada; usar datos sintéticos. La prueba con Supabase es opcional y solo de lectura. La conexión real a Groq fue manual, no una regresión automatizada.

## 6. Edge Cases

| Caso | Resultado esperado | Criterio |
| --- | --- | --- |
| Catálogo cambia entre consultas | La nueva respuesta refleja la fuente reciente. | CA-01 |
| Catálogo vacío, lento o con error | No se inventan datos; se ofrece alternativa. | CA-02, CA-04 |
| Herramienta ajena o argumentos inválidos | Se rechaza sin efecto externo. | CA-03, CA-06 |
| Contraseña o tarjeta en el mensaje | Advertencia local; el dato no llega al proveedor. | CA-05 |
| Conversaciones simultáneas | Cada una conserva su contexto aislado. | CA-07 |
| Tema público desconocido o argumento malformado | Se rechaza sin consultar otras fuentes. | CA-09 |
| Pregunta ambigua o claramente ajena | La primera pide detalle; la segunda redirige al gimnasio sin inventar hechos. | CA-10 |
| Recuperación de cuenta con datos de prueba | El formulario queda local; no se promete contacto ni restablecimiento. | CA-11 |
| Pregunta «¿cómo me registro?» frente a «inscríbeme» | La primera explica el proceso; la segunda no ejecuta matrícula. | CA-03, CA-12 |
| Cuota del proceso agotada | Lectura del catálogo para preguntas reconocibles y HTTP 429 para las demás. | CA-13 |

### Decisiones de alcance

- V1 orienta sobre información pública y conserva una conversación breve. No es un agente entrenado con toda la base, no hace búsquedas semánticas y no consulta tablas por instrucciones libres del modelo.
- Matrículas, cancelaciones, compras, consultas privadas y el envío de solicitudes de recuperación requieren criterios y permisos de otra entrega.
- El trabajo de Rodrigo se usa como referencia, según indicó el usuario; no se fusionó en esta rama.

## 7. Definition of Done

- [x] El comportamiento implementado, sus límites y los criterios verificables están descritos en este SPEC.
- [x] Hay trazabilidad hacia pruebas de dominio, ruta, interfaz y lectura pública en la [validación](validation.md) y la [batería](qa-v1-bateria.md).
- [x] La rama de pruebas registra un antes/después **de la ampliación de la batería**; no existe una línea base anterior a toda la implementación de v1 y no se afirma lo contrario.
- [x] Se demuestran planes, horarios, errores y privacidad con datos controlados; una prueba separada contrasta horarios actuales de Supabase sin escribir.
- [ ] Integrar v1 al `develop` vigente y repetir la regresión sobre ese código actualizado.
- [ ] Revisar con el equipo el alcance y la UX antes de exponer el agente al público.
- [ ] Implementar cuota distribuida y ampliar la revisión de privacidad antes de un despliegue con tráfico real.
- [ ] Ejecutar SonarQube/Quality Gate de la rama integrada; no se atribuye a v1 la cobertura histórica del proyecto.
