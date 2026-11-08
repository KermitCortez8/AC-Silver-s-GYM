import { ChatResponse, QuickReply, ScheduleItem, ProductBasic, SendMessageParams, ChatState } from '../types/chat';
import { ChatService } from './chatService';

/**
 * Calcula dinámicamente el próximo lunes a partir de la fecha actual del sistema.
 * Ejemplo: "Lunes 9 de Febrero"
 */
export function getNextMondayFormatted(): string {
  const today = new Date();
  const dayOfWeek = today.getDay(); // 0: domingo, 1: lunes, ..., 6: sábado
  // Si hoy es lunes (1), el próximo lunes es en 7 días; en cualquier otro caso calculamos los días restantes
  const daysUntilNextMonday = dayOfWeek === 1 ? 7 : (8 - dayOfWeek) % 7;
  const nextMonday = new Date(today);
  nextMonday.setDate(today.getDate() + (daysUntilNextMonday === 0 ? 7 : daysUntilNextMonday));

  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];

  const dia = nextMonday.getDate();
  const mes = meses[nextMonday.getMonth()];
  return `Lunes ${dia} de ${mes}`;
}

const DEFAULT_QUICK_REPLIES: QuickReply[] = [
  { label: 'Horario del gimnasio', action: 'gym_hours' },
  { label: 'Horario de atención', action: 'attention_hours' },
  { label: 'Actividades y cupos', action: 'activities' },
  { label: 'Productos de la tienda', action: 'products' },
  { label: 'Hablar con una persona', action: 'contact_human' },
];

export class MockChatService implements ChatService {
  private failedAttempts: number = 0;

  public getInitialMessage(conversationId: string): ChatResponse {
    return {
      conversationId,
      blocks: [
        {
          type: 'text',
          text: 'Hola, soy Silver, el asistente con IA de Silver Gym Surco. Puedo ayudarte con horarios, actividades, productos y cómo contactarnos. ¿En qué te ayudo hoy?',
        },
      ],
      quickReplies: DEFAULT_QUICK_REPLIES,
      state: 'ok',
    };
  }

