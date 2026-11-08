import React from 'react';

export const GymHeader: React.FC = () => {
  return (
    <header className="w-full bg-white text-slate-800 sticky top-0 z-30 shadow-xs" data-purpose="gym-navigation-bar">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand Logo */}
        <a
          href="#"
          className="flex items-center space-x-1.5 text-2xl lg:text-[28px] font-black italic tracking-tight text-[#DC2626] hover:opacity-90 transition-opacity font-oswald"
          data-purpose="brand-logo"
        >
          <span>Silver Gym Surco</span>
        </a>

        {/* Desktop Navigation Links */}
        <nav
          className="hidden md:flex items-center space-x-7 lg:space-x-10 text-[13px] font-bold tracking-wider text-slate-700 font-inter"
          data-purpose="desktop-nav-links"
        >
          <a href="#servicios" className="hover:text-[#DC2626] transition-colors whitespace-nowrap">
            SERVICIOS
          </a>
          <a href="#nosotros" className="hover:text-[#DC2626] transition-colors whitespace-nowrap">
            NOSOTROS
          </a>
          <a href="#membresias" className="hover:text-[#DC2626] transition-colors whitespace-nowrap">
            MEMBRESÍAS
          </a>
          <a href="#ubicacion" className="hover:text-[#DC2626] transition-colors whitespace-nowrap">
            UBICACIÓN
          </a>
        </nav>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2.5 sm:space-x-3.5" data-purpose="header-cta-group">
          <a
            href="#registro"
            className="bg-[#DC2626] hover:bg-[#B91C1C] text-white text-[12px] font-bold tracking-wider px-5 py-2.5 rounded-full transition-all shadow-sm uppercase font-oswald shrink-0"
          >
            REGISTRARSE
          </a>
          <a
            href="#plataforma"
            className="hidden sm:inline-flex border border-red-300 hover:border-[#DC2626] text-[#DC2626] hover:bg-red-50/50 text-[12px] font-bold tracking-wider px-4 py-2.5 rounded-full transition-all uppercase font-oswald shrink-0"
          >
            ACCESO DIGITAL
          </a>
        </div>
      </div>
    </header>
  );
};
