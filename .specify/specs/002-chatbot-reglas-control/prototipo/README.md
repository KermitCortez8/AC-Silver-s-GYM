# Chatbot Silver Gym Surco - Widget Web (Vista Usuario & Móvil)

Prototipo frontend del widget de chatbot para **Silver Gym Surco** desarrollado con React 19, TypeScript y Tailwind CSS, siguiendo el diseño atlético de `DESIGN.md` y las historias de usuario de la Vista Usuario (HU-CB01 a HU-CB17).

---

## 1. Estructura del Proyecto

```
src/
├── types/
│   └── chat.ts               # Contrato de datos: ChatResponse, Block, ChatState, QuickReply
├── services/
│   ├── chatService.ts        # Interfaz del servicio
│   ├── mockChatService.ts    # Simulación con latencia (600-1200ms) y reglas de negocio
│   └── httpChatService.ts    # Esqueleto listo para FastAPI y Supabase Auth
├── hooks/
│   └── useChatbot.ts         # Hook principal: mensajes, auto-scroll, rate-limiting y timers
├── components/
│   ├── landing/
│   │   ├── GymHeader.tsx     # Cabecera web oficial de Silver Gym Surco
│   │   └── GymHero.tsx       # Sección hero con fondo deportivo y métricas
│   ├── chatbot/
│   │   ├── ChatLauncher.tsx  # Píldora flotante "Pregúntale a Silver"
│   │   ├── ChatWindow.tsx    # Contenedor responsive (400x680px escritorio / 100dvh móvil)
│   │   ├── ChatHeader.tsx    # Cabecera Oswald con "Silver" y subtítulo
│   │   ├── MessageList.tsx   # Lista de mensajes accesible con aria-live
│   │   ├── BotMessage.tsx    # Texto limpio del bot sin burbuja
│   │   ├── UserMessage.tsx   # Burbuja naranja #D83A00 alineada a la derecha
│   │   ├── QuickReplies.tsx  # 5 opciones rápidas apiladas (min 44px)
│   │   ├── TypingIndicator.tsx # 3 puntos pulsantes
│   │   ├── ChatInput.tsx     # Input con contador, botón avión y aviso de sesión
│   │   └── DemoToolbar.tsx   # Selector demo (atajo Alt+D) para estados y vista móvil
│   └── cards/
│       ├── ScheduleCard.tsx       # Actividades y cupos sin botón inscribir
│       ├── ProductCardBasic.tsx   # Catálogo básico sin precios ni carrito
│       ├── ContactCard.tsx        # Derivación a WhatsApp y horario de recepción
│       └── NoticeBanner.tsx       # Banners de límite, modo básico y sesión expirada
├── App.tsx                   # Aplicación principal
└── main.tsx                  # Punto de entrada
```

---

## 2. Cómo cambiar de MockChatService a HttpChatService

El hook `useChatbot` está desacoplado del origen de los datos a través de la interfaz `ChatService`:

1. En `src/services/httpChatService.ts`, descomenta la llamada `fetch` a tu endpoint de FastAPI:
   ```typescript
   const response = await fetch('/api/chatbot/message', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'Authorization': `Bearer ${jwtToken}`, // Supabase Auth JWT
     },
     body: JSON.stringify({
       conversation_id: params.conversationId,
       message: params.text,
       action: params.action,
     }),
   });
   ```
2. En `src/hooks/useChatbot.ts`, sustituye la instancia:
   ```typescript
   // Antes:
   const chatService = new MockChatService();

   // Después:
   const chatService = new HttpChatService('/api/chatbot/message', () => supabase.auth.getSession()?.access_token);
   ```
3. **Regla de Seguridad**: La identidad del cliente se obtiene siempre en el backend a partir del token JWT validado por Supabase, nunca del texto escrito por el usuario.

---

## 3. Contrato de Datos (`ChatResponse`)

```typescript
export type ChatState =
  | 'ok'
  | 'rate_limited'
  | 'slow'
  | 'basic_mode'
  | 'session_expired'
  | 'forbidden';

export type Block =
  | { type: 'text'; text: string }
  | { type: 'schedule_list'; items: ScheduleItem[] }
  | { type: 'product_basic_list'; items: ProductBasic[] }
  | { type: 'contact'; phone: string; whatsappUrl: string; attentionHours: string }
  | { type: 'notice'; kind: 'rate_limit' | 'basic_mode' | 'session_expired'; text: string; retryInSeconds?: number };

export interface QuickReply {
  label: string;
  action: string;
}

export interface ChatResponse {
  conversationId: string;
  blocks: Block[];
  quickReplies: QuickReply[];
  state: ChatState;
}
```

---

## 4. Opciones Rápidas de la Vista Usuario

1. **Horario del gimnasio** (HU-CB01): Lun a Vie 6:00 am - 10:00 pm, Sáb 7:00 am - 7:00 pm.
2. **Horario de atención** (HU-CB02): Lun a Sáb 8:00 am - 8:00 pm.
3. **Actividades y cupos** (HU-CB03): Spinning, Funcional y Boxeo con cupos dinámicos calculados para el próximo lunes.
4. **Productos de la tienda** (HU-CB04): Información general de suplementos y accesorios con disponibilidad.
5. **Hablar con una persona** (HU-CB10): Derivación directa a WhatsApp con recepción.

---

## 5. Modo Demo (`DEMO_MODE`)

- **Interruptor rápido**: La constante `DEMO_MODE` en `src/App.tsx` oculta todos los controles de prueba al pasar a `false`.
- **Atajo**: Pulsa `Alt+D` o `Shift+D` para alternar la visibilidad de la barra demo.
- **Funcionalidades**: Permite alternar entre **Vista Escritorio** (400 px flotante) y **Vista Móvil** (100dvh pantalla completa), así como forzar los estados especiales A, B, C, D y E.