  public async sendMessage(params: SendMessageParams): Promise<ChatResponse> {
    const { conversationId, text = '', action, forcedState } = params;

    // Simulación de latencia realista entre 600 y 1200 ms
    const latency = Math.floor(Math.random() * 600) + 600;
    await new Promise((resolve) => setTimeout(resolve, latency));

    // Si se fuerza un estado especial desde el panel de pruebas (DEMO_MODE)
    if (forcedState && forcedState !== 'ok') {
      return this.handleForcedState(conversationId, forcedState);
    }

    const normalizedText = text.trim().toLowerCase();
    const cleanAction = action || this.detectAction(normalizedText);

    // 1. Detección de datos sensibles (contraseñas, tarjetas)
    if (this.containsSensitiveData(normalizedText)) {
      return {
        conversationId,
        blocks: [
          {
            type: 'text',
            text: '⚠️ Por tu seguridad, no compartas contraseñas, números de tarjeta ni datos bancarios por el chat. Ningún dato confidencial ha sido almacenado.',
          },
        ],
        quickReplies: DEFAULT_QUICK_REPLIES,
        state: 'ok',
      };
    }

    // 2. Acciones no permitidas (congelar, activar membresía, cambiar precios, confirmar pagos) - HU-CB13 / Estado A
    if (this.isForbiddenAction(normalizedText, cleanAction)) {
      return {
        conversationId,
        blocks: [
          {
            type: 'text',
            text: 'Esta gestión debe realizarse directamente con nuestro equipo administrativo en recepción o atención al cliente.',
          },
          {
            type: 'contact',
            phone: '+51 987 654 321',
            whatsappUrl: 'https://wa.me/51987654321?text=Hola,%20quisiera%20realizar%20una%20consulta%20con%20recepci%C3%B3n',
            attentionHours: 'Lun a Sáb de 8:00 am a 8:00 pm',
          },
        ],
        quickReplies: DEFAULT_QUICK_REPLIES,
        state: 'forbidden',
      };
    }

    // 3. Petición de datos personales o privados en vista usuario - HU-CB11
    if (this.isPersonalDataRequest(normalizedText)) {
      return {
        conversationId,
        blocks: [
          {
            type: 'text',
            text: 'Para consultar información de tu membresía, historial de reservas o pedidos, necesitas iniciar sesión con tu cuenta registrada en Silver Gym Surco.',
          },
        ],
        quickReplies: DEFAULT_QUICK_REPLIES,
        state: 'ok',
      };
    }

    // 4. Consulta de cómo inscribirse a clases
    if (normalizedText.includes('inscribir') || normalizedText.includes('inscripción') || normalizedText.includes('reserva')) {
      return {
        conversationId,
        blocks: [
          {
            type: 'text',
            text: 'La inscripción a actividades grupales está disponible para clientes con membresía activa iniciando sesión en la plataforma o de manera presencial en recepción.',
          },
          {
            type: 'contact',
            phone: '+51 987 654 321',
            whatsappUrl: 'https://wa.me/51987654321?text=Hola,%20deseo%20inscribirme%20en%20una%20actividad',
            attentionHours: 'Lun a Sáb de 8:00 am a 8:00 pm',
          },
        ],
        quickReplies: DEFAULT_QUICK_REPLIES,
        state: 'ok',
      };
    }

    // 5. Manejo según acción
    switch (cleanAction) {
      case 'gym_hours':
        this.failedAttempts = 0;
        return {
          conversationId,
          blocks: [
            {
              type: 'text',
              text: 'Estamos abiertos en los siguientes horarios para entrenamiento:',
            },
            {
              type: 'text',
              text: '• Lunes a Viernes: 6:00 am - 10:00 pm\n• Sábados: 7:00 am - 7:00 pm\n(Domingos cerrado por mantenimiento general)',
            },
          ],
          quickReplies: DEFAULT_QUICK_REPLIES,
          state: 'ok',
        };

      case 'attention_hours':
        this.failedAttempts = 0;
        return {
          conversationId,
          blocks: [
            {
              type: 'text',
              text: 'El horario de atención en recepción y administración es de Lunes a Sábado de 8:00 am a 8:00 pm. Puedes realizar trámites, consultas y pagos en ese rango.',
            },
          ],
          quickReplies: DEFAULT_QUICK_REPLIES,
          state: 'ok',
        };

      case 'activities': {
        this.failedAttempts = 0;
        const dynamicDay = getNextMondayFormatted();
        const scheduleItems: ScheduleItem[] = [
          {
            id: 'act-1',
            service: 'SPINNING',
            day: dynamicDay,
            start: '7:00 am',
            end: '8:00 am',
            slotsLeft: 3,
          },
          {
            id: 'act-2',
            service: 'FUNCIONAL',
            day: dynamicDay,
            start: '6:00 pm',
            end: '7:00 pm',
            slotsLeft: 0, // Completo
          },
          {
            id: 'act-3',
            service: 'BOXEO & CARDIO',
            day: dynamicDay,
            start: '7:30 pm',
            end: '8:30 pm',
            slotsLeft: 5,
          },
        ];
        return {
          conversationId,
          blocks: [
            {
              type: 'text',
              text: `Estas son las actividades grupales programadas para el ${dynamicDay} en Silver Gym Surco:`,
            },
            {
              type: 'schedule_list',
              items: scheduleItems,
            },
          ],
          quickReplies: DEFAULT_QUICK_REPLIES,
          state: 'ok',
        };
      }

      case 'products': {
        this.failedAttempts = 0;
        const products: ProductBasic[] = [
          {
            id: 'prod-1',
            name: 'Proteína Whey Isolate 2kg',
            category: 'Suplementos & Nutrición',
            imageUrl: 'https://images.unsplash.com/photo-1593095948071-474c5cc2989d?auto=format&fit=crop&w=400&q=80',
            available: true,
          },
          {
            id: 'prod-2',
            name: 'Creatina Monohidratada 300g',
            category: 'Fuerza & Rendimiento',
            imageUrl: 'https://images.unsplash.com/photo-1579722821273-0f6c7d44362f?auto=format&fit=crop&w=400&q=80',
            available: true,
          },
          {
            id: 'prod-3',
            name: 'Shaker Oficial Silver 750ml',
            category: 'Accesorios',
            imageUrl: 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=400&q=80',
            available: false, // Agotado
          },
          {
            id: 'prod-4',
            name: 'Straps de Levantamiento Pesado',
            category: 'Accesorios',
            imageUrl: 'https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=400&q=80',
            available: true,
          },
        ];
        return {
          conversationId,
          blocks: [
            {
              type: 'text',
              text: 'Aquí tienes un resumen general de los productos disponibles en la tienda de Silver Gym Surco. (Para ver precios y realizar pedidos inicia sesión o acércate a recepción):',
            },
            {
              type: 'product_basic_list',
              items: products,
            },
          ],
          quickReplies: DEFAULT_QUICK_REPLIES,
          state: 'ok',
        };
      }

      case 'contact_human':
        this.failedAttempts = 0;
        return {
          conversationId,
          blocks: [
            {
              type: 'text',
              text: 'Con gusto te comunicamos con nuestro equipo de atención al cliente de la sede Surco:',
            },
            {
              type: 'contact',
              phone: '+51 987 654 321',
              whatsappUrl: 'https://wa.me/51987654321?text=Hola,%20necesito%20asistencia%20de%20un%20asesor%20de%20Silver%20Gym%20Surco',
              attentionHours: 'Lun a Sáb de 8:00 am a 8:00 pm',
            },
          ],
          quickReplies: DEFAULT_QUICK_REPLIES,
          state: 'ok',
        };

      default:
        // Mensaje no entendido
        this.failedAttempts += 1;
        if (this.failedAttempts >= 2) {
          this.failedAttempts = 0;
          return {
            conversationId,
            blocks: [
              {
                type: 'text',
                text: 'No logré entender completamente tu consulta. Para brindarte una mejor atención, te dejo nuestro canal directo de WhatsApp:',
              },
              {
                type: 'contact',
                phone: '+51 987 654 321',
                whatsappUrl: 'https://wa.me/51987654321?text=Hola,%20tengo%20una%20consulta%20sobre%20Silver%20Gym%20Surco',
                attentionHours: 'Lun a Sáb de 8:00 am a 8:00 pm',
              },
            ],
            quickReplies: DEFAULT_QUICK_REPLIES,
            state: 'ok',
          };
        }

        return {
          conversationId,
          blocks: [
            {
              type: 'text',
              text: 'Disculpa, como asistente virtual solo puedo responder consultas sobre horarios, actividades grupales, productos de la tienda y derivación a recepción. Puedes elegir una opción rápida:',
            },
          ],
          quickReplies: DEFAULT_QUICK_REPLIES,
          state: 'ok',
        };
    }
  }

