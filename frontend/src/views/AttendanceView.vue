<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Operación</p>
      <h1 class="mt-2 text-3xl font-black text-white">Asistencia</h1>
      <p class="mt-2 max-w-3xl text-slate-300">Valida ingresos por DNI o código, consulta métricas de afluencia y revisa el historial en tiempo real.</p>
    </section>

    <section class="grid gap-4 md:grid-cols-4">
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Hoy</p>
        <p class="mt-2 text-3xl font-black text-white">{{ attendanceAnalytics.today }}</p>
      </article>
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Semana</p>
        <p class="mt-2 text-3xl font-black text-white">{{ attendanceAnalytics.week }}</p>
      </article>
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Mes</p>
        <p class="mt-2 text-3xl font-black text-white">{{ attendanceAnalytics.month }}</p>
      </article>
      <article class="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 backdrop-blur">
        <p class="text-sm text-slate-400">Alertas de membresía</p>
        <p class="mt-2 text-3xl font-black text-white">{{ membershipAlerts.length }}</p>
      </article>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.88fr_1.12fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Nuevo registro</p>
        <h2 class="mt-2 text-2xl font-black text-white">Check-in por DNI o código</h2>

        <div class="mt-5 space-y-4">
          <label class="block space-y-2">
            <span class="text-sm text-slate-300">DNI o código interno</span>
            <input
              v-model="form.identity"
              class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none placeholder:text-slate-500"
              placeholder="74281635 o CL-0001"
            />
          </label>

          <div class="grid gap-4 sm:grid-cols-2">
            <label class="block space-y-2">
              <span class="text-sm text-slate-300">Tipo</span>
              <select v-model="form.type" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
                <option>Entrada</option>
                <option>Salida</option>
              </select>
            </label>

            <label class="block space-y-2">
              <span class="text-sm text-slate-300">Modo</span>
              <select v-model="form.mode" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
                <option value="dni">DNI</option>
                <option value="code">Código interno</option>
              </select>
            </label>
          </div>

          <label class="block space-y-2">
            <span class="text-sm text-slate-300">Observación</span>
            <textarea v-model="form.note" rows="3" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Opcional"></textarea>
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          Validar y registrar
        </button>

        <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
          {{ feedbackMessage }}
        </p>

        <div v-if="validatedRecord" class="mt-4 rounded-[1.75rem] border border-emerald-400/20 bg-emerald-400/10 p-4 text-emerald-50">
          <p class="text-[0.65rem] uppercase tracking-[0.5em] text-emerald-200">Registro confirmado</p>
          <p class="mt-2 text-lg font-bold text-white">{{ validatedRecord.memberName }}</p>
          <p class="text-sm text-emerald-100/90">{{ validatedRecord.memberCode }} · {{ validatedRecord.date }} · {{ validatedRecord.time }}</p>
        </div>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex items-end justify-between gap-4">
          <div>
            <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Historial</p>
            <h2 class="mt-2 text-2xl font-black text-white">Últimos registros</h2>
          </div>
          <div class="rounded-2xl bg-slate-950/70 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Hoy</p>
            <p class="text-xl font-black text-white">{{ stats.attendanceToday }}</p>
          </div>
        </div>

        <div v-if="membershipAlerts.length" class="mt-5 rounded-[1.75rem] border border-amber-400/20 bg-amber-400/10 p-4 text-amber-50">
          <p class="text-[0.65rem] uppercase tracking-[0.5em] text-amber-200">Alertas de vencimiento</p>
          <div class="mt-3 space-y-2 text-sm">
            <p v-for="member in membershipAlerts.slice(0, 3)" :key="member.id">
              {{ member.name }} · vence en {{ member.daysUntilExpiry }} día(s)
            </p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="entry in recentAttendance" :key="entry.id" class="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="font-semibold text-white">{{ entry.memberName }}</p>
                <p class="text-sm text-slate-400">{{ entry.memberCode }} · {{ entry.exercise }}</p>
                <p class="text-sm text-slate-400">{{ entry.note }}</p>
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
  identity: '',
  type: 'Entrada',
  note: '',
  mode: 'dni',
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
  if (!form.identity.trim()) {
    feedbackTone.value = 'error';
    feedbackMessage.value = 'Ingresa un DNI o código válido.';
    return;
  }

  try {
    const record = form.mode === 'code'
      ? await gymStore.recordAttendanceByCode(form.identity, '', form.type, form.note)
      : await gymStore.checkinByDni(form.identity);

    validatedRecord.value = {
      memberName: record?.memberName || `Cliente ${form.identity}`,
      memberCode: record?.memberCode || form.identity,
      date: record?.fecha || record?.date || todayISO(),
      time: record?.hora || record?.time || '',
      type: record?.type || form.type,
    };
    feedbackTone.value = 'success';
    feedbackMessage.value = 'Asistencia registrada correctamente.';
    form.identity = '';
    form.note = '';
  } catch (error) {
    validatedRecord.value = null;
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo validar el acceso.';
  }
};

const todayISO = () => new Date().toISOString().slice(0, 10);
</script>
