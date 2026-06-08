<template>
  <section class="excel-shell">
    <div class="excel-header">
      <div>
        <h2>{{ title }}</h2>
        <p>{{ subtitle }}</p>
      </div>
      <button type="button" class="excel-export" @click="exportExcel">
        Exportar Excel
      </button>
    </div>

    <div class="excel-calendar">
      <FullCalendar :options="calendarOptions" />
      <p v-if="!items.length" class="excel-empty">{{ emptyMessage }}</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import * as XLSX from 'xlsx';

const props = defineProps({
  title: {
    type: String,
    default: 'Horario',
  },
  subtitle: {
    type: String,
    default: 'Para ver el detalle, presione sobre el bloque del horario',
  },
  items: {
    type: Array,
    default: () => [],
  },
  fileName: {
    type: String,
    default: 'horario.xlsx',
  },
  emptyMessage: {
    type: String,
    default: 'No hay horarios para mostrar.',
  },
});

const baseWeek = {
  lunes: '2026-01-05',
  martes: '2026-01-06',
  miercoles: '2026-01-07',
  jueves: '2026-01-08',
  viernes: '2026-01-09',
  sabado: '2026-01-10',
  domingo: '2026-01-11',
};

const dayLabels = {
  lunes: 'Lun',
  martes: 'Mar',
  miercoles: 'Mie',
  jueves: 'Jue',
  viernes: 'Vie',
  sabado: 'Sab.',
  domingo: 'Dom',
};

const dayByIndex = ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'];

