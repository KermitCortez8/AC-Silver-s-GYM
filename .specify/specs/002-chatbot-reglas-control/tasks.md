# Tasks: tareas_v1 — Programar las Reglas de Control del Chatbot

**Caso de Tareas:** Programar las reglas de control del Chatbot: permisos, privacidad, acciones permitidas y límites de mensajes, frecuencia, presupuesto y espera.  
**Feature:** `002-chatbot-reglas-control` · **Fecha:** 2026-11-08  
**Documentos Base:** [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [contracts/control.md](contracts/control.md).  

---

## Reparto de Responsabilidades (Delegación de Trabajo)

| Responsable | Alcance Asignado |
|---|---|
| **AGENTE (Antigravity)** | **Parte fuerte y repetitiva:**<br>1. Toda la codificación de backend en FastAPI (Clean Architecture: Settings, DTOs, Repositorio atómico y 6 servicios de reglas de control CB11..CB16).<br>2. Endpoint `POST /api/chatbot/message` y orquestación del pipeline.<br>3. **Implementación completa del widget en el frontend Vue 3** a partir del prototipo (`ChatWindow`, `ChatLauncher`, `ChatInput`, tarjetas de horario/productos y banners de control).<br>4. Suite formal de pruebas automatizadas y casos de abuso (SEC-01..07). |
| **USUARIO** | **Testeos exploratorios y validación rápida:**<br>1. Scripts pequeños de prueba en Python para testear conectividad de `GROQ_API_KEY` y `RESEND_API_KEY`.<br>2. Comprobación de inserción en tablas de Supabase tras las primeras llamadas.<br>3. Validación visual en navegador de la experiencia del widget. |

---

## Dependencias y Orden de Ejecución

```
Fase 1: Configuración & Repositorio (AGENTE)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
Fase 2: HU-CB11 Permisos (AGENTE)   Test Script Conectividad Groq/Resend (USUARIO)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
Fase 3: HU-CB12 Privacidad (AGENTE) Fase 4: HU-CB13 Acciones (AGENTE)
       │                                 │
       └────────────────┬────────────────┘
                        ▼
Fase 5: HU-CB14 Límites & Rate Limiting (AGENTE)
                        │
                        ▼
Fase 6: HU-CB15 Presupuesto & Tokens (AGENTE)
                        │
                        ▼
Fase 7: HU-CB16 Expiración & Tiempos (AGENTE)
                        │
                        ▼
Fase 8: Orquestación & Endpoint Backend (AGENTE)
                        │
                        ▼
Fase 9: Implementación del Prototipo en Frontend (AGENTE)
                        │
                        ▼
Fase 10: Validación, Pruebas de Abuso & Aceptación (AMBOS)
```

---

## Fase 1: Fundamentos y Configuración Operativa (Backend)

- [x] **T001 [tareas_v1] [AGENTE]** Crear `backend/app/core/chatbot_settings.py` con Pydantic Settings para cargar variables de entorno de `backend/.env.example` con sus valores confirmados (RNF-CB07).  
  *Criterio:* Carga correcta de `CHATBOT_*`, `RESEND_API_KEY` y `GROQ_API_KEY`; validación estricta de tipos.  
  *Prueba:* `test_chatbot_control_rules.py::test_settings_loading`

- [x] **T002 [tareas_v1] [AGENTE]** Crear DTOs y esquemas Pydantic del contrato en `backend/application/schemas/chatbot_schemas.py` según `contracts/control.md` (`ChatRequest`, `ChatResponse`, `Block`, `QuickReply`, `ChatState`).  
  *Criterio:* Serialización y validación estricta de longitud `message <= 500`.  
  *Prueba:* `test_chatbot_control_rules.py::test_contract_schemas`

- [x] **T003 [tareas_v1] [AGENTE]** Implementar `backend/infrastructure/repositories/chatbot_repository.py` con operaciones atómicas sobre las 6 tablas `chatbot_*` en PostgreSQL.  
  *Criterio:* Consultas parametrizadas con `ON CONFLICT` para evitar condiciones de carrera (RNF-CB06).  
  *Prueba:* `test_chatbot_control_rules.py::test_repository_crud`

---

## Fase 2: HU-CB11 — Permisos según Vista y Sesión (Backend)

- [x] **T004 [tareas_v1] [AGENTE] [HU-CB11]** Implementar servicio `backend/domain/services/chatbot_permissions.py` para validar tokens JWT contra Supabase Auth y resolver `id_cliente` en `public."CLIENTES"` (RN-01).  
  *Criterio:* Sin token categoriza `visitante`; con token categoriza `cliente`; token malformado devuelve `401 Unauthorized` / `session_expired` (EX-01).  
  *Prueba:* `test_chatbot_control_rules.py::test_permissions_jwt_validation`

- [x] **T005 [tareas_v1] [AGENTE] [HU-CB11]** Implementar aislamiento estricto de cliente y protección contra acceso a datos de terceros (EX-13, RF-CB11-06).  
  *Criterio:* Toda consulta fuerza `cliente_id = :id_jwt`. Petición de datos ajenos responde neutralmente sin confirmar existencia y registra `acceso_datos_tercero` en `chatbot_eventos_seguridad`.  
  *Prueba:* `test_chatbot_control_rules.py::test_permissions_third_party_data_isolation`

- [x] **T006 [tareas_v1] [AGENTE] [HU-CB11]** Implementar neutralización de suplantación de roles administrativos en texto (RF-CB11-04, CUS30 §3).  
  *Criterio:* Declaraciones como "soy el administrador" se ignoran por completo; se mantienen privilegios del JWT.  
  *Prueba:* `test_chatbot_control_rules.py::test_permissions_role_spoofing_ignored`

---

## Fase 3: HU-CB12 — Privacidad de Datos Personales (Backend)

- [x] **T007 [tareas_v1] [AGENTE] [HU-CB12]** Implementar sanitizador de entrada en `backend/domain/services/chatbot_privacy.py` para interceptar contraseñas, PINs y números de tarjetas bancarias (RF-CB12-02, HU-CB12 Esc. 2).  
  *Criterio:* Intercepta patrones de tarjetas/contraseñas, detiene el procesamiento, emite advertencia de seguridad y registra `datos_sensibles_entrada` sin guardar datos en texto plano.  
  *Prueba:* `test_chatbot_control_rules.py::test_privacy_sensitive_input_sanitizer`

- [x] **T008 [tareas_v1] [AGENTE] [HU-CB12]** Implementar enmascarador de salida para DNI, correos electrónicos y teléfonos (RN-07, HU-CB12 Esc. 1).  
  *Criterio:* Transforma DNI en `****4521`, correos en `r***@gmail.com` y teléfonos en `***-***-583` antes de emitir respuesta al widget.  
  *Prueba:* `test_chatbot_control_rules.py::test_privacy_output_masking`

- [x] **T009 [tareas_v1] [AGENTE] [HU-CB12]** Implementar constructor de prompt con contexto mínimo (RN-08, RF-CB12-03) y persistencia segura en `chatbot_mensajes` sin PII en texto plano (RF-CB12-04).  
  *Criterio:* El prompt al LLM no contiene identificadores internos ni PII completa.  
  *Prueba:* `test_chatbot_control_rules.py::test_privacy_minimal_context_builder`

---

## Fase 4: HU-CB13 — Lista Cerrada de Acciones Permitidas (Backend)

- [x] **T010 [tareas_v1] [AGENTE] [HU-CB13]** Implementar `backend/domain/services/chatbot_actions.py` con la función determinista `autorizar_accion(accion, contexto_usuario, parametros)` (RN-04, RF-CB13-04).  
  *Criterio:* Permite únicamente las 7 acciones taxativas; no depende de HU-CB17.  
  *Prueba:* `test_chatbot_control_rules.py::test_actions_closed_list_authorization`

- [x] **T011 [tareas_v1] [AGENTE] [HU-CB13]** Implementar rechazo y derivación de acciones prohibidas (confirmar pagos, activar membresías, modificar datos) (RN-05, EX-10, RF-CB13-02/03).  
  *Criterio:* Devuelve estado `forbidden`, mensaje explicativo, tarjeta de WhatsApp y registra `accion_no_permitida`.  
  *Prueba:* `test_chatbot_control_rules.py::test_actions_forbidden_rejection`

- [x] **T012 [tareas_v1] [AGENTE] [HU-CB13]** Implementar flujo de confirmación explícita previa obligatoria para inscripciones, cancelaciones y compras (RN-06, RF-CB13-05).  
  *Criterio:* Si `confirmed != true`, la acción se guarda en `accion_pendiente` y se solicita confirmación al usuario; no se escribe en la BD operativa.  
  *Prueba:* `test_chatbot_control_rules.py::test_actions_explicit_confirmation_required`

---

## Fase 5: HU-CB14 — Límite de Mensajes y Frecuencia (Backend)

- [x] **T013 [tareas_v1] [AGENTE] [HU-CB14]** Implementar generador de clave de sujeto y anonimizador de IP mediante `HMAC-SHA256` en `backend/domain/services/chatbot_rate_limiter.py` (RN-10, RF-CB14-04).  
  *Criterio:* Clave `id_cliente` para clientes y `HMAC-SHA256(ip, secret)` para visitantes; soporte de cabeceras de proxy de confianza.  
  *Prueba:* `test_chatbot_control_rules.py::test_rate_limiter_subject_key`

- [x] **T014 [tareas_v1] [AGENTE] [HU-CB14]** Implementar validador de rate limit atómico sobre `chatbot_rate_limit_contadores` para ventanas de minuto y día (RN-10, EX-04, RF-CB14-01/03).  
  *Criterio:* Clientes: 10/min, 100/día; Visitantes: 5/min, 20/día. Superar cuota devuelve `429 Too Many Requests` con `retry_after_seconds`.  
  *Prueba:* `test_chatbot_control_rules.py::test_rate_limiter_windows_enforcement`

- [x] **T015 [tareas_v1] [AGENTE] [HU-CB14]** Implementar validación estricta de longitud máxima de mensaje en 500 caracteres (RF-CB14-02).  
  *Criterio:* Mensajes > 500 caracteres devuelven HTTP 400 antes de procesar lógica o LLM.  
  *Prueba:* `test_chatbot_control_rules.py::test_rate_limiter_max_chars`

---

## Fase 6: HU-CB15 — Presupuesto de Uso del LLM (Backend)

- [x] **T016 [tareas_v1] [AGENTE] [HU-CB15]** Implementar acumulador de consumo de tokens en `backend/domain/services/chatbot_budget.py` utilizando `chatbot_uso_tokens` y campo `usage` de Groq (RN-11, RF-CB15-01).  
  *Criterio:* Acumulación correcta diaria por usuario y total global `__sistema__`.  
  *Prueba:* `test_chatbot_control_rules.py::test_budget_token_accumulation`

- [x] **T017 [tareas_v1] [AGENTE] [HU-CB15]** Implementar emisor de alertas por correo vía Resend en `backend/infrastructure/notifications/resend_notifier.py` para el umbral del 80% y 100% (RF-CB15-04, [?-P2 DECIDIDO]).  
  *Criterio:* Envío de correo a `CHATBOT_ALERT_EMAIL_TO` con deduplicación en `chatbot_alertas_enviadas` (máximo 1 envío por tipo/día). Si Resend falla, el chat no se bloquea.  
  *Prueba:* `test_chatbot_control_rules.py::test_budget_resend_notification`

- [x] **T018 [tareas_v1] [AGENTE] [HU-CB15]** Implementar activación de modo básico al alcanzar el 100% del presupuesto interno diario o tope por usuario (EX-03, RF-CB15-03/05).  
  *Criterio:* Devuelve estado `basic_mode`, deshabilita llamadas al LLM y ofrece solo respuestas predefinidas y WhatsApp.  
  *Prueba:* `test_chatbot_control_rules.py::test_budget_basic_mode_trigger`

---

## Fase 7: HU-CB16 — Tiempos de Espera y Expiración (Backend)

- [x] **T019 [tareas_v1] [AGENTE] [HU-CB16]** Implementar control de inactividad de 30 minutos sobre `chatbot_conversaciones` en `backend/domain/services/chatbot_expiration.py` (EX-14, RF-CB16-02).  
  *Criterio:* Conversaciones con `now() - ultimo_mensaje_en > 30 min` pasan a `expirada_inactividad`; nuevo mensaje inicia conversación con nuevo UUID.  
  *Prueba:* `test_chatbot_control_rules.py::test_expiration_inactivity_30min`

- [x] **T020 [tareas_v1] [AGENTE] [HU-CB16]** Implementar expiración de acciones pendientes a los 5 minutos sin reserva previa (EX-15, RF-CB16-03, [?-F2 PROPUESTA-ACEPTADA]).  
  *Criterio:* Si `now() - accion_pendiente_desde > 5 min`, la confirmación se rechaza; se requiere re-validar disponibilidad.  
  *Prueba:* `test_chatbot_control_rules.py::test_expiration_pending_action_5min`

- [x] **T021 [tareas_v1] [AGENTE] [HU-CB16]** Implementar timeout de llamada al LLM de 15 segundos con 1 reintento interno backend (RNF-CB01, EX-02, RF-CB16-01).  
  *Criterio:* Falla tras 15 s dispara reintento; si vuelve a fallar devuelve error de timeout y tarjeta WhatsApp (`state: 'slow'`).  
  *Prueba:* `test_chatbot_control_rules.py::test_expiration_llm_timeout_retry`

---

## Fase 8: Orquestación del Endpoint y Casos de Abuso (Backend)

- [x] **T022 [tareas_v1] [AGENTE]** Implementar orquestador del pipeline de 9 etapas en `backend/application/services/chatbot_orchestrator.py` y conectar endpoint `POST /api/chatbot/message` en `backend/presentation/routes/chatbot_routes.py`.  
  *Criterio:* Enlace fluido de todas las reglas de control en el orden establecido en la especificación.  
  *Prueba:* `test_chatbot_control_rules.py::test_full_pipeline_orchestration`

- [x] **T023 [tareas_v1] [AGENTE]** Implementar suite exhaustiva de casos de prueba de abuso (SEC-01 a SEC-07) en `backend/tests/test_chatbot_control_rules.py`.  
  *Criterio:* 100% de casos de abuso aprobados (ráfagas por IP, JWT falso, suplantación de personal, robo de datos ajenos, payloads masivos y datos bancarios).  
  *Prueba:* `test_chatbot_control_rules.py::test_abuse_security_cases`

---

## Fase 9: Implementación Fuerte del Widget en Frontend (AGENTE)

- [x] **T024 [tareas_v1] [AGENTE] [Frontend]** Portar e integrar los componentes visuales del prototipo (`prototipo/src/components/chatbot/`) a la aplicación Vue 3 del gimnasio (`ChatLauncher`, `ChatWindow`, `ChatHeader`, `MessageList`, `BotMessage`, `UserMessage`, `QuickReplies`, `TypingIndicator`, `ChatInput`).  
  *Criterio:* Renderizado responsivo (400px escritorio / 100dvh móvil), diseño deportivo oficial, contador de caracteres hasta 500 chars.  
  *Prueba:* Compilación de componentes y renderizado visual en la app Vue 3.

- [x] **T025 [tareas_v1] [AGENTE] [Frontend]** Portar e integrar las tarjetas y banners del prototipo (`prototipo/src/components/cards/`): `NoticeBanner`, `ContactCard`, `ScheduleCard` y `ProductCardBasic`.  
  *Criterio:* Visualización fluida de los 5 estados de control devueltos por el backend (`rate_limited` con cuenta regresiva, `basic_mode`, `session_expired` con acción de login, `forbidden` con WhatsApp +51 912 794 583 y `slow`).  
  *Prueba:* Renderizado de cada bloque y banner ante estados de prueba.

- [x] **T026 [tareas_v1] [AGENTE] [Frontend]** Implementar el servicio cliente HTTP en Vue (`httpChatService.js`) conectado a `POST /api/chatbot/message`, adjuntando automáticamente el JWT de Supabase Auth en cabecera `Authorization: Bearer <token>` cuando el usuario haya iniciado sesión.  
  *Criterio:* Comunicación JSON según `contracts/control.md`, manejo de errores 400, 401, 403, 429 y 503.  
  *Prueba:* Pruebas de integración frontend de consumo del endpoint.

- [x] **T027 [tareas_v1] [AGENTE] [Frontend]** Implementar el composable/store de estado (`useChatbot.js`) en Pinia/Vue para gestionar el ciclo de vida del chat: temporizador de inactividad de 30 min en UI, bloqueo de input en `rate_limited`, restricción a `quickReplies` en `basic_mode` y expiración de sesión.  
  *Criterio:* Reactividad total de la interfaz ante los controles de flujo y límites del backend.  
  *Prueba:* Verificación de transiciones de estado en la UI del chatbot.

---

## Fase 10: Testeo Exploratorio, Verificación y Cierre (USUARIO & AGENTE)

- [x] **T028 [tareas_v1] [USUARIO & AGENTE]** Crear y ejecutar script pequeño en Python (`scratch/test_groq_connection.py`) para verificar conectividad directa con Groq API usando `GROQ_API_KEY` y validar que el campo `response.usage.total_tokens` responde con el modelo `openai/gpt-oss-120b`. Conectar `GroqService` en vivo con System Prompt blindado.  
  *Criterio:* Confirmar formato de respuesta y tiempo de latencia (< 15 s). Verificado en 0.49 s con status 200 OK y pipeline conectado.

- [ ] **T029 [tareas_v1] [USUARIO]** Crear y ejecutar script pequeño en Python (`scratch/test_resend_email.py`) para verificar el envío de un correo de prueba a `CHATBOT_ALERT_EMAIL_TO` usando `RESEND_API_KEY`.  
  *Criterio:* Recepción exitosa del correo de prueba de alerta sin romper el flujo.

- [ ] **T030 [tareas_v1] [USUARIO]** Testeo manual exploratorio de las reglas de control en el widget integrado (probar escribir > 500 caracteres, enviar ráfaga rápida de mensajes para forzar rate limit de 10 msg/min, y probar una consulta con y sin sesión de Supabase).  
  *Criterio:* Validar en navegador que la experiencia visual responda correctamente a los controles.

- [x] **T031 [tareas_v1] [AGENTE]** Ejecutar la suite completa automatizada (`pytest backend/tests/test_chatbot_control_rules.py`), auditar cobertura y registrar evidencia final en `validation.md`.  
  *Criterio:* 100% pruebas aprobadas sin regresiones en otros módulos.
