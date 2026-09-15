<template>
  <div class="week-picker">
    <div class="month-controls">
      <div class="month-navigation">
        <label class="month-label">
          <CalendarDays :size="19" aria-hidden="true" />
          <span>{{ monthLabel }}</span><ChevronDown :size="15" aria-hidden="true" />
          <input type="month" :value="month" aria-label="Mes del horario" @change="selectMonth($event.target.value)" />
        </label>
        <div class="month-arrows">
          <button type="button" aria-label="Mes anterior" @click="moveMonth(-1)"><ChevronLeft :size="18" /></button>
          <button type="button" aria-label="Mes siguiente" @click="moveMonth(1)"><ChevronRight :size="18" /></button>
        </div>
        <button type="button" class="today-button" @click="emit('update:modelValue', limaDate())">Hoy</button>
      </div>
      <span class="timezone"><Clock3 :size="13" aria-hidden="true" /> Hora de Perú</span>
    </div>
    <nav ref="weekNav" class="weeks" aria-label="Semanas del mes">
      <button v-for="(week, index) in weeks" :key="week.start" type="button"
        :aria-pressed="week.start === selectedStart" :class="{ selected: week.start === selectedStart }"
        @click="emit('update:modelValue', week.from)">
        <span class="week-number">Semana {{ index + 1 }}</span>
        <strong>{{ shortDate(week.from) }} – {{ shortDate(week.to) }}</strong>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { CalendarDays, ChevronDown, ChevronLeft, ChevronRight, Clock3 } from 'lucide-vue-next';
import { dateLabel, limaDate } from '../utils/attendance.js';
import { monthWeeks, weekStart } from '../utils/scheduleCalendar.js';
const props = defineProps({ modelValue: { type: String, required: true } });
const emit = defineEmits(['update:modelValue']);
const weekNav = ref(null);
const month = computed(() => props.modelValue.slice(0, 7));
const monthLabel = computed(() => dateLabel(`${month.value}-01`, { day: undefined, month: 'long' }));
const weeks = computed(() => monthWeeks(month.value));
const selectedStart = computed(() => weekStart(props.modelValue));
const shortDate = (date) => dateLabel(date, { year: undefined });
const selectMonth = (value) => { if (monthWeeks(value).length) emit('update:modelValue', `${value}-01`); };
const moveMonth = (delta) => {
  const date = new Date(`${month.value}-01T12:00:00Z`);
  date.setUTCMonth(date.getUTCMonth() + delta);
  selectMonth(date.toISOString().slice(0, 7));
};
const revealWeek = () => {
  const nav = weekNav.value;
  const selected = nav?.querySelector('[aria-pressed="true"]');
  if (selected) nav.scrollLeft = selected.offsetLeft - nav.offsetLeft - (nav.clientWidth - selected.clientWidth) / 2;
};
watch(() => props.modelValue, revealWeek, { flush: 'post' });
let resizeObserver;
onMounted(() => {
  revealWeek();
  resizeObserver = new ResizeObserver(revealWeek);
  resizeObserver.observe(weekNav.value);
});
onBeforeUnmount(() => resizeObserver?.disconnect());
</script>

<style scoped>
.week-picker { min-width: 0; color: var(--app-text); }
.month-controls, .month-navigation, .month-arrows, .month-label, .timezone { display: flex; align-items: center; }
.month-controls { justify-content: space-between; gap: 12px; padding: 20px 24px 16px; }
.month-navigation { gap: 12px; flex-wrap: wrap; }
button { min-height: 40px; border: 1px solid var(--app-border); border-radius: 8px; background: transparent; color: var(--app-text-soft); padding: 8px 12px; font: inherit; cursor: pointer; }
button:hover { background: var(--app-surface-soft); color: var(--app-text); }
.month-label { position: relative; gap: 9px; font-size: 18px; font-weight: 750; min-height: 40px; }
.month-label > span::first-letter { text-transform: uppercase; }
.month-label > svg:first-child { color: var(--app-accent-text); }
.month-label input { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
.month-arrows { gap: 4px; }
.month-arrows button { display: grid; place-items: center; width: 36px; min-height: 36px; padding: 0; }
.today-button { font-size: 12px; font-weight: 700; min-height: 36px; }
.timezone { gap: 6px; white-space: nowrap; font-size: 11px; color: var(--app-text-muted); }
.weeks { display: flex; position: relative; gap: 6px; padding: 0 24px 18px; overflow-x: auto; scrollbar-width: thin; }
.weeks button { flex: 1 0 112px; display: flex; flex-direction: column; gap: 5px; padding: 11px 14px; text-align: left; border-color: transparent; border-bottom: 2px solid var(--app-border); border-radius: 8px 8px 0 0; white-space: nowrap; }
.week-number { font-size: 11px; color: var(--app-text-muted); }
.weeks strong { font-size: 12px; font-weight: 650; }
.weeks .selected { border-bottom-color: var(--app-accent); background: var(--app-accent-soft); color: var(--app-text); }
.weeks .selected .week-number { color: var(--app-accent-text); font-weight: 700; }
button:focus-visible, .month-label:focus-within { outline: 2px solid var(--app-accent); outline-offset: 3px; }
@media (max-width: 720px) {
  .month-controls { padding: 16px 16px 12px; }
  .month-navigation { gap: 7px; }
  .month-label { font-size: 15px; gap: 6px; }
  .month-label > svg:first-child { display: none; }
  .timezone { display: none; }
  .weeks { padding: 0 16px 14px; }
  .weeks button { flex: 1 0 112px; }
}
</style>
