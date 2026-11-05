<template>
  <div
    class="routine-ex-card rounded-2xl border transition p-3.5 space-y-2.5"
    :class="
      ex.completado
        ? 'border-emerald-500/40 bg-emerald-950/20'
        : 'border-white/10 bg-slate-900/60'
    "
  >
    <!-- Fila Superior: Botón de estado del ejercicio y Botón de descanso -->
    <div
      class="flex items-center justify-between gap-2 border-b border-white/5 pb-2"
    >
      <div class="flex items-center gap-3">
        <!-- Botón interactivo de check/completado (Sin checkbox plano) -->
        <button
          type="button"
          class="flex h-7 w-7 items-center justify-center rounded-lg transition active:scale-95"
          :class="
            ex.completado
              ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/30'
              : 'bg-slate-800 text-slate-400 border border-white/10 hover:border-emerald-500/50 hover:text-emerald-400'
          "
          @click="
            ex.completado = !ex.completado;
            onToggleExerciseCompleted(ex);
          "
          :title="
            ex.completado
              ? 'Ejercicio completado'
              : 'Marcar ejercicio como completado'
          "
        >
          <i
            :class="
              ex.completado
                ? 'fa-solid fa-check text-sm font-black'
                : 'fa-regular fa-circle text-xs'
            "
          ></i>
        </button>

        <div class="flex items-center gap-2">
          <i class="fa-solid fa-dumbbell text-red-500 text-sm"></i>
          <span
            class="font-extrabold text-white text-base tracking-tight"
            :class="{ 'text-emerald-400': ex.completado }"
          >
            {{ ex.nombre_ejercicio }}
          </span>
          <span
            v-if="ex.completado"
            class="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[10px] font-black text-emerald-400 border border-emerald-500/30"
          >
            <i class="fa-solid fa-check text-[9px] mr-1"></i> Completado
          </span>
        </div>
      </div>

      <button
        type="button"
        class="rest-badge-btn flex items-center gap-1.5 rounded-xl bg-red-600/10 border border-red-600/30 px-3 py-1 text-xs font-bold text-red-400 hover:bg-red-600 hover:text-white transition"
        @click="$emit('rest', ex.descanso_segundos || 60)"
      >
        <i class="fa-solid fa-stopwatch text-xs"></i>
        <span>{{ ex.descanso_segundos || 60 }}s descanso</span>
      </button>
    </div>

    <p
      v-if="ex.notas"
      class="text-xs text-slate-400 italic flex items-center gap-1.5"
    >
      <i class="fa-solid fa-circle-info text-red-500/70 text-[11px]"></i>
      <span>Notas: {{ ex.notas }}</span>
    </p>

    <!-- CONTROLES HORIZONTALES COMPACTOS (3 COLUMNAS SIN ROLLO ROJO Y NEGRO) -->
    <div class="grid gap-3 md:grid-cols-3">
      <!-- Control 1: Series Completadas -->
      <div
        class="routine-subbox space-y-1 bg-slate-950/80 p-2.5 rounded-xl border border-white/5"
      >
        <span
          class="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1"
        >
          <i class="fa-solid fa-layer-group text-red-500/80"></i>
          <span>Series Completadas</span>
        </span>
        <div class="flex items-center justify-between gap-2">
          <button
            type="button"
            class="flex h-7 w-8 items-center justify-center rounded-lg bg-slate-900 text-white font-black hover:bg-slate-800 active:scale-95 transition border border-white/10"
            @click="adjustSeries(ex, -1)"
          >
            <i class="fa-solid fa-minus text-xs"></i>
          </button>
          <span class="text-sm font-black text-red-400">
            {{ ex.series_completadas || 0 }}
            <span class="text-xs text-slate-500 font-bold"
              >/ {{ ex.series_meta }}</span
            >
          </span>
          <button
            type="button"
            class="flex h-7 w-8 items-center justify-center rounded-lg bg-red-600 text-white font-black hover:bg-red-500 active:scale-95 transition"
            @click="adjustSeries(ex, 1)"
          >
            <i class="fa-solid fa-plus text-xs"></i>
          </button>
        </div>
        <!-- Pills rápidos de series -->
        <div class="flex flex-wrap gap-1 pt-1">
          <button
            v-for="s in Number(ex.series_meta || 3)"
            :key="s"
            type="button"
            class="rounded px-2.5 py-0.5 text-[10px] font-bold transition"
            :class="
              ex.series_completadas === s
                ? 'bg-red-600 text-white font-black'
                : 'bg-slate-900 text-slate-400 border border-white/5 hover:bg-slate-800'
            "
            @click="
              ex.series_completadas = s;
              onSeriesChanged(ex);
            "
          >
            {{ s }}
          </button>
        </div>
      </div>

      <!-- Control 2: Peso Real Utilizado (kg) -->
      <div
        class="routine-subbox space-y-1 bg-slate-950/80 p-2.5 rounded-xl border border-white/5"
      >
        <div class="flex items-center justify-between">
          <span
            class="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1"
          >
            <i class="fa-solid fa-weight-hanging text-red-500/80"></i>
            <span>Peso Real (kg)</span>
          </span>
          <span class="text-sm font-black text-red-400"
            >{{ ex.peso_utilizado_kg || 0 }} kg</span
          >
        </div>
        <div class="flex flex-wrap gap-1 pt-1">
          <button
            type="button"
            class="flex-1 rounded bg-slate-900 py-1 text-[10px] font-bold text-slate-300 border border-white/10 hover:bg-slate-800 transition"
            @click="adjustWeight(ex, -2.5)"
          >
            -2.5
          </button>
          <button
            v-if="ex.peso_sugerido_kg"
            type="button"
            class="sug-weight-btn flex-1 rounded bg-red-950/60 py-1 text-[10px] font-bold text-red-400 border border-red-600/40 hover:bg-red-600 hover:text-white transition flex items-center justify-center gap-1"
            @click="setWeightToSuggested(ex)"
          >
            <i class="fa-solid fa-wand-magic-sparkles text-[9px]"></i>
            <span>Sug: {{ ex.peso_sugerido_kg }}</span>
          </button>
          <button
            type="button"
            class="flex-1 rounded bg-slate-900 py-1 text-[10px] font-bold text-slate-300 border border-white/10 hover:bg-slate-800 transition"
            @click="adjustWeight(ex, 2.5)"
          >
            +2.5
          </button>
          <button
            type="button"
            class="flex-1 rounded bg-red-600 py-1 text-[10px] font-bold text-white hover:bg-red-500 transition"
            @click="adjustWeight(ex, 5)"
          >
            +5
          </button>
        </div>
      </div>

      <!-- Control 3: Repeticiones Logradas -->
      <div
        class="routine-subbox space-y-1 bg-slate-950/80 p-2.5 rounded-xl border border-white/5"
      >
        <span
          class="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1"
        >
          <i class="fa-solid fa-bullseye text-red-500/80"></i>
          <span>Reps Logradas</span>
        </span>
        <input
          v-model="ex.repeticiones_logradas"
          class="field-input text-xs py-1 px-2 text-white bg-black border-white/10"
          placeholder="Ej. 10-12"
        />
        <div class="flex flex-wrap gap-1 pt-0.5">
          <button
            type="button"
            class="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-300 border border-white/5 hover:bg-red-600 hover:text-white transition"
            @click="ex.repeticiones_logradas = '8'"
          >
            8
          </button>
          <button
            type="button"
            class="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-300 border border-white/5 hover:bg-red-600 hover:text-white transition"
            @click="ex.repeticiones_logradas = '10'"
          >
            10
          </button>
          <button
            type="button"
            class="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-300 border border-white/5 hover:bg-red-600 hover:text-white transition"
            @click="ex.repeticiones_logradas = '12'"
          >
            12
          </button>
          <button
            type="button"
            class="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-slate-300 border border-white/5 hover:bg-red-600 hover:text-white transition"
            @click="ex.repeticiones_logradas = 'Al fallo'"
          >
            Al fallo
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import {
  onSeriesChanged,
  adjustSeries,
  adjustWeight,
  setWeightToSuggested,
  onToggleExerciseCompleted,
} from '../../utils/exerciseDraft.js';
const ex = defineModel({ type: Object, required: true });
defineEmits(['rest']);
</script>

<style scoped src="../../styles/trainer-monitor.css"></style>
