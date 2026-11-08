# Implementation Plan: Reglas de Control del Backend del Chatbot

**Feature:** `002-chatbot-reglas-control` · **Fecha:** 2026-11-08  
**Spec:** [spec.md](spec.md) · **Contexto:** [context.md](context.md) · **Modelo:** [data-model.md](data-model.md) · **Contrato:** [contracts/control.md](contracts/control.md)  

---

## 1. Resumen

Implementar en el backend FastAPI el conjunto de reglas de control del chatbot para Silver Gym Surco (HU-CB11 a HU-CB16): autenticación/autorización mediante JWT, privacidad y enmascaramiento PII, lista cerrada de acciones deterministas con doble validación, control de flujo y límites de mensajes (rate limiting atómico), presupuesto y conteo de tokens con alertas vía Resend, y tiempos de espera y expiración (inactividad 30 min y pendientes 5 min sin reserva previa).

---

## 2. Contexto Técnico y Arquitectura

- **Stack:** Python 3.10+ / FastAPI / Pydantic Settings v2 / PostgreSQL (Supabase) / Resend SDK / PyJWT.
- **Patrón:** Clean Architecture existente en `backend/` (`domain`, `application`, `infrastructure`, `presentation`).
- **Aislamiento:** Mocks de base de datos y proveedores externos (Groq, Resend) en las pruebas unitarias y de integración rápida; contenedor PostgreSQL en pruebas de integración atómica.

---

## 3. Verificación de Constitución (Constitution Check)

- [x] **I (Especificación previa):** Spec, context, data-model, contracts y plan completados antes de iniciar codificación.
- [x] **II (Capas y Responsabilidades):** Reglas deterministas en `domain`, orquestación en `application`, persistencia en `infrastructure` y routers en `presentation`.
- [x] **III (Consistencia y Persistencia):** Consultas atómicas `INSERT ... ON CONFLICT` para contadores; transacciones seguras sin escrituras parciales.
- [x] **IV (Permisos y Privacidad Zero-Trust):** Validación criptográfica de JWT en cada petición; cero PII en logs y base de datos; respuesta neutra ante terceros (EX-13).
- [x] **V (Continuidad Operativa y Resiliencia):** Degradación elegante a modo básico si Groq falla o agota cuota (EX-03); fallas de Resend no interrumpen el chat.
- [x] **VI (Pruebas y Verificación):** Cobertura unitaria y de integración exhaustiva; casos de prueba de abuso SEC-01 a SEC-07 reproducibles.
- [x] **VII (Mantenibilidad y Documentación):** Variables centralizadas en `.env.example` y parámetros operacionales documentados.

---

## 4. Estructura de Componentes en `backend/`

```
backend/
├── app/core/
│   └── chatbot_settings.py         # Configuración y variables de entorno del chatbot (RNF-CB07)
├── domain/services/
│   ├── chatbot_permissions.py      # HU-CB11 & RN-01 (roles, aislamiento de cliente, JWT)
│   ├── chatbot_privacy.py          # HU-CB12 & RN-07/RN-08 (sanitización de entrada y enmascarado de salida)
│   ├── chatbot_actions.py          # HU-CB13 & RN-04/RN-05/RN-06 (lista cerrada determinista)
│   ├── chatbot_rate_limiter.py     # HU-CB14 & RN-10 (control de mensajes y longitud máx.)
│   ├── chatbot_budget.py           # HU-CB15 & RN-11 (acumulador de tokens y alertas)
│   └── chatbot_expiration.py       # HU-CB16 (temporizadores: inactividad 30m, pendientes 5m)
├── application/services/
│   └── chatbot_orchestrator.py     # Pipeline ordenado de 9 pasos (POST /chat)
├── infrastructure/
│   ├── repositories/
│   │   └── chatbot_repository.py   # Persistencia en tablas chatbot_* (atómico)
│   └── notifications/
│       └── resend_notifier.py      # Envío de alertas de presupuesto vía Resend
├── presentation/api/v1/endpoints/
│   └── chatbot.py                  # Endpoint POST /api/chatbot/message
└── tests/
    └── test_chatbot_control_rules.py # Suite integral de reglas de control y abuso (SEC-01..07)
```

---

## 5. Diseño del Cambio (Pipeline de 9 Etapas)

