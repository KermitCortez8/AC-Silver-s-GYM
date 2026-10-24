<template>
  <Teleport to="body">
    <div
      v-if="open && item"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-3 sm:p-6 backdrop-blur-md overflow-y-auto"
    >
      <div
        class="relative w-full max-w-6xl rounded-3xl border border-white/15 bg-slate-950 p-5 sm:p-6 shadow-2xl space-y-3 text-white my-auto max-h-[95vh] overflow-y-auto"
      >
        <!-- Header del Modal -->
        <div
          class="flex items-center justify-between border-b border-white/10 pb-3"
        >
          <div>
            <div class="flex flex-wrap items-center gap-2.5">
              <h3
                class="text-2xl font-black text-white tracking-tight flex items-center gap-2"
              >
                <i class="fa-solid fa-square-check text-red-500"></i>
                {{ item.rutina_nombre }}
              </h3>
              <span
                class="rounded-full bg-red-600/20 px-3 py-0.5 text-xs font-extrabold text-red-400 border border-red-600/30"
              >
                {{ serviceLabel(item.servicio) }}
              </span>
              <span
                class="rounded-full bg-emerald-500/20 px-3 py-0.5 text-xs font-black text-emerald-300 border border-emerald-500/30"
              >
                EN PROGRESO
              </span>
            </div>
            <p class="text-xs text-slate-400 mt-0.5">
              Zonas musculares:
              <span class="text-slate-200 font-semibold">{{
                item.zonas_musculares || 'General'
              }}</span>
            </p>
          </div>
          <button
            class="rounded-full bg-white/10 p-2 text-slate-400 hover:bg-white/20 hover:text-white transition"
            @click="open = false"
          >
            <i class="fa-solid fa-xmark text-lg"></i>
          </button>
        </div>

        <!-- WIDGET CRONÓMETRO DE DESCANSO EN TIEMPO REAL (Fondo Negro Oscuro + Rojo, Sin Gradientes) -->
        <RoutineRestTimer :timer="timer" />

        <!-- LISTA DE EJERCICIOS (ANCHO MAX 6XL COMPACTO HORIZONTAL SIN OVERFLOW) -->
        <div class="space-y-3">
          <RoutineExerciseCard
            v-for="(exercise, index) in exercises"
            :key="exercise.id_ejercicio"
            v-model="exercises[index]"
            @rest="timer.start"
          />
        </div>

        <!-- Observaciones y Botones de Acción (SIN GRADIENTES, ROJO Y NEGRO) -->
        <div class="space-y-2 pt-2 border-t border-white/10">
          <label class="block space-y-1">
            <span
              class="text-xs font-bold text-slate-300 flex items-center gap-1.5"
            >
              <i class="fa-solid fa-clipboard-list text-red-500/80"></i>
              <span>Observaciones Generales de la Sesión</span>
            </span>
            <input
              v-model="observation"
              class="field-input text-xs py-2 bg-black border-white/10"
              placeholder="Ej. El cliente logró subir peso manteniendo buena técnica."
            />
          </label>
          <div class="flex items-center justify-end gap-3 pt-1">
            <button
              class="flex items-center gap-1.5 rounded-2xl border border-white/10 bg-slate-900 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800 transition"
              @click="open = false"
            >
              <i class="fa-solid fa-xmark text-xs"></i>
              <span>Cerrar</span>
            </button>
            <button
              class="flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-2.5 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/30 disabled:opacity-50"
              :disabled="saving"
              @click="$emit('save')"
            >
              <i class="fa-solid fa-floppy-disk"></i>
              <span>{{
                saving ? 'Guardando…' : 'Guardar Progreso de Sesión'
              }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
<script setup>
import { serviceLabel } from '../../utils/trainerRoutines.js';
import RoutineRestTimer from './RoutineRestTimer.vue';
import RoutineExerciseCard from './RoutineExerciseCard.vue';
const open = defineModel('open', { type: Boolean, default: false });
const observation = defineModel('observation', { type: String, default: '' });
const exercises = defineModel('exercises', { type: Array, required: true });
defineProps({ item: Object, timer: Object, saving: Boolean });
defineEmits(['save']);
</script>

<style scoped src="../../styles/trainer-monitor.css"></style>
