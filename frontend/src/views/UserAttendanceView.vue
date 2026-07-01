<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Miembro</p>
      <h1 class="mt-2 text-3xl font-black text-white">Mi asistencia</h1>
      <p class="mt-2 max-w-3xl text-slate-300">Revisa tu horario matriculado y confirma tus registros de entrada y salida.</p>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Horario</p>
          <h2 class="mt-2 text-2xl font-black text-white">Mi horario y asistencia</h2>
          <p class="mt-2 text-slate-300">Cada bloque muestra un check cuando ya tiene entrada registrada y la salida cuando fue guardada.</p>
        </div>
        <router-link to="/user/enrollment" class="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-bold text-slate-950">
          Matricular horario
        </router-link>
      </div>

      <div class="mt-5">
        <ExcelScheduleGrid
          title="Horario"
          subtitle="Los bloques con check corresponden a tu asistencia registrada."
          :items="calendarItems"
          file-name="mi-asistencia.xlsx"
          empty-message="Tu horario esta vacio. Matriculate en un servicio para verlo aqui."
        />
      </div>

    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
          <h2 class="mt-2 text-2xl font-black text-white">Entradas y salidas</h2>
          <p class="mt-1 text-sm text-slate-400">{{ visibleRecords.length }} registros encontrados</p>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Desde</span>
            <input v-model="historyFrom" type="date" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Hasta</span>
            <input v-model="historyTo" type="date" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
        </div>
      </div>

      <div class="mt-5 overflow-hidden rounded-2xl border border-white/10">
        <div class="hidden grid-cols-[1fr_1fr_1fr_1fr] gap-4 bg-slate-950/80 px-5 py-3 text-xs uppercase tracking-[0.22em] text-slate-400 md:grid">
          <span>Servicio</span>
          <span>Fecha</span>
          <span>Entrada</span>
          <span>Salida</span>
        </div>
        <article v-for="entry in visibleRecords" :key="entry.id" class="grid gap-3 border-t border-white/10 bg-slate-900/70 px-5 py-4 md:grid-cols-[1fr_1fr_1fr_1fr] md:items-center">
          <p class="font-semibold text-white">{{ serviceLabel(entry.service || entry.servicio || 'fitness') }}</p>
          <p class="text-sm text-slate-300">{{ entry.date || '-' }}</p>
          <p class="text-sm text-emerald-100">{{ entry.entryTime || entry.time || 'pendiente' }}</p>
          <p class="text-sm text-cyan-100">{{ entry.exitTime || 'pendiente' }}</p>
        </article>
      </div>

      <p v-if="!visibleRecords.length" class="mt-5 rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-400">
        Todavia no hay registros de asistencia para mostrar.
      </p>

      <div v-if="!memberId" class="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-100">
        No encontramos tu cliente vinculado. Verifica que tu correo o DNI coincida con el registro.
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';
import { attendanceBelongsToClient, buildClientIdentityFromUser, findClientForUser, resolveClientIdForUser, weekdayFromISO } from '../utils/clientIdentity';

const { user } = useAuth();
const gymStore = useGymStore();
const member = computed(() => findClientForUser(user.value, gymStore.members));
const memberId = computed(() => Number(member.value?.id_cliente || resolveClientIdForUser(user.value, gymStore.members) || 0));
const memberIdentity = computed(() => member.value || buildClientIdentityFromUser(user.value, gymStore.members));
const historyFrom = ref('');
const historyTo = ref('');

const myEnrollments = computed(() => {
  const idCliente = memberId.value;
  if (!idCliente) return [];
  return gymStore.enrollments.filter((item) => Number(item.id_cliente) === idCliente && item.estado !== 'CANCELADA');
});

const enrollmentIds = computed(() => new Set(myEnrollments.value.map((item) => Number(item.id_matricula))));

const records = computed(() =>
  gymStore.attendance
    .filter((entry) => enrollmentIds.value.has(Number(entry.idMatricula)) || attendanceBelongsToClient(entry, memberIdentity.value))
    .slice(0, 20),
);

const visibleRecords = computed(() =>
  records.value.filter((entry) => {
    const afterStart = !historyFrom.value || entry.date >= historyFrom.value;
    const beforeEnd = !historyTo.value || entry.date <= historyTo.value;
    return afterStart && beforeEnd;
  }),
);

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service;
const dayLabel = (day) => ({ lunes: 'Lunes', martes: 'Martes', miercoles: 'Miercoles', jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sabado', domingo: 'Domingo' })[day] || day;

const attendanceFor = (item) =>
  gymStore.attendance.find((entry) => {
    const byEnrollment = Number(entry.idMatricula || 0) === Number(item.id_matricula || 0) && Number(item.id_matricula || 0) > 0;
    const bySchedule = Number(entry.idHorarioServicio || 0) === Number(item.id_horario_servicio || 0) && Number(item.id_horario_servicio || 0) > 0;
    const byClientSchedule =
      attendanceBelongsToClient(entry, memberIdentity.value) &&
      String(entry.service || '').toLowerCase() === String(item.servicio || '').toLowerCase() &&
      weekdayFromISO(entry.date) === String(item.dia || '').toLowerCase();

    return byEnrollment || bySchedule || byClientSchedule;
  });

const calendarItems = computed(() =>
  myEnrollments.value.map((item) => {
    const attendance = attendanceFor(item);
    return {
      ...item,
      attendanceSaved: Boolean(attendance),
      cliente_nombre: attendance ? 'OK Guardado' : 'Pendiente',
      entryTime: attendance?.entryTime || attendance?.time || '',
      exitTime: attendance?.exitTime || '',
      checkLabel: attendance
        ? `OK Entrada ${attendance.entryTime || attendance.time || '--:--'} / Salida ${attendance.exitTime || 'pendiente'}`
        : 'Pendiente',
    };
  }),
);

onMounted(async () => {
  await gymStore.fetchFromBackend?.().catch(() => {});
  if (memberId.value) {
    await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: memberId.value }).catch(() => {});
    await gymStore.refreshAttendanceFromBackend?.().catch(() => {});
  }
});
</script>
