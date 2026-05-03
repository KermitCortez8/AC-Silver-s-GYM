<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Agenda</p>
      <h1 class="mt-2 text-3xl font-black text-white">Horarios</h1>
      <p class="mt-2 text-slate-300">Vista pública de clases, apertura y cierre del gimnasio.</p>
    </section>

    <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article v-for="slot in schedule" :key="slot.day" class="rounded-3xl border border-white/10 bg-slate-900/80 p-5">
        <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">{{ slot.day }}</p>
        <p class="mt-3 text-lg font-bold text-white">{{ slot.hours }}</p>
        <p class="mt-2 text-sm text-slate-300">{{ slot.focus }}</p>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const schedule = computed(() => gymStore.schedule);
</script>
