<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Matricula</p>
      <h1 class="mt-2 text-3xl font-black text-white">Matricula de horarios</h1>
      <p class="mt-2 text-slate-300">
        {{ isAdminUser ? 'Busca un cliente por DNI y matriculalo en un horario disponible.' : 'Selecciona el horario que prefieras para tus servicios.' }}
      </p>
    </section>

    <section v-if="isAdminUser" class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <form class="flex flex-col gap-3 sm:flex-row" @submit.prevent="loadAdminClient">
        <input v-model="dniSearch" class="flex-1 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="DNI del cliente" />
        <button class="rounded-2xl bg-cyan-400 px-5 py-3 font-bold text-slate-950">Buscar horarios</button>
      </form>
      <p v-if="selectedClient" class="mt-4 text-sm text-slate-300">
        Cliente seleccionado: <span class="font-bold text-white">{{ selectedClient.name }}</span> - {{ selectedClient.dni }}
      </p>
    </section>

    <ExcelScheduleGrid
      title="Horario del cliente"
      :subtitle="calendarSubtitle"
      :items="visibleEnrollments"
      file-name="horario-cliente.xlsx"
      empty-message="Aun no hay horarios matriculados para este cliente."
    />

    <section class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Disponibles</p>
            <h2 class="mt-2 text-2xl font-black text-white">Horarios de servicios</h2>
          </div>
          <button class="rounded-2xl border border-white/10 bg-slate-900/80 px-4 py-3 text-sm font-bold text-white" @click="refreshAll">Actualizar</button>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="schedule in schedules" :key="schedule.id_horario_servicio" class="rounded-2xl border border-white/10 bg-slate-900/80 p-5">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-lg font-bold text-white">{{ serviceLabel(schedule.servicio) }}</p>
                <p class="text-sm text-slate-400">{{ dayLabel(schedule.dia) }} {{ schedule.codigo_dia }} - {{ schedule.hora_inicio }} a {{ schedule.hora_fin }}</p>
                <p class="mt-1 text-sm text-slate-300">Cupos: {{ schedule.cupos_usados || 0 }} / {{ schedule.cupos }}</p>
              </div>
              <button
                class="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                :disabled="isScheduleClosed(schedule)"
                @click="enroll(schedule)"
              >
                {{ buttonLabel(schedule) }}
              </button>
            </div>
          </article>
        </div>

        <p v-if="!schedules.length" class="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400">
          No hay horarios activos.
        </p>
      </div>

      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Seleccionados</p>
        <h2 class="mt-2 text-2xl font-black text-white">Horario del cliente</h2>

        <div class="mt-5 space-y-3">
          <article v-for="item in visibleEnrollments" :key="item.id_matricula" class="rounded-2xl border border-white/10 bg-slate-900/80 p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="font-bold text-white">{{ serviceLabel(item.servicio) }}</p>
                <p class="text-sm text-slate-400">{{ dayLabel(item.dia) }} - {{ item.hora_inicio }} a {{ item.hora_fin }}</p>
                <p class="text-xs text-slate-500">Matricula #{{ item.id_matricula }}</p>
              </div>
              <button class="rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-100 hover:bg-rose-400/10" @click="cancel(item)">
                Quitar
              </button>
            </div>
          </article>
        </div>

        <p v-if="!visibleEnrollments.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-400">
          Aun no hay horarios matriculados.
        </p>

        <p v-if="feedback" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50'">
          {{ feedback }}
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';

const { user, isAdmin } = useAuth();
const gymStore = useGymStore();
const dniSearch = ref('');
const selectedClient = ref(null);
const feedback = ref('');
const feedbackTone = ref('success');

const schedules = computed(() => gymStore.serviceSchedules.filter((schedule) => schedule.activo !== false));
const readMaybeRef = (value) => value?.value ?? value;
const isAdminUser = computed(() => Boolean(readMaybeRef(isAdmin)));
const authUser = computed(() => readMaybeRef(user) || {});
const normalizeDni = (value) => String(value || '').replace(/\D/g, '');
const normalizeCode = (value) => String(value || '').trim().toUpperCase();

