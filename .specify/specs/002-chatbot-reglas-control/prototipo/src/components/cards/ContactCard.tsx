import React from 'react';

interface ContactCardProps {
  phone?: string;
  whatsappUrl?: string;
  attentionHours?: string;
}

export const ContactCard: React.FC<ContactCardProps> = ({
  phone = '+51 987 654 321',
  whatsappUrl = 'https://wa.me/51987654321?text=Hola,%20quisiera%20realizar%20una%20consulta%20con%20recepci%C3%B3n',
  attentionHours = 'Lun a Sáb de 8:00 am a 8:00 pm',
}) => {
  return (
    <article
      className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm space-y-3.5 w-full pt-1"
      data-purpose="contact-card"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-11 h-11 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center text-[#DC2626] shrink-0">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <div>
            <h3 className="font-bold text-gray-900 text-sm leading-tight">Atención al Cliente Silver Gym</h3>
            <p className="text-xs text-gray-500 mt-0.5">Sede Surco - Recepción Central</p>
          </div>
        </div>
      </div>

      <div className="bg-stone-50 border border-gray-100 rounded-xl p-2.5 text-xs text-gray-600 flex items-center space-x-2">
        <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>
          <strong>Atención:</strong> {attentionHours}
        </span>
      </div>

      {/* Botón de apertura a WhatsApp */}
      <a
        href={whatsappUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center justify-center w-full min-h-[44px] bg-[#25D366] hover:bg-[#20ba5a] active:scale-[0.98] text-white font-bold text-sm py-2.5 px-4 rounded-full shadow-sm transition-all space-x-2 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#25D366]"
        aria-label="Abrir WhatsApp para contactar con recepción"
      >
        <svg className="w-4 h-4 fill-current shrink-0" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981z" />
        </svg>
        <span>Abrir WhatsApp</span>
      </a>
    </article>
  );
};
