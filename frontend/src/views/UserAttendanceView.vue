<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Miembro</p>
      <h1 class="mt-2 text-3xl font-black text-white">Mi asistencia</h1>
      <p class="mt-2 max-w-3xl text-slate-300">Genera un pase QR temporal y revisa tu historial de accesos sin depender de otra aplicación.</p>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Perfil</p>
        <div v-if="member" class="mt-4 space-y-4">
          <div>
            <p class="text-2xl font-black text-white">{{ member.name }}</p>
            <p class="text-slate-400">{{ member.email }}</p>
          </div>

          <div class="rounded-3xl bg-slate-950/70 p-4">
            <p class="text-sm text-slate-400">Estado de membresía</p>
            <p class="mt-1 text-xl font-bold text-white">{{ member.status }}</p>
          </div>
          <div class="rounded-3xl bg-slate-950/70 p-4">
            <p class="text-sm text-slate-400">Plan</p>
            <p class="mt-1 text-xl font-bold text-white">{{ member.plan }}</p>
          </div>
          <div class="rounded-3xl bg-slate-950/70 p-4">
            <p class="text-sm text-slate-400">Asistencia estimada</p>
            <p class="mt-1 text-xl font-bold text-white">{{ member.attendanceRate }}%</p>
          </div>

          <div class="rounded-3xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-cyan-50">
            <p class="text-[0.65rem] uppercase tracking-[0.5em] text-cyan-200">Tu código único</p>
            <p class="mt-2 text-3xl font-black tracking-[0.22em] text-white">{{ member.internalCode }}</p>
            <p class="mt-2 text-sm text-cyan-50/90">Usa este identificador para generar tu pase de acceso temporal.</p>
          </div>

          <button class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300" @click="generatePass">
            Generar pase QR
          </button>
        </div>

        <div v-else class="mt-4 rounded-[1.75rem] border border-amber-400/20 bg-amber-400/10 p-4 text-amber-100">
          Tu correo no coincide con un cliente registrado. Pide al administrador que te vincule.
        </div>
      </div>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex items-end justify-between gap-4">
          <div>
            <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Pase temporal</p>
            <h2 class="mt-2 text-2xl font-black text-white">Código y QR</h2>
          </div>
          <div class="rounded-2xl bg-slate-950/70 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Registros</p>
            <p class="text-xl font-black text-white">{{ visibleRecords.length }}</p>
          </div>
        </div>

        <div v-if="passImage" class="mt-5 grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
          <div class="rounded-[1.75rem] border border-white/10 bg-white p-4 text-slate-950">
            <img :src="passImage" alt="QR de acceso" class="mx-auto w-full max-w-[240px]" />
          </div>
          <div class="rounded-[1.75rem] border border-white/10 bg-slate-950/70 p-4">
            <p class="text-[0.65rem] uppercase tracking-[0.5em] text-cyan-200">Código temporal</p>
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

        <div v-if="visibleRecords.length" class="mt-5 rounded-[1.75rem] border border-emerald-400/20 bg-emerald-400/10 p-4 text-emerald-50">
          <p class="text-[0.65rem] uppercase tracking-[0.5em] text-emerald-200">Último acceso</p>
          <p class="mt-2 text-lg font-bold text-white">{{ visibleRecords[0].date }} · {{ visibleRecords[0].time }}</p>
          <p class="text-sm text-emerald-100/90">{{ visibleRecords[0].type }} · {{ visibleRecords[0].exercise }} · {{ visibleRecords[0].note || 'Sin observaciones' }}</p>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="entry in visibleRecords" :key="entry.id" class="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="font-semibold text-white">{{ entry.type }}</p>
                <p class="text-sm text-slate-400">{{ entry.memberCode }} · {{ entry.exercise || 'Sin ejercicio' }}</p>
                <p class="text-sm text-slate-400">{{ entry.note || 'Sin observaciones' }}</p>
              </div>
              <div class="text-sm text-slate-300 sm:text-right">
                <p class="font-semibold text-cyan-200">{{ entry.date }}</p>
                <p>{{ entry.time }}</p>
              </div>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import QRCode from 'qrcode';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';

const { user } = useAuth();
const gymStore = useGymStore();
const member = computed(() => gymStore.memberByEmail(user.value?.email));
const records = computed(() => gymStore.userAttendance(user.value?.email));
const historyFrom = ref('');
const historyTo = ref('');
const passImage = ref('');
const activePass = ref(null);

const activePassExpiration = computed(() => {
  if (!activePass.value?.expiresAt) {
    return 'Sin pase generado';
  }

  return new Date(activePass.value.expiresAt).toLocaleString();
});

const visibleRecords = computed(() =>
  records.value.filter((entry) => {
    const afterStart = !historyFrom.value || entry.date >= historyFrom.value;
    const beforeEnd = !historyTo.value || entry.date <= historyTo.value;
    return afterStart && beforeEnd;
  }),
);

const generatePass = async () => {
  if (!member.value) {
    return;
  }

  activePass.value = gymStore.createAttendancePass(member.value.id);
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
  if (member.value) {
    await generatePass();
  }
});
</script>