const findClientForAuthUser = () => {
  const currentUser = authUser.value;
  const idCliente = Number(currentUser.id_cliente || 0);
  const idUsuario = normalizeCode(currentUser.id_usuario || currentUser.id);
  const email = String(currentUser.email || currentUser.correo || '').trim().toLowerCase();

  return (
    gymStore.members.find((member) => Number(member.id_cliente || 0) === idCliente && idCliente > 0) ||
    gymStore.members.find((member) => [member.id, member.internalCode].map(normalizeCode).includes(idUsuario) && idUsuario) ||
    gymStore.memberByEmail(email) ||
    null
  );
};

const currentClient = computed(() => (isAdminUser.value ? selectedClient.value : findClientForAuthUser()));
const visibleEnrollments = computed(() => {
  const idCliente = Number(currentClient.value?.id_cliente || 0);
  if (!idCliente) return [];
  return gymStore.enrollments.filter((item) => Number(item.id_cliente) === idCliente && item.estado !== 'CANCELADA');
});
const calendarSubtitle = computed(() => {
  if (isAdminUser.value && !selectedClient.value) return 'Busca un cliente por DNI para ver su horario matriculado.';
  return 'Este horario se actualiza cada vez que se agrega o quita una matricula.';
});

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service;
const dayLabel = (day) => ({ lunes: 'Lunes', martes: 'Martes', miercoles: 'Miercoles', jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sabado', domingo: 'Domingo' })[day] || day;

const alreadyEnrolled = (schedule) =>
  visibleEnrollments.value.some((item) => Number(item.id_horario_servicio) === Number(schedule.id_horario_servicio));

const isScheduleFull = (schedule) => Number(schedule.cupos_usados || 0) >= Number(schedule.cupos || 0);
const isScheduleClosed = (schedule) => alreadyEnrolled(schedule) || isScheduleFull(schedule);
const buttonLabel = (schedule) => {
  if (alreadyEnrolled(schedule)) return 'Ya matriculado';
  if (isScheduleFull(schedule)) return 'Sin cupos';
  return 'Matricular';
};

const refreshAll = async () => {
  await gymStore.fetchFromBackend?.().catch(async () => {
    await gymStore.refreshServiceSchedulesFromBackend?.();
    await gymStore.refreshEnrollmentsFromBackend?.();
  });
};

const loadAdminClient = async () => {
  await gymStore.fetchFromBackend?.().catch(() => {});
  const dni = normalizeDni(dniSearch.value);
  selectedClient.value = gymStore.members.find((member) => normalizeDni(member.dni) === dni) || null;
  if (!selectedClient.value) {
    feedbackTone.value = 'error';
    feedback.value = 'Cliente no encontrado por DNI.';
    return;
  }
  await gymStore.refreshEnrollmentsFromBackend({ dni: dniSearch.value });
  feedback.value = '';
};

const enroll = async (schedule) => {
  if (!currentClient.value?.id_cliente) {
    feedbackTone.value = 'error';
    feedback.value = isAdminUser.value ? 'Busca primero un cliente por DNI.' : 'No se encontro tu cliente.';
    return;
  }
  try {
    await gymStore.enrollSchedule({
      id_cliente: currentClient.value.id_cliente,
      id_horario_servicio: schedule.id_horario_servicio,
    });
    await gymStore.refreshEnrollmentsFromBackend({ id_cliente: currentClient.value.id_cliente });
    feedbackTone.value = 'success';
    feedback.value = 'Matricula registrada.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo matricular.';
  }
};

const cancel = async (item) => {
  try {
    await gymStore.deleteEnrollment(item.id_matricula);
    feedbackTone.value = 'success';
    feedback.value = 'Matricula cancelada.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo cancelar.';
  }
};

onMounted(refreshAll);
</script>
