<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Operacion</p>
      <h1 class="mt-2 text-3xl font-black text-white">Configuracion del gimnasio</h1>
      <p class="mt-2 text-slate-300">Controla aforo diario y capacidad por hora para check-in y horarios.</p>
    </section>

    <p v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">{{ feedback }}</p>

    <section class="grid gap-5 lg:grid-cols-[420px_1fr]">
      <form class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="save">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Aforo</p>
        <h2 class="mt-2 text-2xl font-black text-white">Limites operativos</h2>
        <div class="mt-5 space-y-4">
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Capacidad total diaria</span>
            <input v-model.number="form.capacidad_total" type="number" min="1" class="field-input" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Capacidad por hora</span>
            <input v-model.number="form.capacidad_por_hora" type="number" min="1" class="field-input" />
          </label>
        </div>
        <button class="mt-5 w-full rounded-2xl bg-emerald-400 px-4 py-3 font-black text-slate-950">Guardar configuracion</button>
      </form>

      <div class="grid gap-4 md:grid-cols-3">
        <article class="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
          <p class="text-sm text-slate-400">Asistencias hoy</p>
          <p class="mt-2 text-3xl font-black text-white">{{ todayAttendance }}</p>
          <p class="mt-1 text-xs text-slate-500">Controladas por vigencia</p>
        </article>
        <article class="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
          <p class="text-sm text-slate-400">Aforo diario</p>
          <p class="mt-2 text-3xl font-black text-emerald-300">{{ todayAttendance }} / {{ settings.capacidad_total }}</p>
          <div class="mt-4 h-2 rounded-full bg-white/10">
            <div class="h-full rounded-full bg-emerald-400" :style="{ width: `${dailyPercent}%` }"></div>
          </div>
        </article>
        <article class="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
          <p class="text-sm text-slate-400">Pico permitido</p>
          <p class="mt-2 text-3xl font-black text-cyan-300">{{ settings.capacidad_por_hora }}</p>
          <p class="mt-1 text-xs text-slate-500">Check-ins por hora</p>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const feedback = ref('');
const feedbackTone = ref('success');
const settings = computed(() => gymStore.gymSettings || { capacidad_total: 30, capacidad_por_hora: 10 });
const today = new Date().toISOString().slice(0, 10);
const todayAttendance = computed(() => gymStore.attendance.filter((entry) => entry.date === today || entry.fecha === today).length);
const dailyPercent = computed(() => Math.min(100, Math.round((todayAttendance.value / Number(settings.value.capacidad_total || 1)) * 100)));
const feedbackClass = computed(() => feedbackTone.value === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50');
const form = reactive({ capacidad_total: 30, capacidad_por_hora: 10 });

watch(settings, (value) => Object.assign(form, value), { immediate: true });

/**
 * Gestiona esta acción de la vista.
 */
const save = async () => {
  try {
    await gymStore.updateGymSettings({ ...form });
    feedbackTone.value = 'success';
    feedback.value = 'Configuracion guardada.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar la configuracion.';
  }
};

onMounted(() => gymStore.fetchFromBackend?.().catch(() => {}));
</script>

<style scoped>
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
</style>
