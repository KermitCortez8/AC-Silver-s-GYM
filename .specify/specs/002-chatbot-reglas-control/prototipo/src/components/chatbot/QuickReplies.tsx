import React from 'react';
import { QuickReply } from '../../types/chat';

interface QuickRepliesProps {
  options: QuickReply[];
  onSelect: (option: QuickReply) => void;
  disabled?: boolean;
}

export const QuickReplies: React.FC<QuickRepliesProps> = ({ options, onSelect, disabled = false }) => {
  if (!options || options.length === 0) return null;

  return (
    <nav
      aria-label="Opciones rápidas"
      className="flex flex-col items-start gap-2 pt-1 pb-2 w-full"
      data-purpose="quick-replies"
    >
      <p className="text-xs font-semibold text-gray-500 mb-1">Opciones rápidas:</p>
      {options.map((option) => (
        <button
          key={option.action}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(option)}
          className={`w-fit max-w-[95%] text-left px-4 py-2.5 min-h-[44px] bg-[#DC2626] hover:bg-[#B91C1C] active:scale-[0.98] text-white text-xs sm:text-sm font-semibold rounded-full shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#DC2626] flex items-center justify-between gap-2 ${
            disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
          }`}
        >
          <span>{option.label}</span>
          {option.action === 'contact_human' && (
            <svg
              className="w-3.5 h-3.5 shrink-0 ml-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          )}
        </button>
      ))}
    </nav>
  );
};
