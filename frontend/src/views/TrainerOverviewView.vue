<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">Trainer</p>
          <h1 class="mt-2 text-3xl font-black text-white">Supervision de horarios</h1>
          <p class="mt-2 text-slate-300">Monitorea matriculas activas, cupos y asistencia reciente sin editar clientes ni horarios.</p>
        </div>
        <button class="rounded-2xl border border-white/10 bg-slate-900/80 px-4 py-3 text-sm font-bold text-white" @click="refresh">
          Actualizar
        </button>
      </div>
    </section>

    <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article v-for="card in cards" :key="card.label" class="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
        <p class="text-sm text-slate-400">{{ card.label }}</p>
        <p class="mt-2 text-3xl font-black text-white">{{ card.value }}</p>
        <p class="mt-2 text-xs uppercase tracking-[0.16em]" :class="card.tone">{{ card.detail }}</p>
      </article>
    </section>

    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Horarios</p>
          <h2 class="mt-2 text-2xl font-black text-white">Clientes matriculados</h2>
        </div>
        <input v-model="search" class="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none" placeholder="Filtrar por cliente, servicio o dia..." />
      </div>

      <div class="mt-5 overflow-hidden rounded-2xl border border-white/10">
        <div class="hidden grid-cols-[1.2fr_0.9fr_1fr_1fr_1fr] gap-4 bg-slate-950/80 px-5 py-3 text-xs uppercase tracking-[0.22em] text-slate-400 md:grid">
          <span>Cliente</span>
          <span>Servicio</span>
          <span>Rutina</span>
          <span>Horario</span>
          <span>Asistencia</span>
        </div>
        <article v-for="item in filteredSchedules" :key="item.id_matricula" class="grid gap-3 border-t border-white/10 bg-slate-900/70 px-5 py-4 md:grid-cols-[1.2fr_0.9fr_1fr_1fr_1fr] md:items-center">
          <div>
            <p class="font-bold text-white">{{ item.cliente_nombre || 'Cliente' }}</p>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">{{ item.cliente_codigo || `Cliente #${item.id_cliente}` }}</p>
          </div>
          <p class="text-sm font-semibold text-cyan-100">{{ serviceLabel(item.servicio) }}</p>
          <div>
            <p class="text-sm font-semibold text-white">{{ item.rutina_nombre || 'Sin rutina' }}</p>
            <p class="text-xs text-slate-500">{{ item.zonas_musculares || 'Rutina pendiente' }}</p>
          </div>
          <p class="text-sm text-slate-300">{{ dayLabel(item.dia) }} {{ item.hora_inicio }} - {{ item.hora_fin }}</p>
          <p class="text-sm text-slate-300">{{ attendanceLabel(item) }}</p>
        </article>
      </div>

      <p v-if="!filteredSchedules.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-8 text-center text-slate-400">
        No hay horarios activos para mostrar.
      </p>

      <p v-if="errorMessage" class="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-50">
        {{ errorMessage }}
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const search = ref('');
const errorMessage = ref('');

const overview = computed(() => gymStore.trainerOverview || {});
const schedules = computed(() => overview.value.schedule_monitor || []);
const stats = computed(() => overview.value.stats || {});

const cards = computed(() => [
  { label: 'Clientes', value: stats.value.clientes_en_horario || 0, detail: 'con horario activo', tone: 'text-emerald-300' },
  { label: 'Matriculas', value: stats.value.matriculas_activas || 0, detail: 'activas', tone: 'text-cyan-300' },
  { label: 'Rutinas', value: stats.value.rutinas || 0, detail: 'catalogadas', tone: 'text-sky-300' },
  { label: 'Asignaciones', value: stats.value.rutinas_asignadas || 0, detail: 'en supervision', tone: 'text-fuchsia-300' },
]);

const filteredSchedules = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return schedules.value;
  return schedules.value.filter((item) =>
    [item.cliente_nombre, item.cliente_codigo, item.servicio, item.rutina_nombre, item.zonas_musculares, item.dia, item.hora_inicio, item.hora_fin]
      .join(' ')
      .toLowerCase()
      .includes(query),
  );
});

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculacion', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';
const dayLabel = (day) => ({ lunes: 'Lunes', martes: 'Martes', miercoles: 'Miercoles', jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sabado', domingo: 'Domingo' })[day] || day || 'Dia';

const attendanceLabel = (item) => {
  const records = Array.isArray(item.asistencias) ? item.asistencias : [];
  if (!records.length) return 'Sin asistencia registrada';
  const last = records[0] || {};
  return `Ultima: ${last.fecha || last.Fecha || 'fecha'} ${last.hora_entrada || last.hora || last.Hora || ''}`.trim();
};

const refresh = async () => {
  try {
    errorMessage.value = '';
    await gymStore.fetchTrainerOverview();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'No se pudo cargar la supervision.';
  }
};

onMounted(refresh);
</script>
