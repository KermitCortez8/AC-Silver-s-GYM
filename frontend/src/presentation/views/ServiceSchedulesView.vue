<template>
  <div class="schedule-admin space-y-5">
    <header class="schedule-page-header">
      <div><p class="schedule-eyebrow">Planificación del gimnasio</p><h1>Horarios por servicio</h1><p class="schedule-description">Organiza tus clases, revisa los cupos y planifica cada semana.</p></div>
      <div class="schedule-page-actions">
        <button type="button" class="schedule-secondary" :disabled="isRefreshing" @click="refreshAll(true)"><RefreshCw :size="16" :class="{ 'animate-spin': isRefreshing }" />{{ isRefreshing ? 'Actualizando…' : 'Actualizar' }}</button>
        <button type="button" class="schedule-primary" @click="openNewSchedule"><Plus :size="17" />Nuevo horario</button>
      </div>
    </header>
    <section class="schedule-workspace" aria-label="Calendario de clases">
      <div class="schedule-toolbar">
        <div class="schedule-metrics"><span><strong>{{ activeSchedules }}</strong> horarios activos</span><span><strong>{{ usedSlots }} / {{ totalSlots }}</strong> cupos ocupados</span></div>
        <div class="schedule-search-actions"><label class="schedule-search"><Search :size="16" aria-hidden="true" /><SearchInput v-model="filters.search" placeholder="Servicio, rutina, día u hora…" aria-label="Buscar horario" /></label><button type="button" class="schedule-secondary" :aria-expanded="showFilters" aria-controls="schedule-filters" @click="showFilters = !showFilters"><SlidersHorizontal :size="15" />Filtros<span v-if="extraFilterCount" class="filter-count">{{ extraFilterCount }}</span></button></div>
      </div>
      <nav class="service-tabs" aria-label="Filtrar por servicio">
        <button v-for="service in serviceFilters" :key="service.value" type="button" :aria-pressed="filters.servicio === service.value" @click="filters.servicio = service.value">
          <span v-if="service.value !== 'todos'" class="service-tab-dot" :style="{ background: servicePalette[service.value].border }"></span>{{ service.value === 'todos' ? 'Todas las clases' : service.label }}<span class="service-tab-count">{{ service.value === 'todos' ? schedules.length : schedules.filter((item) => item.servicio === service.value).length }}</span>
        </button>
      </nav>
      <div v-if="showFilters" id="schedule-filters" class="schedule-extra-filters">
        <label>Día<select v-model="filters.dia"><option value="todos">Todos los días</option><option v-for="day in days" :key="day.value" :value="day.value">{{ day.label }}</option></select></label>
        <label>Disponibilidad<select v-model="filters.estado"><option v-for="status in statusFilters" :key="status.value" :value="status.value">{{ status.label }}</option></select></label>
        <label>Ordenar<select v-model="filters.sortBy"><option v-for="option in sortOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
        <button type="button" class="schedule-secondary" @click="resetFilters">Limpiar filtros</button>
      </div>
      <ExcelScheduleGrid title="Calendario de clases" subtitle="Elige tu semana y selecciona una clase para editarla."
        interactive modal-feedback @notification="showNotification" @select="editSchedule" @range-change="visibleRange = $event" :items="filteredSchedules" file-name="horarios-servicio.xlsx" />
    </section>

    <section class="schedule-list-section">
      <button type="button" class="schedule-list-toggle" :aria-expanded="showList" aria-controls="schedule-list" @click="showList = !showList"><span><List :size="17" /><strong>Gestionar lista de horarios</strong><span>{{ weeklySchedules.length }} sesiones esta semana</span></span><ChevronDown :size="18" :class="{ 'rotate-180': showList }" /></button>
      <div id="schedule-list" v-if="showList">
      <div v-if="weeklySchedules.length" class="mt-5 overflow-hidden rounded-2xl border schedule-border schedule-surface shadow-xl shadow-black/10">
        <div class="hidden overflow-x-auto lg:block">
          <table class="w-full min-w-[960px] text-left text-sm">
            <thead class="sticky top-0 z-10 schedule-inset text-[11px] uppercase tracking-[0.22em] schedule-muted">
              <tr>
                <th class="px-5 py-4">Servicio</th>
                <th class="px-5 py-4">Rutina</th>
                <th class="px-5 py-4">Fecha</th>
                <th class="px-5 py-4">Horario</th>
                <th class="px-5 py-4">Cupos</th>
                <th class="px-5 py-4">Estado</th>
                <th class="px-5 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y schedule-dividers">
              <tr
                v-for="schedule in weeklySchedules"
                :key="schedule.id_horario_servicio"
                class="group schedule-surface transition schedule-row"
                :style="serviceStyle(schedule.servicio)"
              >
                <td class="px-5 py-4">
                  <div class="flex items-center gap-3">
                    <span class="schedule-service-accent h-10 w-1.5 rounded-full"></span>
                    <div class="min-w-0">
                      <p class="truncate font-black schedule-text">{{ serviceLabel(schedule.servicio) }}</p>
                      <p class="mt-1 text-xs schedule-muted">Horario #{{ schedule.id_horario_servicio }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-4">
                  <p class="font-bold schedule-text">{{ routineName(schedule.id_rutina) }}</p>
                  <p class="mt-1 text-xs schedule-muted">{{ routineZones(schedule.id_rutina) }}</p>
                </td>
                <td class="px-5 py-4">
                  <p class="font-bold schedule-text">{{ dateLabel(schedule.fecha, { weekday: 'long' }) }}</p>
                  <span class="schedule-service-badge mt-1 inline-flex rounded-full px-2.5 py-1 text-xs font-black">
                    {{ schedule.codigo_dia }}
                  </span>
                </td>
                <td class="px-5 py-4">
                  <p class="font-black schedule-text">{{ schedule.hora_inicio }} - {{ schedule.hora_fin }}</p>
                  <p class="mt-1 text-xs schedule-muted">{{ durationLabel(schedule) }}</p>
                </td>
                <td class="px-5 py-4">
                  <div class="max-w-[220px]">
                    <div class="flex items-center justify-between gap-3 text-xs">
                      <span class="font-bold schedule-text">{{ schedule.cupos_usados || 0 }} / {{ schedule.cupos }}</span>
                      <span class="schedule-muted">{{ availableSlots(schedule) }} libres</span>
                    </div>
                    <div class="mt-2 h-2 overflow-hidden rounded-full schedule-track">
                      <div class="schedule-service-progress h-full rounded-full" :style="{ width: `${slotsPercent(schedule)}%` }"></div>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-4">
                  <span class="inline-flex items-center rounded-full px-3 py-1 text-xs font-black" :class="statusClass(schedule)">
                    {{ isScheduleActive(schedule) ? 'Activo' : 'Pausado' }}
                  </span>
                </td>
                <td class="px-5 py-4">
                  <div class="flex justify-end gap-2">
                    <button class="rounded-xl border schedule-border bg-white/5 px-3 py-2 text-sm font-bold schedule-text transition hover:bg-white/10" @click="editSchedule(schedule)">Editar</button>
                    <button class="rounded-xl border border-rose-400/30 bg-rose-400/5 px-3 py-2 text-sm font-bold schedule-danger transition hover:bg-rose-400/10" @click="removeSchedule(schedule)">Eliminar</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="grid gap-3 p-3 lg:hidden">
          <article
            v-for="schedule in weeklySchedules"
            :key="`mobile-${schedule.id_horario_servicio}`"
            class="rounded-2xl border schedule-border schedule-surface p-4"
            :style="serviceStyle(schedule.servicio)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex min-w-0 items-center gap-3">
                <span class="schedule-service-accent h-11 w-1.5 rounded-full"></span>
                <div class="min-w-0">
                  <p class="truncate text-base font-black schedule-text">{{ serviceLabel(schedule.servicio) }}</p>
                  <p class="mt-1 text-xs schedule-muted">
                    {{ dateLabel(schedule.fecha, { weekday: 'long' }) }}
                    <span class="schedule-service-badge ml-1 inline-flex rounded-full px-2 py-0.5 font-black">{{ schedule.codigo_dia }}</span>
                  </p>
                </div>
              </div>
              <span class="shrink-0 rounded-full px-3 py-1 text-xs font-black" :class="statusClass(schedule)">
                {{ isScheduleActive(schedule) ? 'Activo' : 'Pausado' }}
              </span>
            </div>

            <div class="mt-4 grid gap-3 rounded-2xl border schedule-border schedule-inset p-3 text-sm sm:grid-cols-2">
              <div>
                <p class="text-xs uppercase tracking-[0.18em] schedule-muted">Horario</p>
                <p class="mt-1 font-black schedule-text">{{ schedule.hora_inicio }} - {{ schedule.hora_fin }}</p>
                <p class="text-xs schedule-muted">{{ durationLabel(schedule) }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-[0.18em] schedule-muted">Rutina</p>
                <p class="mt-1 font-black schedule-text">{{ routineName(schedule.id_rutina) }}</p>
                <p class="text-xs schedule-muted">{{ routineZones(schedule.id_rutina) }}</p>
              </div>
              <div>
                <p class="text-xs uppercase tracking-[0.18em] schedule-muted">Cupos</p>
                <p class="mt-1 font-black schedule-text">{{ schedule.cupos_usados || 0 }} / {{ schedule.cupos }}</p>
                <p class="text-xs schedule-muted">{{ availableSlots(schedule) }} libres</p>
              </div>
            </div>

            <div class="mt-3 h-2 overflow-hidden rounded-full schedule-track">
              <div class="schedule-service-progress h-full rounded-full" :style="{ width: `${slotsPercent(schedule)}%` }"></div>
            </div>

            <div class="mt-4 grid grid-cols-2 gap-2">
              <button class="rounded-xl border schedule-border bg-white/5 px-3 py-2 text-sm font-bold schedule-text" @click="editSchedule(schedule)">Editar</button>
              <button class="rounded-xl border border-rose-400/30 bg-rose-400/5 px-3 py-2 text-sm font-bold schedule-danger" @click="removeSchedule(schedule)">Eliminar</button>
            </div>
          </article>
        </div>
      </div>

      <p v-if="!weeklySchedules.length" class="mt-6 rounded-2xl border schedule-border bg-white/5 px-4 py-3 text-sm schedule-muted">
        No hay sesiones en esta semana con los filtros actuales.
      </p>
      </div>
    </section>

    <ScheduleModal v-if="isEditorOpen" wide :title="form.id_horario_servicio ? 'Editar horario' : 'Nuevo horario'" :busy="isSaving" @close="closeEditor">
        <form class="schedule-editor" novalidate @submit.prevent="saveSchedule">
          <p class="editor-intro">Define el servicio, la rutina y los cupos de tu clase semanal.</p>
          <div class="mt-6 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2">
              <span class="text-sm schedule-soft">Servicio</span>
              <select autofocus v-model="form.servicio" class="field-input">
                <option value="fitness">Fitness</option>
                <option value="musculacion">Musculación</option>
                <option value="cardio">Cardio</option>
                <option value="baile">Baile</option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Rutina específica</span>
              <select v-model.number="form.id_rutina" class="field-input">
                <option :value="0">Selecciona una rutina</option>
                <option v-for="routine in routinesForSelectedService" :key="routine.id_rutina" :value="routine.id_rutina">
                  {{ routine.nombre_rutina }} - {{ routine.zonas_musculares || 'Sin zonas' }}
                </option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Día de cada semana</span>
              <select v-model="form.dia" class="field-input">
                <option v-for="day in days" :key="day.value" :value="day.value">{{ day.label }}</option>
              </select>
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Código del día</span>
              <input v-model="form.codigo_dia" class="field-input" placeholder="LUN" maxlength="10" />
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Hora de inicio</span>
              <input v-model="form.hora_inicio" type="time" class="field-input" />
            </label>

            <label class="space-y-2">
              <span class="text-sm schedule-soft">Hora de salida</span>
              <input v-model="form.hora_fin" type="time" class="field-input" />
            </label>
            <label class="space-y-2">
              <span class="text-sm schedule-soft">Cupos</span>
              <input v-model.number="form.cupos" type="number" min="1" class="field-input" />
            </label>
          </div>

          <p class="mt-3 rounded-2xl border border-orange-400/20 bg-orange-400/10 px-4 py-3 text-sm schedule-soft">
            Este horario se repite cada semana. Al editarlo, el cambio se aplica a las próximas clases y sus recordatorios. La duración debe ser de 1 o 2 horas.
          </p>

          <label class="mt-5 flex items-center gap-3 text-sm font-bold schedule-text">
            <input v-model="form.activo" type="checkbox" class="h-4 w-4 schedule-checkbox" />
            Disponible para matrícula
          </label>

          <footer class="editor-actions">
            <button type="button" class="schedule-secondary" :disabled="isSaving" @click="closeEditor">Cancelar</button>
            <button type="submit" class="schedule-primary" :disabled="isSaving">{{ isSaving ? 'Guardando…' : 'Guardar horario' }}</button>
          </footer>
        </form>
    </ScheduleModal>
    <ScheduleModal v-if="pendingDelete" title="¿Eliminar este horario?" :busy="isDeleting" @close="pendingDelete = null">
      <div class="notice-icon is-danger"><Trash2 :size="24" /></div>
      <p class="notice-message">Vas a eliminar el horario de <strong>{{ serviceLabel(pendingDelete.servicio) }}</strong> del {{ dayLabel(pendingDelete.dia) }}, de {{ pendingDelete.hora_inicio }} a {{ pendingDelete.hora_fin }}.</p>
      <p class="notice-detail">Esta acción no se puede deshacer.</p>
      <footer class="editor-actions">
        <button type="button" autofocus class="schedule-secondary" :disabled="isDeleting" @click="pendingDelete = null">Cancelar</button>
        <button type="button" class="schedule-primary" :disabled="isDeleting" @click="confirmRemoveSchedule">{{ isDeleting ? 'Eliminando…' : 'Eliminar horario' }}</button>
      </footer>
    </ScheduleModal>
    <ScheduleModal v-if="feedback" :title="feedbackTone === 'error' ? 'No se pudo completar la acción' : 'Todo listo'" @close="feedback = ''">
      <div class="notice-icon" :class="{ 'is-danger': feedbackTone === 'error' }"><CircleAlert v-if="feedbackTone === 'error'" :size="24" /><CircleCheck v-else :size="24" /></div>
      <p class="notice-message" role="status">{{ feedback }}</p>
      <footer class="editor-actions"><button type="button" autofocus class="schedule-primary" @click="feedback = ''">Entendido</button></footer>
    </ScheduleModal>
  </div>
</template>

<script setup>
import SearchInput from '../components/SearchInput.vue';
import {
  ChevronDown,
  CircleAlert,
  CircleCheck,
  List,
  Plus,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Trash2,
} from 'lucide-vue-next';
import ScheduleModal from '../components/ScheduleModal.vue';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { dateLabel } from '../utils/attendance.js';
import { useServiceSchedules } from '../composables/schedules/useServiceSchedules.js';

const {
  gymStore, schedules, routines, showFilters, showList,
  extraFilterCount, isSaving, isRefreshing, today, visibleRange,
  weeklySchedules, isEditorOpen, feedback, pendingDelete, isDeleting,
  feedbackTone, showNotification, filters, days, serviceFilters,
  statusFilters, sortOptions, defaultForm, form, normalizeService,
  serviceLabel, dayLabel, dayOrder, serviceOrder, routineById,
  routineName, routineZones, routinesForSelectedService, isScheduleActive, activeSchedules,
  totalSlots, usedSlots, timeToMinutes, availableSlots, durationLabel,
  slotsPercent, servicePalette, serviceStyle, statusClass, normalizeText,
  searchableScheduleText, matchesStatus, compareBase, filteredSchedules, hasValidShortDuration,
  resetForm, openNewSchedule, closeEditor, resetFilters, editSchedule,
  refreshAll, saveSchedule, removeSchedule, confirmRemoveSchedule,
} = useServiceSchedules();
</script>

<style scoped>
.schedule-admin { color: var(--app-text); min-width: 0; }
.schedule-page-header { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 8px 0 12px; }
.schedule-eyebrow { margin: 0 0 8px; color: var(--app-accent-text); font-size: 11px; letter-spacing: .18em; text-transform: uppercase; font-weight: 750; }
.schedule-page-header h1 { margin: 0; font-size: clamp(24px, 2.5vw, 32px); letter-spacing: -.035em; font-weight: 800; }
.schedule-description { margin: 8px 0 0; font-size: 13px; color: var(--app-text-muted); }
.schedule-page-actions, .schedule-search-actions, .schedule-toolbar { display: flex; align-items: center; gap: 10px; }
.schedule-primary, .schedule-secondary { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; padding: 10px 15px; border-radius: 9px; font: inherit; font-size: 12px; font-weight: 650; cursor: pointer; white-space: nowrap; }
.schedule-primary { background: var(--app-accent); color: white; box-shadow: 0 4px 10px #dc262620; }
.schedule-primary:hover { background: var(--app-accent-hover); }
.schedule-secondary { border: 1px solid var(--app-border); background: var(--app-surface); color: var(--app-text-soft); }
.schedule-secondary:hover, .schedule-secondary[aria-expanded="true"] { border-color: var(--app-border-strong); color: var(--app-accent-text); }
.schedule-workspace { min-width: 0; }
.schedule-toolbar { justify-content: space-between; padding-bottom: 18px; gap: 20px; }
.schedule-metrics { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; font-size: 12px; color: var(--app-text-muted); }
.schedule-metrics > span { padding: 12px 16px; border: 1px solid var(--app-border); border-radius: 12px; background: var(--app-surface); }
.schedule-checkbox { accent-color: var(--app-accent); }
.schedule-metrics strong { color: var(--app-text); font-size: 14px; font-weight: 750; padding-right: 5px; }
.schedule-search { display: flex; align-items: center; gap: 9px; padding: 10px 12px; border: 1px solid var(--app-border); border-radius: 9px; background: var(--app-input); color: var(--app-text-muted); }
.schedule-search input { width: 175px; min-width: 0; outline: none; background: transparent; color: var(--app-text); font-size: 12px; }
.service-tabs { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 18px; scrollbar-width: thin; }
.service-tabs button { display: inline-flex; flex-shrink: 0; align-items: center; gap: 7px; min-height: 44px; padding: 8px 12px; border: 1px solid var(--app-border); border-radius: 8px; background: var(--app-surface); color: var(--app-text-muted); font-size: 12px; font-weight: 650; cursor: pointer; }
.service-tabs button[aria-pressed="true"] { border-color: var(--app-border-strong); background: var(--app-accent-soft); color: var(--app-accent-text); }
.service-tab-dot { height: 6px; width: 6px; border-radius: 50%; }
.service-tab-count { opacity: .6; font-size: 11px; }
.schedule-extra-filters { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; padding: 16px; background: var(--app-surface); border: 1px solid var(--app-border); border-radius: 12px; }
.schedule-extra-filters label { display: flex; flex: 1; flex-direction: column; gap: 7px; min-width: 140px; font-size: 12px; color: var(--app-text-muted); }
.schedule-extra-filters select { border: 1px solid var(--app-border); border-radius: 8px; min-height: 44px; padding: 8px 10px; background: var(--app-input); color: var(--app-text); font-size: 12px; }
.filter-count { display: grid; place-items: center; width: 17px; height: 17px; border-radius: 50%; background: var(--app-accent); color: white; font-size: 11px; }
.schedule-list-section { border: 1px solid var(--app-border); border-radius: 12px; padding: 0 16px; background: var(--app-surface); }
.schedule-list-toggle { display: flex; align-items: center; justify-content: space-between; gap: 12px; width: 100%; padding: 17px 0; color: var(--app-text-soft); cursor: pointer; }
.schedule-list-toggle > span { display: flex; align-items: center; gap: 10px; }
.schedule-list-toggle strong { font-size: 12px; font-weight: 650; }
.schedule-list-toggle span span { color: var(--app-text-muted); font-size: 12px; }
#schedule-list { padding-bottom: 16px; }
button:focus-visible, .schedule-search:focus-within { outline: 2px solid var(--app-accent); outline-offset: 3px; }
@media (max-width: 1000px) { .schedule-page-header { align-items: flex-start; flex-direction: column; gap: 16px; } .schedule-toolbar { flex-wrap: wrap; } }
@media (max-width: 720px) {
  .schedule-page-header { padding-top: 0; }
  .schedule-page-actions { width: 100%; }
  .schedule-page-actions > button { flex: 1; }
  .schedule-search-actions { width: 100%; }
  .schedule-search { flex: 1; min-width: 0; }
  .schedule-search input { width: 100%; }
  .schedule-metrics { gap: 16px; }
  .schedule-list-toggle > span { flex-wrap: wrap; }
  .schedule-list-toggle span span { display: none; }
}

.field-input {
  width: 100%;
  border: 1px solid var(--app-border);
  border-radius: 1rem;
  background: var(--app-input);
  padding: 0.75rem 1rem;
  color: var(--app-text);
  outline: none;
}

.field-input::placeholder {
  color: #64748b;
}

.schedule-service-accent,
.schedule-service-progress {
  background: var(--schedule-service-border);
}

.schedule-service-progress {
  box-shadow: 0 0 12px color-mix(in srgb, var(--schedule-service-border) 45%, transparent);
}

.schedule-service-badge {
  border: 1px solid var(--schedule-service-border);
  background: var(--schedule-service-bg);
  color: #17324d;
}
.schedule-text { color: var(--app-text); }
.schedule-soft { color: var(--app-text-soft); }
.schedule-muted { color: var(--app-text-muted); }
.schedule-danger { color: var(--app-accent-text); }
.schedule-surface { background: var(--app-surface); }
.schedule-inset { background: var(--app-input); }
.schedule-border, .schedule-dividers > * { border-color: var(--app-border); }
.schedule-track { background: var(--app-border); }
#schedule-list button { min-height: 44px; }
.schedule-row:hover { background: var(--app-surface-soft); }
.schedule-status-active { background: #dcfce7; color: #166534; }
.schedule-status-paused { background: var(--app-surface-strong); color: var(--app-text-soft); border: 1px solid var(--app-border); }
.editor-intro, .notice-detail { color: var(--app-text-muted); font-size: 14px; line-height: 1.6; }
.schedule-editor label { display: block; }
.schedule-editor label:has(input[type="checkbox"]) { display: flex; }
.schedule-editor .field-input { min-height: 46px; border-radius: 10px; }
.field-input:focus-visible { outline: 2px solid var(--app-accent); outline-offset: 2px; }
.editor-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--app-border); }
.notice-message { font-size: 15px; line-height: 1.7; overflow-wrap: anywhere; color: var(--app-text); }
.notice-icon { display: grid; place-items: center; width: 48px; height: 48px; margin-bottom: 16px; border-radius: 14px; background: #dcfce7; color: #166534; }
.notice-icon.is-danger { background: var(--app-accent-soft); color: var(--app-accent-text); }
button:disabled { opacity: .55; cursor: wait; }
@media (max-width: 480px) { .editor-actions > button { flex: 1; white-space: normal; } }
</style>
