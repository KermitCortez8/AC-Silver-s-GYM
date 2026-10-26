<template>
  <div
    v-if="timer.active || timer.seconds > 0 || timer.finished"
    class="rounded-2xl border border-red-500/40 bg-black p-3 shadow-xl space-y-2"
  >
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span
          class="flex h-9 w-9 items-center justify-center rounded-xl bg-red-600/20 text-red-400 font-black border border-red-600/30"
        >
          <i class="fa-solid fa-stopwatch text-base"></i>
        </span>
        <div>
          <p
            class="text-[10px] uppercase tracking-wider text-slate-400 font-bold"
          >
            Cronómetro de Descanso En Vivo
          </p>
          <p
            class="text-lg font-black text-white"
            :class="{ 'text-emerald-400 animate-pulse': timer.seconds === 0 }"
          >
            {{ formatTimer(timer.seconds) }}
            <span
              v-if="timer.seconds === 0"
              class="text-xs font-extrabold text-emerald-400 ml-2"
              >¡Tiempo completado!</span
            >
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          v-if="!timer.active"
          class="rounded-xl bg-red-600 px-3.5 py-1.5 font-black text-white text-xs hover:bg-red-500 transition flex items-center gap-1.5"
          @click="timer.resume()"
        >
          <i class="fa-solid fa-play text-[10px]"></i>
          <span>{{ timer.seconds > 0 ? 'Reanudar' : 'Iniciar' }}</span>
        </button>
        <button
          v-else
          class="rounded-xl bg-amber-500 px-3.5 py-1.5 font-black text-slate-950 text-xs hover:bg-amber-400 transition flex items-center gap-1.5"
          @click="timer.pause"
        >
          <i class="fa-solid fa-pause text-[10px]"></i>
          <span>Pausar</span>
        </button>
        <button
          class="rounded-xl border border-white/10 bg-slate-900 px-3 py-1.5 text-xs font-bold text-slate-300 hover:bg-slate-800 transition flex items-center gap-1.5"
          @click="timer.reset"
        >
          <i class="fa-solid fa-rotate-right text-[10px]"></i>
          <span>Reiniciar</span>
        </button>
      </div>
    </div>

    <!-- Barra de progreso de tiempo en rojo sólido -->
    <div
      class="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-white/5"
    >
      <div
        class="bg-red-600 h-1.5 transition-all duration-1000"
        :style="{
          width:
            timer.initialSeconds > 0
              ? `${(timer.seconds / timer.initialSeconds) * 100}%`
              : '0%',
        }"
      ></div>
    </div>
  </div>
</template>
<script setup>
defineProps({ timer: { type: Object, required: true } });
const formatTimer = (totalSec) => {
  const value = Math.max(0, Number(totalSec) || 0);
  return `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`;
};
</script>