  private handleForcedState(conversationId: string, state: ChatState): ChatResponse {
    switch (state) {
      case 'forbidden':
        return {
          conversationId,
          blocks: [
            {
              type: 'text',
              text: 'Esta gestión debe realizarse directamente con nuestro equipo administrativo en recepción o atención al cliente.',
            },
            {
              type: 'contact',
              phone: '+51 987 654 321',
              whatsappUrl: 'https://wa.me/51987654321?text=Consulta%20administrativa%20Silver%20Gym%20Surco',
              attentionHours: 'Lun a Sáb de 8:00 am a 8:00 pm',
            },
          ],
          quickReplies: DEFAULT_QUICK_REPLIES,
          state: 'forbidden',
        };

      case 'rate_limited':
        return {
          conversationId,
          blocks: [
            {
              type: 'notice',
              kind: 'rate_limit',
              text: 'Enviaste muchos mensajes. Por seguridad del sistema implementamos un control de flujo.',
              retryInSeconds: 40,
            },
          ],
          quickReplies: [],
          state: 'rate_limited',
        };

      case 'slow':
        return {
          conversationId,
          blocks: [
            {
              type: 'text',
              text: 'Está tardando más de lo normal. ¿Quieres intentar de nuevo o hablar con una persona?',
            },
          ],
          quickReplies: [
            { label: 'Reintentar', action: 'retry_last' },
            { label: 'Hablar con una persona', action: 'contact_human' },
          ],
          state: 'slow',
        };

      case 'basic_mode':
        return {
          conversationId,
          blocks: [
            {
              type: 'notice',
              kind: 'basic_mode',
              text: 'Nuestros servicios avanzados están en mantenimiento temporal. Puedes usar las opciones rápidas:',
            },
          ],
          quickReplies: DEFAULT_QUICK_REPLIES,
          state: 'basic_mode',
        };

      case 'session_expired':
        return {
          conversationId,
          blocks: [
            {
              type: 'notice',
              kind: 'session_expired',
              text: 'Tu sesión terminó por inactividad. Inicia sesión para continuar consultando tus datos.',
            },
          ],
          quickReplies: [],
          state: 'session_expired',
        };

      default:
        return this.getInitialMessage(conversationId);
    }
  }