1. **CB11 (Identificación):** Decodificar JWT con Supabase Auth; extraer `id_cliente` o clasificar como `visitante`. Generar `ip_hmac = HMAC-SHA256(ip, secret)`.
2. **CB14 (Rate Limit):** Verificar e incrementar contadores en `chatbot_rate_limit_contadores`. Si excede, lanzar HTTP 429 con `retry_after_seconds`.
3. **CB14 (Longitud Máx.):** Validar `len(message) <= 500`. Si excede, rechazar con HTTP 400.
4. **CB12 (Filtro Entrada):** Evaluar regex de contraseñas/tarjetas de crédito. Si detecta datos sensibles, devolver advertencia sin registrar texto en claro.
5. **CB15 (Presupuesto):** Verificar acumulado diario en `chatbot_uso_tokens`. Si alcanzó 100%, conmutar a `basic_mode`.
6. **Llamada LLM (Frontera):** Invocar Groq con timeout de 15 s y 1 reintento interno. Extraer `usage.total_tokens`.
7. **CB13 (Re-validación Acción):** Validar acción contra la lista cerrada con `autorizar_accion()`. Exigir confirmación previa para escrituras.
8. **CB12 (Enmascarado Salida):** Aplicar regex de enmascaramiento (`***4521`) a DNI, correo y teléfono en el texto devuelto.
9. **Persistencia & Alertas:** Guardar mensaje sanitizado en `chatbot_mensajes`, actualizar tokens, y disparar correo Resend si se cruzó el 80% o 100%.

---

## 6. Matriz de Verificación y Criterios de Aceptación

| Criterio | Componente / Prueba | Resultado Esperado |
|---|---|---|
| **CA-CB11** | `test_chatbot_control_rules.py::test_permissions` | Visitante restringido a info pública; cliente aislado por su propio `id_cliente`; JWT falso/expirado rechazado. |
| **CA-CB12** | `test_chatbot_control_rules.py::test_privacy` | Contraseñas/tarjetas rechazadas en entrada; DNI/teléfono enmascarados en salida; historial sin PII. |
| **CA-CB13** | `test_chatbot_control_rules.py::test_actions` | Acciones prohibidas rechazadas con `forbidden`; mutaciones requieren confirmación explícita. |
| **CA-CB14** | `test_chatbot_control_rules.py::test_rate_limits` | Mensajes > 500 caracteres rechazados; exceso de 10 msg/min genera HTTP 429 con tiempo restante. |
| **CA-CB15** | `test_chatbot_control_rules.py::test_budget` | Acumulación correcta de tokens; alerta Resend emitida al 80% (máx 1/día); modo básico al 100%. |
| **CA-CB16** | `test_chatbot_control_rules.py::test_expiration` | Inactividad > 30 min marca conversación cerrada; acción pendiente > 5 min se anula sin reserva. |
| **CA-SEC** | `test_chatbot_control_rules.py::test_abuse_cases` | Casos SEC-01 a SEC-07 aprobados sin fugas ni elevación de privilegios. |
| **CA-FE-PROTO** | Pruebas de integración HTTP y UI | Widget renderiza banners para los 5 estados (`rate_limited`, `basic_mode`, `session_expired`, `forbidden`, `slow`) y enlaza JWT. |

---

## 7. Integración con el Prototipo Frontend (`prototipo/`)

Se incorpora la carpeta [prototipo/](prototipo/) en la feature specification para servir como referencia y base de código del widget frontend.

### Componentes y Tarjetas Reutilizadas del Prototipo
- **Contenedores y Cabecera:** `ChatLauncher`, `ChatWindow`, `ChatHeader`, `MessageList`.
- **Mensajería:** `BotMessage`, `UserMessage`, `QuickReplies`, `TypingIndicator`, `ChatInput` (con contador visible de 500 caracteres).
- **Tarjetas y Banners:** `NoticeBanner` (cuenta regresiva de rate limit y aviso de modo básico), `ContactCard` (derivación directa a WhatsApp +51 912 794 583), `ScheduleCard` y `ProductCardBasic`.
- **Servicio y Composable:** Adaptar `httpChatService.ts` y `useChatbot.ts` para consumir `POST /api/chatbot/message`, inyectando el token JWT de Supabase Auth en `Authorization: Bearer <token>`.
