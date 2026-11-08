# Contrato de API: Reglas de Control del Chatbot

**Feature:** `002-chatbot-reglas-control` · **Fecha:** 2026-11-08  
**Endpoint:** `POST /api/chatbot/message`  
**Autenticación:** Cabecera HTTP opcional `Authorization: Bearer <jwt_supabase_auth>`  

---

## 1. Esquema de Petición (Request Body)

```json
{
  "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "message": "Hola, ¿cuáles son los horarios de spinning para mañana?",
  "action": "activities",
  "confirmed": false
}
```

### Especificación de Campos
- `conversation_id` (UUID, opcional/nullable): Identificador de la conversación activa. Si se omite o la sesión anterior expiró (30 min), el backend genera un nuevo UUID.
- `message` (string, obligatorio): Texto libre del usuario. Longitud máxima estricta: **500 caracteres** (HU-CB14, `CHATBOT_MAX_MENSAJE_CHARS`).
- `action` (string, opcional): Acción estructurada enviada por botones de opciones rápidas (`quickReplies`).
- `confirmed` (boolean, opcional, default: `false`): Señal de confirmación explícita para la `accion_pendiente` (HU-CB13, RN-06).

---

## 2. Esquema de Respuesta Exitosa (Response Body: `ChatResponse`)

```json
{
  "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "state": "ok",
  "blocks": [
    {
      "type": "text",
      "text": "Estas son las actividades grupales disponibles para el Lunes 9 de Febrero:"
    },
    {
      "type": "schedule_list",
      "items": [
        {
          "id": 12,
          "service": "SPINNING",
          "day": "Lunes 9 de Febrero",
          "start": "07:00",
          "end": "08:00",
          "slots_left": 3
        }
      ]
    }
  ],
  "quick_replies": [
    { "label": "Horario del gimnasio", "action": "gym_hours" },
    { "label": "Hablar con una persona", "action": "contact_human" }
  ],
  "retry_after_seconds": null
}
```

### Estados Posibles (`state`)
| Estado | Condición | Comportamiento en Widget |
|---|---|---|
| `ok` | Procesamiento exitoso estándar. | Muestra mensajes y botones normalmente. |
| `rate_limited` | Límite por minuto o día superado (EX-04). | Muestra banner de advertencia y deshabilita input según `retry_after_seconds`. |
| `basic_mode` | Presupuesto 100% alcanzado o LLM caído (EX-03). | Muestra banner informativo; restringe entrada libre y ofrece solo `quick_replies`. |
| `session_expired` | Token JWT vencido (EX-01) o inactividad de 30 min (EX-14). | Muestra banner invitando a iniciar sesión o reiniciar el chat. |
| `forbidden` | Intento de acción prohibida (EX-10, RN-05). | Muestra mensaje explicativo y tarjeta de contacto a WhatsApp. |
| `slow` | Timeout tras reintento fallido del LLM (EX-02). | Muestra mensaje de fallo y botón de reintento o derivación. |

### Tipos de Bloques (`blocks`)
- `text`: `{ "type": "text", "text": "..." }`
- `schedule_list`: `{ "type": "schedule_list", "items": [...] }`
- `product_basic_list`: `{ "type": "product_basic_list", "items": [...] }`
- `contact`: `{ "type": "contact", "phone": "+51 912 794 583", "whatsapp_url": "https://wa.me/51912794583", "attention_hours": "Lun a Sáb 8:00 am - 8:00 pm" }`
- `notice`: `{ "type": "notice", "kind": "rate_limit|basic_mode|session_expired", "text": "...", "retry_in_seconds": 40 }`

---

## 3. Códigos de Error HTTP

| Código HTTP | Causa | Cuerpo de Respuesta |
|:---:|---|---|
| `400 Bad Request` | Mensaje > 500 caracteres o JSON malformado. | `{ "detail": "El mensaje supera el límite máximo permitido de 500 caracteres." }` |
| `401 Unauthorized` | JWT malformado o firma inválida. | `{ "detail": "Sesión inválida o expirada. Por favor inicie sesión.", "state": "session_expired" }` |
| `403 Forbidden` | Intento de modificar datos administrativos o violar lista cerrada. | `{ "detail": "Acción no permitida.", "state": "forbidden" }` |
| `429 Too Many Requests` | Exceso de cuota de mensajes por minuto o por día (EX-04). | `{ "detail": "Límite de mensajes alcanzado.", "state": "rate_limited", "retry_after_seconds": 35 }` |
| `503 Service Unavailable` | LLM no disponible tras agotar reintentos (EX-02) y modo básico degradado. | `{ "detail": "Servicio temporalmente no disponible.", "state": "basic_mode" }` |
