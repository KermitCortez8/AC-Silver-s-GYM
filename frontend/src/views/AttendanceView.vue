<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Operación</p>
      <h1 class="mt-2 text-3xl font-black text-white">Asistencia</h1>
      <p class="mt-2 text-slate-300">Recibe el código personal del usuario, valida membresías vigentes y consulta la afluencia del local.</p>
    </section>

    <section class="grid gap-4 md:grid-cols-4">
      <article class="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Hoy</p>
        <p class="mt-2 text-3xl font-black text-white">{{ attendanceAnalytics.today }}</p>
      </article>
      <article class="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Semana</p>
        <p class="mt-2 text-3xl font-black text-white">{{ attendanceAnalytics.week }}</p>
      </article>
      <article class="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Mes</p>
        <p class="mt-2 text-3xl font-black text-white">{{ attendanceAnalytics.month }}</p>
      </article>
      <article class="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Membresías por vencer</p>
        <p class="mt-2 text-3xl font-black text-white">{{ membershipAlerts.length }}</p>
      </article>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Nuevo registro</p>
        <h2 class="mt-2 text-2xl font-black text-white">Registrar asistencia por código único</h2>

        <div class="mt-5 space-y-4">
          <label class="space-y-2 block">
            <span class="text-sm text-slate-300">Código único del usuario</span>
            <textarea
              v-model="form.passInput"
              rows="4"
              class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none"
              placeholder="Ej. GYM-0001"
            ></textarea>
          </label>

          <label class="space-y-2 block">
            <span class="text-sm text-slate-300">Tipo</span>
            <select v-model="form.type" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option>Entrada</option>
              <option>Salida</option>
            </select>
          </label>

          <label class="space-y-2 block">
            <span class="text-sm text-slate-300">Ejercicio realizado</span>
            <input v-model="form.exercise" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Ej. pierna, cardio, espalda" />
          </label>

          <label class="space-y-2 block">
            <span class="text-sm text-slate-300">Nota</span>
            <textarea v-model="form.note" rows="4" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Observación opcional"></textarea>
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          Validar y registrar
        </button>

        <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
          {{ feedbackMessage }}
        </p>

        <div v-if="validatedRecord" class="mt-4 rounded-3xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-emerald-50">
          <p class="text-xs uppercase tracking-[0.35em] text-emerald-200">Registro confirmado</p>
          <p class="mt-2 text-lg font-bold text-white">{{ validatedRecord.memberName }}</p>
          <p class="text-sm text-emerald-100/90">{{ validatedRecord.memberCode }} · {{ validatedRecord.exercise }}</p>
          <p class="text-sm text-emerald-100/90">{{ validatedRecord.date }} · {{ validatedRecord.time }} · {{ validatedRecord.type }}</p>
        </div>
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

        <div v-if="membershipAlerts.length" class="mt-5 rounded-3xl border border-amber-400/20 bg-amber-400/10 p-4 text-amber-50">
          <p class="text-xs uppercase tracking-[0.35em] text-amber-200">Alertas de vencimiento</p>
          <div class="mt-3 space-y-2 text-sm">
            <p v-for="member in membershipAlerts.slice(0, 3)" :key="member.id">
              {{ member.name }} · vence en {{ member.daysUntilExpiry }} día(s)
            </p>
          </div>
        </div>

        <div v-if="recentAttendance.length" class="mt-5 rounded-3xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-cyan-50">
          <p class="text-xs uppercase tracking-[0.35em] text-cyan-200">Ejemplo de asistencia guardada</p>
          <p class="mt-2 text-lg font-bold text-white">{{ recentAttendance[0].memberName }} · {{ recentAttendance[0].memberCode }}</p>
          <p class="text-sm text-cyan-100/90">{{ recentAttendance[0].exercise }} · {{ recentAttendance[0].date }} · {{ recentAttendance[0].time }}</p>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="entry in recentAttendance" :key="entry.id" class="rounded-3xl border border-white/10 bg-slate-900/80 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="font-semibold text-white">{{ entry.memberName }}</p>
                <p class="text-sm text-slate-400">{{ entry.memberCode }} · {{ entry.exercise || 'Sin ejercicio' }}</p>
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
import { computed, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const recentAttendance = computed(() => gymStore.recentAttendance.slice(0, 12));
const stats = computed(() => gymStore.stats);
const attendanceAnalytics = computed(() => gymStore.attendanceAnalytics);
const membershipAlerts = computed(() => gymStore.membershipAlerts);
const feedbackMessage = ref('');
const feedbackTone = ref('info');
const validatedRecord = ref(null);

const form = reactive({
  passInput: '',
  type: 'Entrada',
  exercise: '',
  note: '',
});

const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success') {
    return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50';
  }

  if (feedbackTone.value === 'error') {
    return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  }

  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

const handleSubmit = async () => {
  if (!form.passInput.trim()) {
    feedbackTone.value = 'error';
    feedbackMessage.value = 'Ingresa el código del usuario.';
    return;
  }

  try {
    const record = await gymStore.recordAttendanceByCode(form.passInput, form.exercise, form.type, form.note);
    validatedRecord.value = record;
    feedbackTone.value = 'success';
    feedbackMessage.value = `Asistencia guardada para ${record.memberName}.`;
    form.passInput = '';
    form.exercise = '';
    form.note = '';
  } catch (error) {
    validatedRecord.value = null;
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo validar el código.';
  }
};
</script>
