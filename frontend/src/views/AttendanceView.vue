<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Operación</p>
      <h1 class="mt-2 text-3xl font-black text-white">Asistencia</h1>
      <p class="mt-2 text-slate-300">Registra entradas y salidas, y revisa el historial reciente.</p>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Nuevo registro</p>
        <h2 class="mt-2 text-2xl font-black text-white">Marcar asistencia</h2>

        <div class="mt-5 space-y-4">
          <label class="space-y-2 block">
            <span class="text-sm text-slate-300">Miembro</span>
            <select v-model="form.memberId" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option value="">Seleccionar miembro</option>
              <option v-for="member in members" :key="member.id" :value="member.id">{{ member.name }} · {{ member.plan }}</option>
            </select>
          </label>

          <label class="space-y-2 block">
            <span class="text-sm text-slate-300">Tipo</span>
            <select v-model="form.type" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option>Entrada</option>
              <option>Salida</option>
            </select>
          </label>

          <label class="space-y-2 block">
            <span class="text-sm text-slate-300">Nota</span>
            <textarea v-model="form.note" rows="4" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Ej. rutina de tren superior"></textarea>
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          Registrar
        </button>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex items-end justify-between gap-4">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
            <h2 class="mt-2 text-2xl font-black text-white">Últimos registros</h2>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Hoy</p>
            <p class="text-xl font-black text-white">{{ stats.attendanceToday }}</p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="entry in recentAttendance" :key="entry.id" class="rounded-3xl border border-white/10 bg-slate-900/80 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="font-semibold text-white">{{ entry.memberName }}</p>
                <p class="text-sm text-slate-400">{{ entry.note || 'Sin observaciones' }}</p>
              </div>
              <div class="text-sm text-slate-300 sm:text-right">
                <p class="font-semibold text-cyan-200">{{ entry.type }}</p>
                <p>{{ entry.date }} · {{ entry.time }}</p>
              </div>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const members = computed(() => gymStore.members);
const recentAttendance = computed(() => gymStore.recentAttendance.slice(0, 12));
const stats = computed(() => gymStore.stats);

const form = reactive({
  memberId: '',
  type: 'Entrada',
  note: '',
});

const handleSubmit = () => {
  if (!form.memberId) {
    return;
  }

  gymStore.recordAttendance(form.memberId, form.type, form.note);
  form.type = 'Entrada';
  form.note = '';
};
</script>
