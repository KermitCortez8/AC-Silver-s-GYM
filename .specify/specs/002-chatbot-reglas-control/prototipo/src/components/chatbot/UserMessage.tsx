import React from 'react';

interface UserMessageProps {
  text: string;
}

export const UserMessage: React.FC<UserMessageProps> = ({ text }) => {
  return (
    <article className="flex justify-end pt-1 w-full" data-purpose="user-message">
      <div className="max-w-[85%] bg-[#DC2626] text-white px-4 py-2.5 rounded-2xl rounded-tr-sm shadow-sm">
        <p className="text-[14px] leading-snug break-words">
          {text}
        </p>
      </div>
    </article>
  );
};