  private detectAction(text: string): string | undefined {
    if (text.includes('horario del gym') || text.includes('horario del gimnasio') || (text.includes('horario') && text.includes('apertura')) || (text.includes('a qué hora') && text.includes('abren'))) {
      return 'gym_hours';
    }
    if (text.includes('atención') || text.includes('recepción') || text.includes('trámite') || text.includes('horario de atencion')) {
      return 'attention_hours';
    }
    if (text.includes('actividad') || text.includes('cupo') || text.includes('clase') || text.includes('spinning') || text.includes('funcional')) {
      return 'activities';
    }
    if (text.includes('producto') || text.includes('tienda') || text.includes('proteina') || text.includes('creatina') || text.includes('suplemento')) {
      return 'products';
    }
    if (text.includes('persona') || text.includes('humano') || text.includes('whatsapp') || text.includes('asesor') || text.includes('hablar con')) {
      return 'contact_human';
    }
    return undefined;
  }

  private isForbiddenAction(text: string, action?: string): boolean {
    const forbiddenPhrases = [
      'congelar',
      'congelamiento',
      'activar membresia',
      'activar membresía',
      'cambiar precio',
      'cambiar precios',
      'confirmar pago',
      'confirmar pagos',
      'anular pago',
      'descuento especial',
      'editar datos',
    ];
    return forbiddenPhrases.some((phrase) => text.includes(phrase));
  }

  private isPersonalDataRequest(text: string): boolean {
    const personalPhrases = [
      'mi membresía',
      'mi membresia',
      'mi dni',
      'mis datos',
      'mis reservas',
      'mis inscripciones',
      'mi pedido',
      'estado de mi pedido',
      'cuánto me queda de plan',
      'cuanto me queda',
      'ver mi cuenta',
      'consultar dni',
    ];
    return personalPhrases.some((phrase) => text.includes(phrase));
  }

  private containsSensitiveData(text: string): boolean {
    // Patrón de contraseña o números de tarjeta (16 dígitos o grupos de 4)
    const cardPattern = /\b(?:\d{4}[ -]?){3}\d{4}\b/;
    const passwordPattern = /(password|contraseña|clave|pin|cvv|cvc)[:= ]+\S+/i;
    return cardPattern.test(text) || passwordPattern.test(text);
  }
}
