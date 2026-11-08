import React from 'react';

interface BotMessageProps {
  text: string;
}

export const BotMessage: React.FC<BotMessageProps> = ({ text }) => {
  return (
    <article className="space-y-1 w-full text-left" data-purpose="bot-message">
      <div className="text-[14.5px] leading-relaxed text-gray-800 whitespace-pre-line font-normal pr-2">
        {text}
      </div>
    </article>
  );
};
