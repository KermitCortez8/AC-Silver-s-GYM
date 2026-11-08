import React, { useState, useEffect } from 'react';
import { ChatState } from '../../types/chat';

interface DemoToolbarProps {
  demoMode: boolean;
  forceMobileView: boolean;
  onToggleMobileView: () => void;
  onForceState: (state: ChatState) => void;
  currentState: ChatState;
}

export const DemoToolbar: React.FC<DemoToolbarProps> = ({
  demoMode,
  forceMobileView,
  onToggleMobileView,
  onForceState,
  currentState,
}) => {
  const [isVisible, setIsVisible] = useState<boolean>(false);

  // Atajo de teclado: Alt+D o Shift+D para alternar visibilidad de la barra demo
  useEffect(() => {
    if (!demoMode) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.altKey || e.shiftKey) && (e.key === 'd' || e.key === 'D')) {
        e.preventDefault();
        setIsVisible((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [demoMode]);

  // Si DEMO_MODE está apagado, no renderizar nada
  if (!demoMode) return null;

  return (
    <div className="fixed top-3 left-3 md:left-6 z-50 flex flex-col items-start gap-1 font-sans">
      {/* Botón discreto para desplegar el panel o atajo */}
      <button
        type="button"
        onClick={() => setIsVisible(!isVisible)}
        className="bg-neutral-900/90 hover:bg-neutral-900 text-white text-[11px] font-mono px-3 py-1.5 rounded-full backdrop-blur-md border border-neutral-700 shadow-md flex items-center gap-1.5 transition-all active:scale-95"
        title="Alternar panel demo (Atajo: Alt+D)"
      >
        <span className="w-2 h-2 rounded-full bg-[#DC2626]" />
        <span>DEMO CONTROLS</span>
        <span className="text-[10px] text-gray-400 bg-neutral-800 px-1.5 py-0.2 rounded">Alt+D</span>
      </button>

      {/* Contenedor del panel demo */}
      {isVisible && (
        <div
          className="mt-1 bg-white/95 backdrop-blur-md border border-gray-200 rounded-2xl p-3 shadow-2xl max-w-sm w-full space-y-2.5 text-gray-800 transition-all text-xs"
          role="region"
          aria-label="Controles de prueba y estados especiales"
        >
          {/* Header del panel */}
          <div className="flex items-center justify-between pb-1.5 border-b border-gray-100">
            <span className="font-bold text-gray-900 uppercase tracking-wider text-[11px] font-oswald">
              Simulador de Estados (DEMO)
            </span>
            <button
              type="button"
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-gray-600 text-sm font-bold px-1"
              aria-label="Cerrar panel demo"
            >
              ✕
            </button>
          </div>

          {/* Interruptor de Vista: Escritorio vs Móvil */}
          <div className="flex items-center justify-between bg-stone-100 p-1.5 rounded-xl">
            <span className="font-semibold text-gray-700 text-[11px]">Modo de Vista:</span>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => forceMobileView && onToggleMobileView()}
                className={`px-2.5 py-1 rounded-lg font-medium text-[11px] transition-all ${
                  !forceMobileView
                    ? 'bg-white text-gray-900 shadow-xs font-bold'
                    : 'text-gray-500 hover:text-gray-800'
                }`}
              >
                Escritorio
              </button>
              <button
                type="button"
                onClick={() => !forceMobileView && onToggleMobileView()}
                className={`px-2.5 py-1 rounded-lg font-medium text-[11px] transition-all ${
                  forceMobileView
                    ? 'bg-[#DC2626] text-white shadow-xs font-bold'
                    : 'text-gray-500 hover:text-gray-800'
                }`}
              >
                Móvil (100dvh)
              </button>
            </div>
          </div>

          {/* Selectores de Estados Especiales */}
          <div className="space-y-1.5">
            <span className="font-semibold text-gray-700 text-[11px] block">Forzar Estado Especial:</span>
            <div className="grid grid-cols-2 gap-1.5">
              <button
                type="button"
                onClick={() => onForceState('ok')}
                className={`px-2 py-1.5 rounded-lg border text-left text-[11px] font-medium transition-all ${
                  currentState === 'ok'
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-800 font-bold'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                ✓ Normal (OK)
              </button>
              <button
                type="button"
                onClick={() => onForceState('forbidden')}
                className={`px-2 py-1.5 rounded-lg border text-left text-[11px] font-medium transition-all ${
                  currentState === 'forbidden'
                    ? 'bg-red-50 border-red-300 text-red-800 font-bold'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                A: Restringido
              </button>
              <button
                type="button"
                onClick={() => onForceState('rate_limited')}
                className={`px-2 py-1.5 rounded-lg border text-left text-[11px] font-medium transition-all ${
                  currentState === 'rate_limited'
                    ? 'bg-amber-50 border-amber-300 text-amber-800 font-bold'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                B: Límite msgs
              </button>
              <button
                type="button"
                onClick={() => onForceState('slow')}
                className={`px-2 py-1.5 rounded-lg border text-left text-[11px] font-medium transition-all ${
                  currentState === 'slow'
                    ? 'bg-blue-50 border-blue-300 text-blue-800 font-bold'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                C: Demora &gt;15s
              </button>
              <button
                type="button"
                onClick={() => onForceState('basic_mode')}
                className={`px-2 py-1.5 rounded-lg border text-left text-[11px] font-medium transition-all ${
                  currentState === 'basic_mode'
                    ? 'bg-gray-100 border-gray-400 text-gray-900 font-bold'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                D: Modo Básico
              </button>
              <button
                type="button"
                onClick={() => onForceState('session_expired')}
                className={`px-2 py-1.5 rounded-lg border text-left text-[11px] font-medium transition-all ${
                  currentState === 'session_expired'
                    ? 'bg-red-50 border-red-300 text-red-800 font-bold'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                E: Sesión Expirada
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
