<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Asistencia</p>
      <h1 class="mt-2 text-3xl font-black text-white">Control de entrada y salida</h1>
      <p class="mt-2 text-slate-300">Busca al cliente, revisa su horario matriculado y registra entrada/salida.</p>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Buscar cliente</p>
        <h2 class="mt-2 text-2xl font-black text-white">DNI o codigo</h2>

        <form class="mt-5 space-y-4" @submit.prevent="lookupClient">
          <div class="grid grid-cols-2 rounded-2xl border border-white/10 bg-slate-950/60 p-1">
            <button type="button" class="rounded-xl px-3 py-2 text-sm font-bold" :class="mode === 'dni' ? 'bg-cyan-400 text-slate-950' : 'text-slate-300'" @click="mode = 'dni'">DNI</button>
            <button type="button" class="rounded-xl px-3 py-2 text-sm font-bold" :class="mode === 'code' ? 'bg-cyan-400 text-slate-950' : 'text-slate-300'" @click="mode = 'code'">Codigo</button>
          </div>

          <input v-model="lookup" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" :placeholder="mode === 'dni' ? 'Ej. 12345678' : 'Ej. SGCLI001'" />
          <button class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950">Mostrar horario</button>
        </form>

        <div v-if="selectedClient" class="mt-5 rounded-2xl border border-white/10 bg-slate-900/80 p-4">
          <p class="font-bold text-white">{{ selectedClient.name }}</p>
          <p class="text-sm text-slate-400">{{ selectedClient.internalCode }} - DNI {{ selectedClient.dni }}</p>
          <p class="mt-2 text-sm text-slate-300">Membresia: {{ selectedClient.membershipStatus || selectedClient.status }}</p>
        </div>

        <p v-if="feedback" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'">
          {{ feedback }}
        </p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Horario realizado</p>
            <h2 class="mt-2 text-2xl font-black text-white">Matriculas del cliente</h2>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Hoy</p>
            <p class="text-xl font-black text-white">{{ attendanceAnalytics.today }}</p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="item in clientEnrollments" :key="item.id_matricula" class="rounded-2xl border border-white/10 bg-slate-900/80 p-5">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-lg font-bold text-white">{{ serviceLabel(item.servicio) }}</p>
                <p class="text-sm text-slate-400">{{ dayLabel(item.dia) }} {{ item.codigo_dia }} - {{ item.hora_inicio }} a {{ item.hora_fin }}</p>
                <p class="mt-2 text-sm text-slate-300">Entrada: {{ attendanceFor(item)?.entryTime || '-' }} · Salida: {{ attendanceFor(item)?.exitTime || '-' }}</p>
              </div>
              <div class="flex flex-wrap gap-2 lg:justify-end">
                <button
                  class="rounded-2xl bg-emerald-400 px-4 py-3 text-sm font-bold text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                  :disabled="Boolean(attendanceFor(item)?.entryTime)"
                  @click="registerEntry(item)"
                >
                  Entrada
                </button>
                <button
                  class="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-bold text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                  :disabled="!attendanceFor(item)?.id_asistencia || Boolean(attendanceFor(item)?.exitTime)"
                  @click="registerExit(item)"
                >
                  Salida
                </button>
              </div>
            </div>
          </article>
        </div>

        <p v-if="selectedClient && !clientEnrollments.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-center text-slate-400">
          Este cliente no tiene horarios matriculados.
        </p>
        <p v-if="!selectedClient" class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-center text-slate-400">
          Busca un cliente para ver su horario.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const mode = ref('dni');
const lookup = ref('');
const selectedClient = ref(null);
const feedback = ref('');
const feedbackTone = ref('success');

const attendanceAnalytics = computed(() => gymStore.attendanceAnalytics);
const clientEnrollments = computed(() => {
  const idCliente = Number(selectedClient.value?.id_cliente || 0);
  if (!idCliente) return [];
  return gymStore.enrollments.filter((item) => Number(item.id_cliente) === idCliente && item.estado !== 'CANCELADA');
});

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service;
const dayLabel = (day) => ({ lunes: 'Lunes', martes: 'Martes', miercoles: 'Miercoles', jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sabado', domingo: 'Domingo' })[day] || day;
const attendanceFor = (item) => gymStore.attendance.find((entry) => Number(entry.idMatricula) === Number(item.id_matricula));

const lookupClient = async () => {
  await gymStore.fetchFromBackend?.().catch(() => {});
  const query = lookup.value.trim().toUpperCase();
  selectedClient.value =
    mode.value === 'dni'
      ? gymStore.members.find((member) => String(member.dni) === lookup.value.trim()) || null
      : gymStore.members.find((member) => [member.id, member.internalCode].map((value) => String(value || '').toUpperCase()).includes(query)) || null;

  if (!selectedClient.value) {
    feedbackTone.value = 'error';
    feedback.value = 'Cliente no encontrado.';
    return;
  }

  await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: selectedClient.value.id_cliente }).catch(() => {});
  feedback.value = '';
};

const registerEntry = async (item) => {
  try {
    await gymStore.registerAttendanceEntry({
      id_matricula: item.id_matricula,
      fecha: new Date().toISOString().slice(0, 10),
      hora_entrada: new Date().toTimeString().slice(0, 5),
    });
    feedbackTone.value = 'success';
    feedback.value = 'Entrada registrada.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo registrar entrada.';
  }
};

const registerExit = async (item) => {
  const current = attendanceFor(item);
  if (!current?.id_asistencia) return;
  try {
    await gymStore.registerAttendanceExit({
      id_asistencia: current.id_asistencia,
      hora_salida: new Date().toTimeString().slice(0, 5),
    });
    feedbackTone.value = 'success';
    feedback.value = 'Salida registrada.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo registrar salida.';
  }
};
</script>
