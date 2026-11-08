import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div
      aria-label="El asistente está redactando una respuesta"
      className="flex items-center space-x-1.5 bg-white border border-gray-200 rounded-full px-4 py-2.5 w-fit shadow-xs my-1"
      data-purpose="typing-indicator"
    >
      <span className="w-2 h-2 rounded-full bg-[#DC2626] typing-dot-1" />
      <span className="w-2 h-2 rounded-full bg-gray-400 typing-dot-2" />
      <span className="w-2 h-2 rounded-full bg-[#DC2626] typing-dot-3" />
      <span className="text-xs text-gray-500 font-medium ml-1.5">Pensando respuesta...</span>
    </div>
  );
};
