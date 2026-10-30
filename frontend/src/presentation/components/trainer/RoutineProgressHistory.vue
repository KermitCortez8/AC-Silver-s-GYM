<template>
  <div>
    <p
      class="text-[11px] uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5"
    >
      <i class="fa-solid fa-clock-rotate-left text-xs text-red-500"></i>
      Avance reciente registrado
    </p>
    <div
      v-if="recentProgress.length"
      class="mt-3 space-y-3 max-h-72 overflow-y-auto pr-1"
    >
      <div
        v-for="progress in recentProgress"
        :key="progress.id_progreso"
        class="rounded-xl bg-black/80 p-4 text-xs space-y-2 border border-white/10"
      >
        <div class="flex flex-wrap items-center justify-between gap-2">
          <span class="flex items-center gap-1.5 font-bold text-red-400">
            <i class="fa-regular fa-calendar text-[11px]"></i>
            {{ formatProgressDate(progress.fecha) }}
          </span>
          <span
            v-if="isCompleted(progress.estado)"
            class="rounded-full bg-emerald-500/20 px-3 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/30"
          >
            <i class="fa-solid fa-check mr-1 text-[9px]"></i>Rutina completada
          </span>
          <span
            v-else
            class="rounded-full bg-orange-500/20 px-3 py-0.5 text-[10px] font-bold text-orange-300 border border-orange-500/30"
          >
            Pendiente
          </span>
        </div>
        <p class="text-slate-300">
          <strong class="text-slate-400">Observación:</strong>
          {{ progress.observacion || 'Sin observación registrada' }}
        </p>
        <div
          v-if="(progress.ejercicios_detalle || []).length"
          class="mt-1 space-y-1 border-t border-white/5 pt-2"
        >
          <div
            v-for="(exDet, detIdx) in progress.ejercicios_detalle"
            :key="detIdx"
            class="text-[11px] text-slate-300 flex justify-between"
          >
            <span>
              <i
                v-if="exDet.completado"
                class="fa-solid fa-check text-emerald-400 mr-1 text-[10px]"
              ></i>
              {{ exDet.nombre_ejercicio }}
            </span>
            <span class="text-slate-400"
              >{{ exDet.series_completadas }} series
              <template v-if="exDet.peso_utilizado_kg"
                >· {{ exDet.peso_utilizado_kg }} kg</template
              ></span
            >
          </div>
        </div>
      </div>
    </div>
    <div
      v-else
      class="mt-3 rounded-xl border border-dashed border-white/10 p-4 text-center text-xs text-slate-500"
    >
      Aún no hay progreso registrado
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue';
import {
  sortedProgress,
  formatProgressDate,
  isCompleted,
} from '../../utils/trainerRoutines.js';
const props = defineProps({ progress: Array });
const recentProgress = computed(() => sortedProgress(props.progress));
</script>
