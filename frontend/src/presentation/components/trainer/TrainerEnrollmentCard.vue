<template>
  <article
    class="rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-xl space-y-4"
  >
    <!-- Cabecera de la rutina y Botones de Acción -->
    <div
      class="flex flex-wrap items-start justify-between gap-4 border-b border-white/10 pb-4"
    >
      <div>
        <div class="flex items-center gap-3">
          <h3 class="text-xl font-black text-white flex items-center gap-2">
            <i class="fa-solid fa-dumbbell text-red-500 text-lg"></i>
            {{
              item.rutina_nombre || 'Servicio de ' + serviceLabel(item.servicio)
            }}
          </h3>
          <span
            class="rounded-full bg-red-600/20 px-3 py-1 text-xs font-bold text-red-300 border border-red-600/30"
          >
            {{ serviceLabel(item.servicio) }}
          </span>
        </div>
        <div class="mt-2 grid gap-1 text-xs text-slate-300 sm:grid-cols-2">
          <p>
            <strong class="text-slate-400">Día:</strong>
            {{ dayLabel(item.dia) }}
          </p>
          <p>
            <strong class="text-slate-400">Hora:</strong>
            {{ item.hora_inicio }} - {{ item.hora_fin }}
          </p>
          <p class="sm:col-span-2">
            <strong class="text-slate-400">Zonas musculares:</strong>
            {{ item.zonas_musculares || 'General / Fuerza' }}
          </p>
          <p class="sm:col-span-2">
            <strong class="text-slate-400">Estado:</strong>
            <span
              class="font-bold ml-1"
              :class="item.id_rutina ? 'text-emerald-400' : 'text-amber-400'"
            >
              {{ item.id_rutina ? 'En progreso' : 'Pendiente asignación' }}
            </span>
          </p>
        </div>
      </div>

      <!-- Botones Editar / Eliminar -->
      <div class="flex items-center gap-2">
        <button
          v-if="item.id_rutina"
          class="rounded-xl border border-white/10 bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 transition flex items-center gap-1.5"
          @click="$emit('exercises')"
        >
          <i class="fa-solid fa-pen-to-square text-xs text-red-400"></i>
          <span>Editar / Ejercicios</span>
        </button>
        <button
          v-if="item.id_rutina"
          class="rounded-xl border border-red-500/30 bg-red-600/20 px-4 py-2 text-xs font-bold text-red-300 hover:bg-red-600 hover:text-white transition flex items-center gap-1.5"
          @click="$emit('unassign')"
        >
          <i class="fa-solid fa-trash text-xs"></i>
          <span>Eliminar</span>
        </button>
      </div>
    </div>

    <!-- Indicadores conservados de la rama de asignación. -->
    <div class="flex flex-wrap gap-2">
      <span
        class="rounded-full px-3 py-1 text-xs font-bold"
        :class="
          isEnrollmentActive(item)
            ? 'bg-emerald-400/15 text-emerald-200'
            : 'bg-amber-400/15 text-amber-200'
        "
      >
        {{
          isEnrollmentActive(item) ? 'Matrícula activa' : 'Matrícula no activa'
        }}
      </span>
      <span
        class="rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-slate-200"
      >
        {{
          item.rutina_origen === 'cliente'
            ? 'Rutina del cliente'
            : 'Rutina del servicio'
        }}
      </span>
    </div>

    <!-- Asignación directa por matrícula, además del modal personalizado. -->
    <div class="grid gap-3 sm:grid-cols-[1fr_auto]">
      <select
        class="field-input text-sm"
        :value="selectedRoutine"
        :disabled="!canAssign || assigningId === item.id_matricula"
        :aria-label="`Rutina para ${serviceLabel(item.servicio)}`"
        @change="$emit('select', Number($event.target.value))"
      >
        <option :value="0" disabled>
          Selecciona una rutina de {{ serviceLabel(item.servicio) }}
        </option>
        <option
          v-for="routine in routines"
          :key="routine.id_rutina"
          :value="routine.id_rutina"
        >
          {{ routine.nombre_rutina }}
        </option>
      </select>
      <button
        type="button"
        class="rounded-2xl bg-red-600 px-4 py-3 text-xs font-black text-white disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
        :disabled="!canAssign || !hasChange || Boolean(assigningId)"
        @click="$emit('assign')"
      >
        {{ assigningId === item.id_matricula ? 'Asignando…' : 'Asignar' }}
      </button>
    </div>
    <button
      type="button"
      class="w-full rounded-2xl bg-emerald-500 px-4 py-3 text-xs font-black text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
      :disabled="
        !item.id_rutina ||
        !isEnrollmentActive(item) ||
        markingId === item.id_matricula
      "
      @click="$emit('done')"
    >
      {{ markingId === item.id_matricula ? 'Registrando…' : 'Check realizado' }}
    </button>
    <p
      v-if="isEnrollmentActive(item) && !routines.length"
      class="rounded-xl border border-amber-400/20 bg-amber-400/10 px-3 py-2 text-sm text-amber-100"
      role="status"
    >
      No hay rutinas compatibles con el servicio
      {{ serviceLabel(item.servicio) }}. Crea una en la sección Rutinas para
      poder asignarla.
    </p>

    <!-- Historial de avance reciente -->
    <RoutineProgressHistory :progress="item.progreso" />
  </article>
</template>
<script setup>
import {
  dayLabel,
  serviceLabel,
  isEnrollmentActive,
} from '../../utils/trainerRoutines.js';
import RoutineProgressHistory from './RoutineProgressHistory.vue';
defineProps({
  item: { type: Object, required: true },
  routines: { type: Array, default: () => [] },
  selectedRoutine: Number,
  canAssign: Boolean,
  hasChange: Boolean,
  assigningId: Number,
  markingId: Number,
});
defineEmits(['select', 'exercises', 'unassign', 'assign', 'done']);
</script>

<style scoped src="../../styles/trainer-monitor.css"></style>
