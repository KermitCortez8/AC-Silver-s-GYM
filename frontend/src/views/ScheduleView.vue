<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Mi horario</p>
      <h1 class="mt-2 text-3xl font-black text-white">Horario matriculado</h1>
      <p class="mt-2 text-slate-300">Esta tabla se llena cuando eliges horarios desde Matricula.</p>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">{{ memberIdentity?.name || 'Cliente' }}</p>
          <h2 class="mt-2 text-2xl font-black text-white">Tabla semanal</h2>
        </div>
        <router-link to="/user/enrollment" class="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-bold text-slate-950">
          Matricular horario
        </router-link>
      </div>

      <div class="mt-5">
        <ExcelScheduleGrid
          title="Horario"
          subtitle="Para ver el detalle del servicio matriculado, presione sobre el bloque del horario"
          :items="calendarItems"
          file-name="mi-horario.xlsx"
        />
      </div>

      <p v-if="!myEnrollments.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-8 text-center text-slate-400">
        Tu horario esta vacio. Entra a Matricula para seleccionar un servicio.
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useAuth } from '../composables/useAuth';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { useGymStore } from '../stores/gymStore';
import { attendanceBelongsToClient, buildClientIdentityFromUser, findClientForUser, resolveClientIdForUser, weekdayFromISO } from '../utils/clientIdentity';

const { user } = useAuth();
const gymStore = useGymStore();
const member = computed(() => findClientForUser(user.value, gymStore.members));
const memberId = computed(() => Number(member.value?.id_cliente || resolveClientIdForUser(user.value, gymStore.members) || 0));
const memberIdentity = computed(() => member.value || buildClientIdentityFromUser(user.value, gymStore.members));

const myEnrollments = computed(() => {
  const idCliente = memberId.value;
  if (!idCliente) return [];
  return gymStore.enrollments.filter((item) => Number(item.id_cliente) === idCliente && item.estado !== 'CANCELADA');
});

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
      cliente_nombre: attendance ? 'OK Guardado' : 'Pendiente',
      entryTime: attendance?.entryTime || '',
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
