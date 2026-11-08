import React from 'react';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useChatbot } from '../../hooks/useChatbot';
import { ChatState, QuickReply } from '../../types/chat';

interface ChatWindowProps {
  isOpen: boolean;
  onClose: () => void;
  forceMobileView?: boolean;
  forcedState?: ChatState;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  isOpen,
  onClose,
  forceMobileView = false,
}) => {
  const {
    messages,
    quickReplies,
    isTyping,
    isSlow,
    isRateLimited,
    rateLimitSeconds,
    sendMessage,
    retryLastMessage,
    contactHuman,
  } = useChatbot(isOpen, onClose);

  if (!isOpen) return null;

  const handleSelectQuickReply = (option: QuickReply) => {
    sendMessage(undefined, option.action);
  };

  const handleSendMessage = (text: string) => {
    sendMessage(text);
  };

  const handleLoginClick = () => {
    // Simula inicio de sesión o redirección
    alert('Redirigiendo a la pantalla de Inicio de Sesión de Silver Gym Surco...');
  };

  // Clases condicionales según vista móvil forzada o responsive real
  const containerClasses = forceMobileView
    ? 'fixed inset-0 z-50 bg-black/60 md:flex md:items-center md:justify-center p-0 md:p-4'
    : 'fixed inset-0 z-50 md:inset-auto md:bottom-6 md:right-8 bg-black/40 md:bg-transparent md:pointer-events-none flex flex-col justify-end md:block';

  const windowClasses = forceMobileView
    ? 'w-full h-[100dvh] md:h-[844px] md:max-w-[414px] bg-white flex flex-col md:rounded-[32px] shadow-2xl overflow-hidden border border-gray-200 pointer-events-auto relative'
    : 'w-full h-[100dvh] md:w-[400px] md:h-[680px] md:max-h-[calc(100vh-40px)] bg-white flex flex-col md:rounded-2xl shadow-2xl border border-gray-200 pointer-events-auto overflow-hidden relative';

  return (
    <aside
      aria-label="Asistente Virtual Silver Gym Surco"
      className={containerClasses}
      id="silver-chatbot"
    >
      <div className={windowClasses} data-purpose="chat-viewport">
        {/* Cabecera unificada */}
        <ChatHeader onClose={onClose} />

        {/* Área de mensajes con scroll automático y aria-live */}
        <MessageList
          messages={messages}
          isTyping={isTyping}
          isSlow={isSlow}
          quickReplies={quickReplies}
          onSelectQuickReply={handleSelectQuickReply}
          onRetry={retryLastMessage}
          onContactHuman={contactHuman}
          onLoginClick={handleLoginClick}
        />

        {/* Pie con aviso de sesión, entrada de texto y aviso de IA */}
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isTyping}
          isRateLimited={isRateLimited}
          rateLimitSeconds={rateLimitSeconds}
          onLoginClick={handleLoginClick}
        />
      </div>
    </aside>
  );
};
