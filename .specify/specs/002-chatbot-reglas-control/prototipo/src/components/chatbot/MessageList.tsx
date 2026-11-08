import React, { useEffect, useRef } from 'react';
import { ChatMessage, QuickReply } from '../../types/chat';
import { BotMessage } from './BotMessage';
import { UserMessage } from './UserMessage';
import { TypingIndicator } from './TypingIndicator';
import { QuickReplies } from './QuickReplies';
import { ScheduleCard } from '../cards/ScheduleCard';
import { ProductCardBasic } from '../cards/ProductCardBasic';
import { ContactCard } from '../cards/ContactCard';
import { NoticeBanner } from '../cards/NoticeBanner';

interface MessageListProps {
  messages: ChatMessage[];
  isTyping: boolean;
  isSlow: boolean;
  quickReplies: QuickReply[];
  onSelectQuickReply: (option: QuickReply) => void;
  onRetry: () => void;
  onContactHuman: () => void;
  onLoginClick?: () => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isTyping,
  isSlow,
  quickReplies,
  onSelectQuickReply,
  onRetry,
  onContactHuman,
  onLoginClick,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll al último mensaje
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, isSlow]);

  return (
    <main
      className="flex-1 overflow-y-auto chat-scrollbar bg-[#FAF9F6] px-4 py-4 space-y-4"
      aria-live="polite"
      aria-atomic="false"
      data-purpose="chat-history"
    >
      {/* Timestamp / Context divider */}
      <div className="text-center my-1">
        <span className="text-[11px] font-medium text-gray-400 bg-white/90 px-3 py-1 rounded-full border border-gray-100 shadow-xs">
          Hoy en Silver Gym Surco
        </span>
      </div>

      {messages.map((message) => {
        if (message.sender === 'user') {
          return <UserMessage key={message.id} text={message.text || ''} />;
        }

        // Mensaje del Bot: renderiza bloques tipados
        return (
          <div key={message.id} className="space-y-3 w-full" data-purpose="bot-message-wrapper">
            {message.blocks?.map((block, idx) => {
              switch (block.type) {
                case 'text':
                  return <BotMessage key={idx} text={block.text} />;

                case 'schedule_list':
                  return <ScheduleCard key={idx} items={block.items} />;

                case 'product_basic_list':
                  return <ProductCardBasic key={idx} items={block.items} />;

                case 'contact':
                  return (
                    <ContactCard
                      key={idx}
                      phone={block.phone}
                      whatsappUrl={block.whatsappUrl}
                      attentionHours={block.attentionHours}
                    />
                  );

                case 'notice':
                  return (
                    <NoticeBanner
                      key={idx}
                      kind={block.kind}
                      text={block.text}
                      retryInSeconds={block.retryInSeconds}
                      onLoginClick={onLoginClick}
                      onContactClick={onContactHuman}
                    />
                  );

                default:
                  return null;
              }
            })}
          </div>
        );
      })}

      {/* Indicador de escritura */}
      {isTyping && <TypingIndicator />}

      {/* Estado C: Aviso automático por demora prolongada (> 15s) */}
      {isSlow && (
        <article
          className="bg-stone-100 border border-stone-200 rounded-2xl p-4 shadow-xs space-y-3 max-w-[95%] w-full"
          data-purpose="slow-response-alert"
        >
          <p className="text-sm text-gray-800 font-medium">
            Está tardando más de lo normal. ¿Quieres intentar de nuevo o hablar con una persona?
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center min-h-[44px] bg-white hover:bg-gray-50 text-gray-800 border border-gray-300 font-semibold text-xs px-4 py-2 rounded-full shadow-xs active:scale-95 transition-all focus:outline-none focus:ring-2 focus:ring-[#DC2626]"
            >
              <svg className="w-3.5 h-3.5 mr-1.5 text-gray-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Reintentar
            </button>
            <button
              type="button"
              onClick={onContactHuman}
              className="inline-flex items-center min-h-[44px] bg-[#DC2626] hover:bg-[#B91C1C] text-white font-semibold text-xs px-4 py-2 rounded-full shadow-xs active:scale-95 transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#DC2626]"
            >
              <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Hablar con una persona
            </button>
          </div>
        </article>
      )}

      {/* Opciones rápidas interactivas: 5 píldoras apiladas */}
      {!isTyping && quickReplies.length > 0 && (
        <QuickReplies
          options={quickReplies}
          onSelect={onSelectQuickReply}
          disabled={isTyping}
        />
      )}

      {/* Elemento ancla para auto-scroll */}
      <div ref={messagesEndRef} className="h-1" />
    </main>
  );
};
