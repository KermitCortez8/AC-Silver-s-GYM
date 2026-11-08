import React from 'react';

interface ChatHeaderProps {
  onClose: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ onClose }) => {
  return (
    <header
      className="flex-none bg-white border-b border-[#E5E7EB] px-5 py-3 pt-safe flex items-center justify-between z-20"
      data-purpose="chat-header"
    >
      {/* Identidad Silver Gym Surco */}
      <div className="flex flex-col">
        <div className="flex items-center space-x-1">
          <span className="font-oswald text-2xl font-black italic tracking-wide uppercase text-[#111111] leading-none">
            Silver
          </span>
        </div>
        <p className="text-xs text-gray-500 font-medium mt-0.5">
          Asistente virtual con IA
        </p>
      </div>

      {/* Botón Cerrar (44x44px target) */}
      <button
        type="button"
        onClick={onClose}
        aria-label="Cerrar ventana de chat"
        className="w-11 h-11 flex items-center justify-center -mr-2 rounded-full text-gray-400 hover:text-gray-900 hover:bg-gray-100 active:bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-[#DC2626]"
      >
        <svg
          className="w-5 h-5 stroke-current stroke-[2.2]"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </header>
  );
};
