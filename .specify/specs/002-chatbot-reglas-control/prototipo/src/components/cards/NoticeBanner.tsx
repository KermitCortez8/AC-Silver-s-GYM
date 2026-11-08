import React from 'react';

interface NoticeBannerProps {
  kind: 'rate_limit' | 'basic_mode' | 'session_expired';
  text: string;
  retryInSeconds?: number;
  onLoginClick?: () => void;
  onContactClick?: () => void;
}

export const NoticeBanner: React.FC<NoticeBannerProps> = ({
  kind,
  text,
  retryInSeconds,
  onLoginClick,
  onContactClick,
}) => {
  if (kind === 'rate_limit') {
    const seconds = retryInSeconds ?? 40;
    const progressPercent = Math.min(100, Math.max(0, (seconds / 40) * 100));

    return (
      <div
        className="bg-amber-50 border-2 border-amber-400 rounded-2xl p-4 shadow-sm space-y-2.5 w-full text-amber-900"
        role="alert"
        aria-live="polite"
      >
        <div className="flex items-center space-x-2.5 font-bold text-sm">
          <svg
            className="w-5 h-5 text-amber-600 shrink-0 animate-spin"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ animationDuration: '3s' }}
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Límite temporal alcanzado</span>
        </div>
        <p className="text-xs text-amber-800 leading-relaxed">
          {text} Intenta de nuevo en{' '}
          <span className="font-extrabold text-amber-900 text-sm" id="countdown">
            {seconds} s
          </span>
          .
        </p>
        <div className="w-full bg-amber-200 h-1.5 rounded-full overflow-hidden">
          <div
            className="bg-amber-500 h-full rounded-full transition-all duration-1000 ease-linear"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>
    );
  }

  if (kind === 'basic_mode') {
    return (
      <div className="space-y-2.5 w-full">
        {/* Franja superior gris neutra */}
        <div className="bg-gray-800 text-white rounded-xl px-4 py-2.5 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2 text-xs font-bold tracking-wide">
            <span className="text-base" aria-hidden="true">⚙️</span>
            <span>Asistente en modo básico</span>
          </div>
          <span className="text-[10px] bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full font-mono">
            Modo Fallback
          </span>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-3.5 shadow-sm space-y-3 text-xs text-gray-600">
          <p className="leading-relaxed font-medium">
            {text}
          </p>
          {onContactClick && (
            <button
              type="button"
              onClick={onContactClick}
              className="w-full min-h-[44px] bg-[#111111] hover:bg-black text-white font-bold text-xs py-2.5 px-4 rounded-full flex items-center justify-center space-x-2 transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-[#DC2626]"
            >
              <svg className="w-4 h-4 text-[#DC2626]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
              <span>Contactar a recepción</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  if (kind === 'session_expired') {
    return (
      <article className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm text-center space-y-3.5 max-w-sm mx-auto w-full my-2">
        <div className="w-12 h-12 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto border border-red-100 shadow-inner">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <div className="space-y-1">
          <h3 className="font-extrabold text-base text-gray-900 leading-tight">Sesión expirada</h3>
          <p className="text-xs text-gray-600 leading-relaxed">
            {text}
          </p>
        </div>
        <button
          type="button"
          onClick={onLoginClick}
          className="w-full min-h-[44px] bg-[#DC2626] hover:bg-[#B91C1C] active:scale-[0.98] text-white font-extrabold text-xs py-3 px-6 rounded-full shadow-md transition-all uppercase tracking-wider focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#DC2626]"
        >
          Iniciar sesión
        </button>
      </article>
    );
  }

  return null;
};
