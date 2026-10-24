<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 backdrop-blur-md"
    >
      <div
        class="w-full max-w-xl rounded-3xl border border-white/15 bg-slate-950 p-6 shadow-2xl space-y-5 text-white"
      >
        <div
          class="flex items-center justify-between border-b border-white/10 pb-3"
        >
          <h3 class="text-xl font-black text-white flex items-center gap-2">
            <i class="fa-solid fa-plus text-red-500 text-sm"></i>
            <span>Asignar rutina personalizada</span>
          </h3>
          <button
            class="rounded-full bg-white/10 p-2 text-slate-400 hover:text-white transition"
            @click="open = false"
          >
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <div class="space-y-4">
          <label class="block space-y-2">
            <span
              class="text-xs uppercase tracking-wider font-bold text-slate-300 flex items-center gap-1.5"
            >
              <i class="fa-solid fa-dumbbell text-red-500/80"></i>
              <span>Seleccionar servicio matriculado del cliente</span>
            </span>
            <select
              v-model="enrollmentId"
              class="field-input text-sm cursor-pointer font-medium"
              @change="routineId = 0"
            >
              <option
                v-for="mat in enrollments.filter(isEnrollmentActive)"
                :key="mat.id_matricula"
                :value="mat.id_matricula"
              >
                {{ serviceLabel(mat.servicio) }} ({{ dayLabel(mat.dia) }}
                {{ mat.hora_inicio }} - {{ mat.hora_fin }})
              </option>
            </select>
          </label>

          <label class="block space-y-2">
            <span
              class="text-xs uppercase tracking-wider font-bold text-slate-300 flex items-center gap-1.5"
            >
              <i class="fa-solid fa-list-check text-red-500/80"></i>
              <span>Rutina del catálogo a vincular</span>
            </span>
            <select
              v-model="routineId"
              class="field-input text-sm cursor-pointer font-medium"
            >
              <option :value="0" disabled>
                Selecciona una rutina del catálogo
              </option>
              <option
                v-for="routine in routines"
                :key="routine.id_rutina"
                :value="routine.id_rutina"
              >
                {{ routine.nombre_rutina }} ({{
                  (routine.ejercicios || []).length
                }}
                ejercicios)
              </option>
            </select>
            <p v-if="!routines.length" class="text-xs text-amber-300">
              No hay rutinas compatibles con el servicio seleccionado.
            </p>
          </label>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <button
            class="rounded-xl bg-slate-900 border border-white/10 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800 transition"
            @click="open = false"
          >
            Cancelar
          </button>
          <button
            class="flex items-center gap-2 rounded-xl bg-red-600 px-6 py-2.5 text-xs font-black text-white hover:bg-red-500 transition shadow-lg shadow-red-600/30 disabled:bg-slate-800 disabled:text-slate-500 disabled:border disabled:border-white/10 disabled:shadow-none disabled:cursor-not-allowed"
            :disabled="!canSubmit || Boolean(busy)"
            @click="$emit('submit')"
          >
            <i class="fa-solid fa-check"></i>
            <span>{{ busy ? 'Guardando…' : 'Guardar rutina' }}</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
<script setup>
import {
  dayLabel,
  serviceLabel,
  isEnrollmentActive,
} from '../../utils/trainerRoutines.js';
const open = defineModel('open', { type: Boolean, default: false });
const enrollmentId = defineModel('enrollmentId');
const routineId = defineModel('routineId', { type: Number, default: 0 });
defineProps({
  enrollments: { type: Array, default: () => [] },
  routines: Array,
  canSubmit: Boolean,
  busy: Boolean,
});
defineEmits(['submit']);
</script>

<style scoped src="../../styles/trainer-monitor.css"></style>
