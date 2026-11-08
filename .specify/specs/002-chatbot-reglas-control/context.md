# Contexto de la Feature: Reglas de Control del Backend del Chatbot

**Feature:** `002-chatbot-reglas-control` · **Fecha:** 2026-11-08  
**Spec Principal:** [spec.md](spec.md) · **Base del Sistema:** [000-base-implementada](../000-base-implementada/spec.md)  
**Módulos Afectados:** MOD-01 (Autenticación), MOD-02 (Clientes), MOD-03 (Membresías), MOD-05 (Horarios/Matrículas), MOD-07 (Tienda) y nuevo submódulo transversal `chatbot_rules`.

---

## 1. Propósito y Arquitectura

El chatbot es un widget web embebido en la aplicación Vue 3 de Silver Gym Surco. Su propósito es proveer autoatención asistida por inteligencia artificial generativa (Groq `openai/gpt-oss-120b`), reduciendo la carga operativa de recepción sin comprometer la seguridad de datos ni permitir operaciones destructivas.

### Principio Fundamental de Seguridad
El backend FastAPI opera bajo una premisa de **desconfianza cero (Zero-Trust)**:
1. Nunca confía en lo que el usuario declare en el texto libre (ej. "soy el administrador").
2. Nunca confía ciegamente en lo que el LLM proponga o devuelva.
3. Toda identidad y permiso se deriva **únicamente del token JWT** de Supabase Auth.
4. Toda mutación sobre la base de datos se ejecuta mediante código determinista de backend re-validando reglas de negocio antes de persistir.

---

## 2. Mapa de Fuentes y Precedencia Documental

```
Jerarquía de Verdad Documental:
CUS30-chatbot.md (Prioridad 1)
       │
       ▼
historias_usuario_chatbot_silver_gym.md (Prioridad 2: HU-CB01 a HU-CB17)
       │
       ▼
secuencia-chatbot.md (Prioridad 3: Flujos A, B, C, D)
       │
       ▼
prototipo/ (Prioridad 4: Referencia visual UI, mocks y base para widget en .specify/specs/002-chatbot-reglas-control/prototipo/)
```

---

## 3. Delimitación de Fronteras

| Componente | Responsabilidad | En este alcance |
|---|---|:---:|
| **Widget Web (Vue.js)** | Renderizado de mensajes, captura de inputs, adjuntar JWT en cabecera, cuenta regresiva de espera. | No (Solo interfaz) |
| **Backend FastAPI (Reglas de Control)** | Decodificación JWT, rate limiting, sanitización PII, lista cerrada de acciones, control de tokens, timeout, expiración. | **SÍ (Núcleo)** |
| **Proveedor LLM (Groq)** | Generación de lenguaje natural con modelo `openai/gpt-oss-120b`. | No (Solo integración) |
| **Supabase PostgreSQL** | Persistencia de tablas `chatbot_*` y tablas maestras (`CLIENTES`, `MEMBRESIA`, etc.). | SÍ (Esquema DDL) |
| **Resend** | Envío de correo de alerta al 80% y 100% de cuota diaria de tokens. | SÍ (Servicio de notificación) |
| **HU-CB17** | Filtro de inyección de prompt del modelo. | No (Enganche desacoplado) |

---

## 4. Registro de Decisiones y Acuerdos Técnicos

- **[?-V1] [PROPUESTA-ACEPTADA]:** Longitud máxima de mensaje = 500 caracteres, validado en backend.
- **[?-V2] [PROPUESTA-ACEPTADA]:** Topes de tokens por usuario = 8.000 tokens/día (cliente) y 3.000 tokens/día (visitante).
- **[?-P2] [DECIDIDO]:** Alerta al 80% y 100% de presupuesto vía correo electrónico con Resend (`RESEND_API_KEY`).
- **[?-P3] [PROPUESTA-ACEPTADA]:** Presupuesto interno = 90% del límite diario de tokens de Groq (180k TPD de 200k TPD).
- **[?-F2] [PROPUESTA-ACEPTADA]:** Sin reserva previa de cupo/stock. Las acciones pendientes expiran a los 5 minutos y se valida disponibilidad en tiempo real al confirmar.
- **[?-S1] [DOCUMENTOS + PROPUESTA]:** Cierre por inactividad tras 30 min borra solo el contexto en memoria. El historial en BD se preserva cerrado.
- **[?-F13] [PROPUESTA-ACEPTADA]:** Esquema `ChatResponse` adaptado y enriquecido para FastAPI, soportando estados `ok`, `rate_limited`, `basic_mode`, `session_expired` y `forbidden`.
