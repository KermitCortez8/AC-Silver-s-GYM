import React from 'react';

interface ChatLauncherProps {
  onClick: () => void;
  isOpen: boolean;
}

export const ChatLauncher: React.FC<ChatLauncherProps> = ({ onClick, isOpen }) => {
  if (isOpen) return null;

  return (
    <div
      className="fixed bottom-6 right-6 md:bottom-8 md:right-8 z-40 flex items-center"
      data-purpose="floating-chat-trigger"
    >
      <button
        type="button"
        onClick={onClick}
        aria-label="Abrir asistente de IA Pregúntale a Silver"
        className="group relative flex items-center min-h-[48px] bg-[#DC2626] hover:bg-[#B91C1C] text-white rounded-full px-5 py-3 shadow-2xl transition-all duration-300 hover:scale-[1.03] active:scale-95 focus:outline-none focus:ring-4 focus:ring-[#DC2626]/40"
      >
        {/* Chat Bubble Icon */}
        <svg
          aria-hidden="true"
          className="w-5 h-5 mr-2.5 text-white flex-shrink-0"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            fillRule="evenodd"
            clipRule="evenodd"
            d="M4.848 2.771A49.144 49.144 0 0112 2.25c2.43 0 4.817.177 7.152.521 1.944.287 3.348 1.954 3.348 3.924v6.554c0 1.97-1.404 3.637-3.348 3.924a50.944 50.944 0 01-3.655.437v3.09a.75.75 0 01-1.28.53l-3.353-3.352a48.74 48.74 0 01-3.864-.71C4.348 16.35 2.944 14.683 2.944 12.713V6.695c0-1.97 1.404-3.637 3.348-3.924z"
          />
        </svg>

        {/* Label */}
        <span className="text-sm font-bold tracking-wide whitespace-nowrap font-inter">
          Pregúntale a Silver
        </span>
      </button>
    </div>
  );
};