const normalizeDay = (day) =>
  String(day || '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

const normalizeTime = (value) => {
  const [hour = '00', minute = '00'] = String(value || '').split(':');
  return `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}:00`;
};

const displayTime = (value) => normalizeTime(value).slice(0, 5);

const timeToMinutes = (value) => {
  const [hour = 0, minute = 0] = normalizeTime(value).split(':').map(Number);
  return hour * 60 + minute;
};

const minutesToSlotTime = (value) => {
  if (value >= 24 * 60) return '24:00:00';
  const safeValue = Math.max(0, Math.min(24 * 60 - 1, value));
  const hour = Math.floor(safeValue / 60);
  const minute = safeValue % 60;
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00`;
};

const serviceLabel = (service) =>
  ({
    fitness: 'Fitness',
    musculacion: 'Musculacion',
    cardio: 'Cardio',
    baile: 'Baile',
  })[service] || service || 'Servicio';

const eventColor = (service) =>
  ({
    fitness: '#d9f99d',
    musculacion: '#bfdbfe',
    cardio: '#fde68a',
    baile: '#fecdd3',
  })[service] || '#e2e8f0';

const eventBorderColor = (service) =>
  ({
    fitness: '#84cc16',
    musculacion: '#38bdf8',
    cardio: '#f59e0b',
    baile: '#fb7185',
  })[service] || '#94a3b8';

const visibleTimeRange = computed(() => {
  const validItems = props.items.filter((item) => item.hora_inicio && item.hora_fin);
  if (!validItems.length) {
    return { min: '06:00:00', max: '22:00:00' };
  }

  const starts = validItems.map((item) => timeToMinutes(item.hora_inicio));
  const ends = validItems.map((item) => timeToMinutes(item.hora_fin));
  const min = Math.max(0, Math.floor((Math.min(...starts) - 60) / 30) * 30);
  const maxBase = Math.min(24 * 60, Math.ceil((Math.max(...ends) + 60) / 30) * 30);
  const max = Math.max(maxBase, Math.min(24 * 60, min + 240));

  return {
    min: minutesToSlotTime(min),
    max: minutesToSlotTime(max),
  };
});

const escapeHtml = (value) =>
  String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

const eventMeta = (item) => {
  if (item.checkLabel) return item.checkLabel;
  if (item.cliente_nombre) return item.cliente_nombre;
  if (item.cupos !== undefined) return `${item.cupos_usados || 0}/${item.cupos} cupos`;
  return `${displayTime(item.hora_inicio)}-${displayTime(item.hora_fin)}`;
};

const calendarEvents = computed(() =>
  props.items
    .map((item) => {
      const day = normalizeDay(item.dia);
      const date = baseWeek[day];
      if (!date || !item.hora_inicio || !item.hora_fin) return null;
      const startTime = normalizeTime(item.hora_inicio);
      const endTime = normalizeTime(item.hora_fin);
      const service = serviceLabel(item.servicio);

      const titleLines = [
        item.codigo_dia || service,
        service,
        eventMeta(item),
      ].filter(Boolean);

      return {
        id: String(item.id_horario_servicio || item.id_matricula || `${item.servicio}-${day}-${item.hora_inicio}`),
        title: titleLines.join('\n'),
        start: `${date}T${startTime}`,
        end: `${date}T${endTime}`,
        backgroundColor: item.color || eventColor(item.servicio),
        borderColor: eventBorderColor(item.servicio),
        textColor: '#17324d',
        extendedProps: item,
      };
    })
    .filter(Boolean),
);

const calendarOptions = computed(() => ({
  plugins: [timeGridPlugin, interactionPlugin],
  initialView: 'timeGridWeek',
  initialDate: '2026-01-05',
  headerToolbar: false,
  allDaySlot: false,
  firstDay: 1,
  slotMinTime: visibleTimeRange.value.min,
  slotMaxTime: visibleTimeRange.value.max,
  slotDuration: '00:30:00',
  slotLabelInterval: '01:00:00',
  scrollTime: visibleTimeRange.value.min,
  height: 540,
  expandRows: false,
  nowIndicator: false,
  slotEventOverlap: false,
  eventMaxStack: 3,
  eventOrder: 'start,servicio,title',
  events: calendarEvents.value,
  dayHeaderContent: (arg) => {
    const dayKey = dayByIndex[arg.date.getDay()];
    return dayLabels[dayKey] || '';
  },
  slotLabelFormat: {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  },
  eventContent: (arg) => {
    const item = arg.event.extendedProps || {};
    const code = item.codigo_dia || serviceLabel(item.servicio);
    const service = serviceLabel(item.servicio);
    const time = `${displayTime(item.hora_inicio)}-${displayTime(item.hora_fin)}`;
    const meta = eventMeta(item);

    return {
      html: `
        <div class="excel-event-card">
          <span class="excel-event-code">${escapeHtml(code)}</span>
          <span class="excel-event-service">${escapeHtml(service)}</span>
          <span class="excel-event-meta">${escapeHtml(meta || time)}</span>
        </div>
      `,
    };
  },
  eventDidMount: ({ el, event }) => {
    const item = event.extendedProps || {};
    el.title = [
      serviceLabel(item.servicio),
      item.dia,
      `${displayTime(item.hora_inicio)} - ${displayTime(item.hora_fin)}`,
      item.cupos !== undefined ? `Cupos: ${item.cupos_usados || 0}/${item.cupos}` : '',
      item.checkLabel || item.cliente_nombre || '',
    ].filter(Boolean).join(' | ');
  },
}));

const exportExcel = () => {
  const rows = props.items.map((item) => ({
    Servicio: serviceLabel(item.servicio),
    Dia: item.dia || '',
    Codigo: item.codigo_dia || '',
    Inicio: item.hora_inicio || '',
    Salida: item.hora_fin || '',
    Cupos: item.cupos ?? '',
    Matriculados: item.cupos_usados ?? '',
    Cliente: item.cliente_nombre || '',
    Entrada: item.entryTime || '',
    SalidaRegistrada: item.exitTime || '',
    Check: item.checkLabel || '',
  }));

  const worksheet = XLSX.utils.json_to_sheet(rows);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Horario');
  XLSX.writeFile(workbook, props.fileName.endsWith('.xlsx') ? props.fileName : `${props.fileName}.xlsx`);
};
</script>

<style scoped>
.excel-shell {
  width: 100%;
  border: 1px solid #d8dde4;
  border-radius: 8px;
  background: #f8f8f8;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.16);
  color: #334155;
  overflow: hidden;
}

.excel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 18px 12px;
  text-align: center;
}

.excel-header > div {
  flex: 1;
}

.excel-header h2 {
  margin: 0;
  color: #3f3f46;
  font-size: 22px;
  font-weight: 500;
  line-height: 1.2;
}

.excel-header p {
  margin: 4px auto 0;
  max-width: 980px;
  color: #52525b;
  font-size: 17px;
  line-height: 1.45;
}

.excel-export {
  flex: 0 0 auto;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #fff;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  padding: 9px 12px;
}

.excel-calendar {
  position: relative;
  overflow-x: auto;
  padding: 0 6px 6px;
}

:deep(.fc) {
  min-width: 960px;
  font-family: Arial, sans-serif;
  font-size: 13px;
}

:deep(.fc-theme-standard td),
:deep(.fc-theme-standard th) {
  border-color: #d9d9d9;
}

:deep(.fc-scrollgrid) {
  border-color: #d9d9d9;
  background: #fff;
}

:deep(.fc-col-header-cell) {
  background: #fbfbfb;
  color: #405064;
  font-weight: 700;
}

:deep(.fc-timegrid-slot) {
  height: 18px;
}

:deep(.fc-timegrid-slot-minor) {
  border-top-style: dotted;
}

:deep(.fc-timegrid-slot-label) {
  color: #405064;
  font-size: 14px;
}

:deep(.fc-timegrid-event) {
  margin: 0 1px;
  border-radius: 3px;
  box-shadow: none;
  overflow: hidden;
}

:deep(.fc-event-main) {
  padding: 1px 2px;
}

:deep(.excel-event-card) {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1px;
  color: #17324d;
  line-height: 1.1;
}

:deep(.excel-event-code),
:deep(.excel-event-service),
:deep(.excel-event-meta) {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
  word-break: break-word;
}

:deep(.excel-event-code) {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}

:deep(.excel-event-service) {
  font-size: 10px;
  font-weight: 700;
}

:deep(.excel-event-meta) {
  color: #334155;
  font-size: 9px;
  font-weight: 600;
}

.excel-empty {
  position: absolute;
  left: 72px;
  top: 82px;
  margin: 0;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.88);
  padding: 10px 12px;
  color: #64748b;
  font-size: 13px;
  pointer-events: none;
}

@media (max-width: 720px) {
  .excel-header {
    flex-direction: column;
    text-align: left;
  }

  .excel-header p {
    font-size: 15px;
  }

  .excel-export {
    width: 100%;
  }
}
</style>
