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

      <div v-if="calendarItems.length" class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <article v-for="item in calendarItems" :key="item.id_matricula" class="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="font-bold text-white">{{ serviceLabel(item.servicio) }}</p>
              <p class="mt-1 text-sm text-slate-400">{{ dayLabel(item.dia) }} - {{ item.hora_inicio }} a {{ item.hora_fin }}</p>
            </div>
            <span class="rounded-full px-3 py-1 text-xs font-black" :class="item.attendanceSaved ? 'bg-emerald-400/20 text-emerald-100' : 'bg-amber-400/20 text-amber-100'">
              {{ item.attendanceSaved ? 'OK' : 'Pendiente' }}
            </span>
          </div>
          <div class="mt-3 grid gap-2 text-sm text-slate-300 sm:grid-cols-2">
            <p>Entrada: <span class="font-bold text-white">{{ item.entryTime || 'pendiente' }}</span></p>
            <p>Salida: <span class="font-bold text-white">{{ item.exitTime || 'pendiente' }}</span></p>
          </div>
        </article>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Perfil</p>
        <div v-if="profileMember" class="mt-4 space-y-4">
          <div>
            <p class="text-2xl font-black text-white">{{ profileMember.name }}</p>
            <p class="text-slate-400">{{ profileMember.email }}</p>
          </div>

          <div class="rounded-2xl bg-slate-950/70 p-4">
            <p class="text-sm text-slate-400">Estado de membresia</p>
            <p class="mt-1 text-xl font-bold text-white">{{ profileMember.membershipStatus || profileMember.status || 'Pendiente' }}</p>
          </div>
          <div class="rounded-2xl bg-slate-950/70 p-4">
            <p class="text-sm text-slate-400">Plan</p>
            <p class="mt-1 text-xl font-bold text-white">{{ profileMember.plan || 'Sin plan' }}</p>
          </div>
          <div class="rounded-2xl bg-slate-950/70 p-4">
            <p class="text-sm text-slate-400">Vigencia</p>
            <p class="mt-1 text-xl font-bold text-white">{{ profileMember.membershipEnd || 'pendiente' }}</p>
          </div>

          <div class="rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-amber-50">
            <p class="text-xs uppercase tracking-[0.35em] text-amber-200">Tu codigo unico</p>
            <p class="mt-2 text-3xl font-black tracking-[0.22em] text-white">{{ profileMember.internalCode || profileMember.id }}</p>
            <p class="mt-2 text-sm text-amber-50/90">Usa este identificador para generar tu pase de acceso temporal.</p>
          </div>

          <button class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300" @click="generatePass">
            Generar pase QR
          </button>
        </div>

        <div v-else class="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-amber-100">
          No encontramos tu cliente vinculado. Verifica que tu usuario tenga el mismo correo, DNI o codigo de cliente registrado.
        </div>
      </div>

      <div class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex items-end justify-between gap-4">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
            <h2 class="mt-2 text-2xl font-black text-white">Entradas y salidas</h2>
          </div>
          <div class="rounded-2xl bg-slate-950/70 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Registros</p>
            <p class="text-xl font-black text-white">{{ visibleRecords.length }}</p>
          </div>
        </div>

        <div v-if="passImage" class="mt-5 grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
          <div class="rounded-2xl border border-white/10 bg-white p-4 text-slate-950">
            <img :src="passImage" alt="QR de acceso" class="mx-auto w-full max-w-[240px]" />
          </div>
          <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
            <p class="text-xs uppercase tracking-[0.35em] text-amber-200">Codigo temporal</p>
            <p class="mt-2 break-all text-sm text-slate-300">{{ activePass?.qrPayload }}</p>
            <p class="mt-4 text-sm text-slate-400">Expira en {{ activePassExpiration }}</p>
          </div>
        </div>

        <div class="mt-6 grid gap-3 sm:grid-cols-2">
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Desde</span>
            <input v-model="historyFrom" type="date" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Hasta</span>
            <input v-model="historyTo" type="date" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="entry in visibleRecords" :key="entry.id" class="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="font-semibold text-white">{{ serviceLabel(entry.service || entry.servicio || 'fitness') }}</p>
                <p class="text-sm text-slate-400">{{ entry.memberCode || profileMember?.internalCode }}</p>
              </div>
              <div class="text-sm text-slate-300 sm:text-right">
                <p class="font-semibold text-amber-200">{{ entry.date }}</p>
                <p>Entrada: {{ entry.entryTime || entry.time || 'pendiente' }}</p>
                <p>Salida: {{ entry.exitTime || 'pendiente' }}</p>
              </div>
            </div>
          </article>
        </div>

        <p v-if="!visibleRecords.length" class="mt-5 rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-400">
          Todavia no hay registros de asistencia para mostrar.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import QRCode from 'qrcode';
import ExcelScheduleGrid from '../components/ExcelScheduleGrid.vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';
import { attendanceBelongsToClient, buildClientIdentityFromUser, findClientForUser, resolveClientIdForUser, weekdayFromISO } from '../utils/clientIdentity';

const { user } = useAuth();
const gymStore = useGymStore();
const member = computed(() => findClientForUser(user.value, gymStore.members));
const memberId = computed(() => Number(member.value?.id_cliente || resolveClientIdForUser(user.value, gymStore.members) || 0));
const memberIdentity = computed(() => member.value || buildClientIdentityFromUser(user.value, gymStore.members));
const profileMember = computed(() => member.value || memberIdentity.value);
const historyFrom = ref('');
const historyTo = ref('');
const passImage = ref('');
const activePass = ref(null);

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

const activePassExpiration = computed(() => {
  if (!activePass.value?.expiresAt) return 'Sin pase generado';
  return new Date(activePass.value.expiresAt).toLocaleString();
});

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

const generatePass = async () => {
  if (!profileMember.value) return;

  activePass.value = gymStore.createAttendancePass(profileMember.value.id || profileMember.value.internalCode || profileMember.value.memberCode);
  passImage.value = await QRCode.toDataURL(activePass.value.qrPayload, {
    margin: 1,
    width: 240,
    color: {
      dark: '#0f172a',
      light: '#ffffff',
    },
  });
};

onMounted(async () => {
  await gymStore.fetchFromBackend?.().catch(() => {});
  if (memberId.value) {
    await gymStore.refreshEnrollmentsFromBackend?.({ id_cliente: memberId.value }).catch(() => {});
    await gymStore.refreshAttendanceFromBackend?.().catch(() => {});
    await generatePass().catch(() => {});
  }
});
</script>
