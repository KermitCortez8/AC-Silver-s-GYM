import React from 'react';

interface GymHeroProps {
  onOpenChat: () => void;
}

export const GymHero: React.FC<GymHeroProps> = ({ onOpenChat }) => {
  return (
    <section className="relative min-h-[calc(100vh-80px)] flex flex-col justify-between overflow-hidden bg-black text-white" data-purpose="hero-section">
      {/* Background Hero Image */}
      <div className="absolute inset-0 z-0">
        <img
          src="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1920&q=80"
          alt="Silver Gym Surco - Entrenamiento y Disciplina"
          className="w-full h-full object-cover object-right md:object-center select-none pointer-events-none brightness-75"
        />
        {/* Gradients */}
        <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 md:via-black/60 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-black/30" />
      </div>

      {/* Hero Content */}
      <div className="relative z-10 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-12 md:pt-20 lg:pt-24 pb-12 flex-1 flex flex-col justify-center">
        <div className="max-w-2xl">
          {/* Tagline */}
          <div className="flex items-center space-x-2.5 mb-3" data-purpose="hero-tagline">
            <span className="w-5 h-[2px] bg-[#DC2626] inline-block" />
            <span className="text-[#DC2626] font-bold text-xs sm:text-sm tracking-widest uppercase font-oswald">
              GIMNASIO · SALUD Y DISCIPLINA
            </span>
          </div>

          {/* Headline */}
          <h1 className="font-oswald text-4xl sm:text-6xl lg:text-7xl leading-[0.98] tracking-tight uppercase mb-5">
            <span className="block text-white">Entrena fuerte,</span>
            <span className="block text-[#DC2626]">cerca de casa.</span>
          </h1>

          {/* Subtitle */}
          <p className="text-gray-300 text-sm sm:text-base leading-relaxed max-w-xl mb-8 font-inter">
            En Silver Gym Surco ofrecemos entrenamiento funcional, musculación, cardio y clases grupales con horarios pensados para tu rutina diaria.
          </p>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-3.5 mb-12" data-purpose="hero-buttons">
            <button
              type="button"
              onClick={onOpenChat}
              className="bg-[#DC2626] hover:bg-[#B91C1C] text-white text-xs sm:text-sm font-bold tracking-wider px-7 py-3.5 rounded-full transition-all duration-200 uppercase inline-flex items-center justify-center font-oswald shadow-lg"
            >
              PREGÚNTALE A SILVER
            </button>
            <a
              href="#registro"
              className="bg-white hover:bg-gray-100 text-slate-900 text-xs sm:text-sm font-bold tracking-wider px-6 py-3.5 rounded-full transition-all duration-200 uppercase inline-flex items-center justify-center shadow-lg font-oswald"
            >
              REGISTRARME AHORA
            </a>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-3 max-w-md pt-4 border-t border-white/10" data-purpose="hero-metrics">
            <div className="pr-3">
              <span className="block text-[11px] font-bold text-[#DC2626] uppercase tracking-wider mb-1 font-oswald">
                HORARIO
              </span>
              <span className="block text-sm sm:text-base font-bold text-white tracking-wide">
                Lun a Sáb
              </span>
            </div>
            <div className="px-3 border-l border-white/10">
              <span className="block text-[11px] font-bold text-[#DC2626] uppercase tracking-wider mb-1 font-oswald">
                SERVICIOS
              </span>
              <span className="block text-sm sm:text-base font-bold text-white tracking-wide">
                4 áreas
              </span>
            </div>
            <div className="pl-3 border-l border-white/10">
              <span className="block text-[11px] font-bold text-[#DC2626] uppercase tracking-wider mb-1 font-oswald">
                ASISTENTE
              </span>
              <span className="block text-sm sm:text-base font-bold text-white tracking-wide">
                Con IA
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
