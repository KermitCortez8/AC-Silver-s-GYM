<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Miembro</p>
      <h1 class="mt-2 text-3xl font-black text-white">Mi asistencia</h1>
      <p class="mt-2 text-slate-300">Genera tu código de verificación para que recepción valide tu ingreso.</p>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Perfil</p>
        <div v-if="member" class="mt-4 space-y-4">
          <div>
            <p class="text-2xl font-black text-white">{{ member.name }}</p>
            <p class="text-slate-400">{{ member.email }}</p>
          </div>

          <div class="rounded-3xl bg-slate-900/80 p-4">
            <p class="text-sm text-slate-400">Estado de membresía</p>
            <p class="mt-1 text-xl font-bold text-white">{{ member.status }}</p>
          </div>
          <div class="rounded-3xl bg-slate-900/80 p-4">
            <p class="text-sm text-slate-400">Plan</p>
            <p class="mt-1 text-xl font-bold text-white">{{ member.plan }}</p>
          </div>
          <div class="rounded-3xl bg-slate-900/80 p-4">
            <p class="text-sm text-slate-400">Asistencia estimada</p>
            <p class="mt-1 text-xl font-bold text-white">{{ member.attendanceRate }}%</p>
          </div>

          <div class="rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-200">
            <p class="font-semibold text-white">Código emitido por recepción</p>
            <p class="mt-1 text-slate-300">Si no aparece ningún código, solicita uno al administrador.</p>
          </div>

          <div v-if="currentPass" class="rounded-3xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-cyan-50">
            <p class="text-xs uppercase tracking-[0.35em] text-cyan-200">Pase activo</p>
            <div class="mt-3 space-y-3">
              <div>
                <p class="text-sm text-cyan-100/80">Código de verificación</p>
                <p class="mt-1 break-all text-2xl font-black tracking-[0.22em] text-white">{{ currentPass.code }}</p>
              </div>
              <div>
                <p class="text-sm text-cyan-100/80">Vence</p>
                <p class="mt-1 font-semibold text-white">{{ passExpiryLabel }}</p>
              </div>
              <p class="text-sm text-cyan-50/90">
                Comparte este código en recepción para validar tu ingreso.
              </p>
              <div class="flex gap-3">
                <button class="flex-1 rounded-2xl bg-white px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-100" @click="copyCode">
                  Copiar código
                </button>
              </div>
              <p v-if="copyFeedback" class="text-sm text-cyan-100">{{ copyFeedback }}</p>
            </div>
          </div>
        </div>

        <div v-else class="mt-4 rounded-3xl border border-amber-400/20 bg-amber-400/10 p-4 text-amber-100">
          Tu correo no coincide con un miembro registrado en la demo.
        </div>
      </div>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex items-end justify-between gap-4">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
            <h2 class="mt-2 text-2xl font-black text-white">Tus últimos movimientos</h2>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Registros</p>
            <p class="text-xl font-black text-white">{{ visibleRecords.length }}</p>
          </div>
        </div>

        <div class="mt-4 grid gap-3 sm:grid-cols-2">
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
          <article v-for="entry in visibleRecords" :key="entry.id" class="rounded-3xl border border-white/10 bg-slate-900/80 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="font-semibold text-white">{{ entry.type }}</p>
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
import { computed, ref } from 'vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';

const { user } = useAuth();
const gymStore = useGymStore();

const member = computed(() => gymStore.memberByEmail(user.value?.email));
const records = computed(() => gymStore.userAttendance(user.value?.email));
const historyFrom = ref('');
const historyTo = ref('');
const visibleRecords = computed(() =>
  records.value.filter((entry) => {
    const afterStart = !historyFrom.value || entry.date >= historyFrom.value;
    const beforeEnd = !historyTo.value || entry.date <= historyTo.value;
    return afterStart && beforeEnd;
  }),
);
const currentPass = computed(() => (member.value ? gymStore.activeAttendancePass(member.value.id) : null));
const copyFeedback = ref('');

const passExpiryLabel = computed(() => {
  if (!currentPass.value?.expiresAt) {
    return 'Sin vencimiento';
  }

  return new Date(currentPass.value.expiresAt).toLocaleString();
});

const copyCode = async () => {
  if (!currentPass.value?.code || typeof navigator === 'undefined' || !navigator.clipboard) {
    copyFeedback.value = 'No se pudo copiar automáticamente.';
    return;
  }

  await navigator.clipboard.writeText(currentPass.value.code);
  copyFeedback.value = 'Código copiado al portapapeles.';
};
</script>
