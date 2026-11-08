import React from 'react';
import { ScheduleItem } from '../../types/chat';

interface ScheduleCardProps {
  items: ScheduleItem[];
}

export const ScheduleCard: React.FC<ScheduleCardProps> = ({ items }) => {
  return (
    <div className="space-y-2.5 w-full pt-1" data-purpose="schedule-cards-list">
      {items.map((item) => {
        const isAvailable = item.slotsLeft > 0;
        return (
          <article
            key={item.id}
            className={`bg-white border rounded-2xl p-4 shadow-sm transition-all ${
              isAvailable
                ? 'border-gray-200 hover:border-red-300'
                : 'border-gray-200 bg-white/70 opacity-80'
            }`}
            data-purpose={isAvailable ? 'class-card-available' : 'class-card-full'}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="text-base font-black tracking-wide text-gray-900 leading-tight uppercase font-oswald">
                  {item.service}
                </h3>
                <p className="text-xs text-gray-500 font-medium mt-1 flex items-center gap-1.5">
                  <svg
                    className="w-3.5 h-3.5 text-gray-400 shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                    />
                  </svg>
                  <span className="truncate">{item.day} · {item.start} a {item.end}</span>
                </p>
              </div>

              {/* Badge de disponibilidad */}
              {isAvailable ? (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                  {item.slotsLeft} {item.slotsLeft === 1 ? 'cupo disponible' : 'cupos disponibles'}
                </span>
              ) : (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-500 border border-gray-200 shrink-0">
                  Completo
                </span>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
};
