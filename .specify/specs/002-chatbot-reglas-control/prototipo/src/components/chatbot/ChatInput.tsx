import React, { useState } from 'react';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
  isRateLimited?: boolean;
  rateLimitSeconds?: number;
  onLoginClick?: () => void;
}

const MAX_CHAR_LENGTH = 250;

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  isRateLimited = false,
  rateLimitSeconds = 0,
  onLoginClick,
}) => {
  const [inputText, setInputText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled || isRateLimited) return;
    const trimmed = inputText.trim();
    if (!trimmed) return;
    onSendMessage(trimmed);
    setInputText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isNearLimit = inputText.length > MAX_CHAR_LENGTH * 0.8;

  return (
    <footer
      className="flex-none bg-white border-t border-[#E5E7EB] p-3 pb-safe z-20 space-y-2 w-full"
      data-purpose="chat-input-bar"
    >
      {/* Aviso discreto de inicio de sesión (una sola línea compacta) */}
      <div className="bg-stone-50 border border-gray-100 rounded-lg px-3 py-1.5 text-center text-[11px] text-gray-600 leading-tight flex items-center justify-center gap-1 flex-wrap">
        <span>Inicia sesión para consultar tu membresía e inscribirte</span>
        <span className="text-gray-400">•</span>
        <button
          type="button"
          onClick={onLoginClick}
          className="text-[#DC2626] font-semibold underline hover:text-[#B91C1C] focus:outline-none focus:ring-1 focus:ring-[#DC2626] rounded"
        >
          Iniciar sesión
        </button>
      </div>

      {/* Formulario de entrada de texto */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <label htmlFor="chat-message-input" className="sr-only">
          Escribe tu pregunta
        </label>
        <div className="relative flex-1">
          <input
            id="chat-message-input"
            type="text"
            value={inputText}
            maxLength={MAX_CHAR_LENGTH}
            disabled={disabled || isRateLimited}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isRateLimited
                ? `Bloqueado (${rateLimitSeconds}s)...`
                : 'Escribe tu pregunta…'
            }
            className={`w-full bg-white border border-[#E5E7EB] rounded-2xl px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#DC2626] focus:border-[#DC2626] transition-shadow ${
              isRateLimited ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : ''
            }`}
          />
          {/* Contador de caracteres discreto cuando el usuario escribe */}
          {inputText.length > 0 && (
            <span
              className={`absolute right-3.5 top-2.5 text-[10px] tabular-nums font-medium ${
                isNearLimit ? 'text-amber-600 font-bold' : 'text-gray-400'
              }`}
            >
              {inputText.length}/{MAX_CHAR_LENGTH}
            </span>
          )}
        </div>

        {/* Botón circular de envío (44x44px touch target) con icono avión de papel consistente */}
        <button
          type="submit"
          disabled={disabled || isRateLimited || !inputText.trim()}
          aria-label="Enviar mensaje"
          className={`w-11 h-11 flex-shrink-0 rounded-full flex items-center justify-center shadow-md transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#DC2626] ${
            disabled || isRateLimited || !inputText.trim()
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-[#DC2626] hover:bg-[#B91C1C] active:scale-95 text-white'
          }`}
        >
          <svg
            className="w-5 h-5 translate-x-0.5"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
            />
          </svg>
        </button>
      </form>

      {/* Descargo legal de IA */}
      <p className="text-[11px] text-center text-gray-500 leading-tight" data-purpose="ai-disclaimer">
        Las respuestas son generadas por IA.{' '}
        <a
          href="#privacidad"
          className="underline hover:text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#DC2626] rounded"
        >
          Ver Política de privacidad
        </a>
      </p>
    </footer>
  );
};
