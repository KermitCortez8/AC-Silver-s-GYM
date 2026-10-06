<template>
  <div class="space-y-6 text-white">
    <!-- Header principal -->
    <section class="rounded-2xl border border-white/10 bg-slate-950 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.35em] text-red-500 font-extrabold flex items-center gap-2">
            <i class="fa-solid fa-clock"></i>
            Supervisión de Horarios
          </p>
          <h1 class="mt-1 text-3xl font-black text-white">Supervisión de Horarios y Asistencias</h1>
          <p class="mt-1 text-sm text-slate-400">Monitorea matrículas activas, cupos y asistencia reciente de los clientes del gimnasio.</p>
        </div>
        <button class="flex items-center gap-2 rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-sm font-bold text-white transition hover:bg-slate-800" @click="refresh">
          <i class="fa-solid fa-rotate-right text-xs"></i>
          <span>Actualizar</span>
        </button>
      </div>
    </section>

    <!-- Tarjetas KPI con Íconos y Alto Contraste -->
    <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article v-for="card in cards" :key="card.label" class="rounded-2xl border border-white/10 bg-slate-950 p-5 backdrop-blur">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wider font-semibold text-slate-400">{{ card.label }}</p>
          <span class="rounded-full bg-red-600/10 p-2.5 text-red-400 border border-red-600/20">
            <i :class="card.icon" class="text-base"></i>
          </span>
        </div>
        <p class="mt-3 text-3xl font-black text-white">{{ card.value }}</p>
        <p class="mt-2 text-xs uppercase tracking-[0.16em] font-extrabold" :class="card.tone">{{ card.detail }}</p>
      </article>
    </section>

    <!-- Sección de Lista de Clientes Matriculados -->
    <section class="rounded-2xl border border-white/10 bg-slate-950 p-6 backdrop-blur space-y-4">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Horarios Registrados</p>
          <h2 class="text-xl font-black text-white">Clientes Matriculados</h2>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Selector de cantidad de filas por página (5, 7, 10) -->
          <div class="flex items-center gap-2 text-xs font-bold text-slate-400">
            <span>Ver:</span>
            <div class="flex items-center gap-1 rounded-xl bg-slate-900 p-1 border border-white/10">
              <button
                v-for="size in [5, 7, 10]"
                :key="size"
                type="button"
                class="px-2.5 py-1 rounded-lg font-black text-xs transition"
                :class="itemsPerPage === size ? 'bg-red-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'"
                @click="setItemsPerPage(size)"
              >
                {{ size }}
              </button>
            </div>
          </div>

          <!-- Buscador -->
          <div class="relative w-full sm:w-64">
            <i class="fa-solid fa-magnifying-glass pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
            <input v-model="search" class="field-input search-input text-xs pr-4 py-2.5" placeholder="Filtrar por cliente, servicio o día..." @input="handleSearchInput" />
          </div>
        </div>
      </div>

      <div class="mt-4 overflow-x-auto rounded-2xl border border-white/10">
        <div class="hidden grid-cols-[1.2fr_0.9fr_1fr_1fr_1fr] gap-4 bg-black/60 px-5 py-3 text-xs uppercase tracking-[0.22em] text-slate-400 font-bold md:grid">
          <span>Cliente</span>
          <span>Servicio</span>
          <span>Rutina</span>
          <span>Horario</span>
          <span>Asistencia</span>
        </div>
        <article v-for="item in paginatedSchedules" :key="item.id_matricula" class="grid gap-3 border-t border-white/5 bg-slate-900/60 px-5 py-4 transition hover:bg-white/[0.03] md:grid-cols-[1.2fr_0.9fr_1fr_1fr_1fr] md:items-center">
          <div>
            <p class="font-bold text-white text-base">{{ item.cliente_nombre || 'Cliente' }}</p>
            <p class="text-xs uppercase tracking-[0.15em] text-slate-400 font-semibold">{{ item.cliente_codigo || `Cliente #${item.id_cliente}` }}</p>
          </div>
          <div>
            <span class="inline-block rounded-full border border-red-600/30 bg-red-600/10 px-3 py-1 text-xs font-bold text-red-400">
              {{ serviceLabel(item.servicio) }}
            </span>
          </div>
          <div>
            <p class="text-sm font-bold text-white">{{ item.rutina_nombre || 'Sin rutina' }}</p>
            <p class="text-xs text-slate-400">{{ item.zonas_musculares || 'Rutina pendiente' }}</p>
          </div>
          <p class="text-sm font-medium text-slate-300">{{ dayLabel(item.dia) }} {{ item.hora_inicio }} - {{ item.hora_fin }}</p>
          <p class="text-sm font-semibold text-slate-300 flex items-center gap-1.5">
            <i class="fa-solid fa-clock-rotate-left text-xs text-slate-400"></i>
            <span>{{ attendanceLabel(item) }}</span>
          </p>
        </article>
      </div>

      <p v-if="!filteredSchedules.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-8 text-center text-slate-400">
        No hay horarios activos que coincidan con la búsqueda.
      </p>

      <!-- Paginación Inferior de la Tabla -->
      <div v-if="filteredSchedules.length > 0" class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-t border-white/10 pt-4 text-xs font-bold text-slate-400">
        <p>
          Mostrando <span class="text-white font-black">{{ showingStart }}</span> a <span class="text-white font-black">{{ showingEnd }}</span> de <span class="text-white font-black">{{ filteredSchedules.length }}</span> matriculados
        </p>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded-xl border border-white/10 bg-slate-900 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1.5"
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            <i class="fa-solid fa-chevron-left text-[10px]"></i>
            <span>Anterior</span>
          </button>

          <div class="flex items-center gap-1">
            <button
              v-for="page in totalPages"
              :key="page"
              type="button"
              class="h-7 w-7 rounded-lg text-xs font-black transition flex items-center justify-center"
              :class="currentPage === page ? 'bg-red-600 text-white shadow-sm shadow-red-600/30' : 'bg-slate-900 text-slate-400 border border-white/10 hover:bg-slate-800 hover:text-white'"
              @click="currentPage = page"
            >
              {{ page }}
            </button>
          </div>

          <button
            type="button"
            class="rounded-xl border border-white/10 bg-slate-900 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1.5"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            <span>Siguiente</span>
            <i class="fa-solid fa-chevron-right text-[10px]"></i>
          </button>
        </div>
      </div>

      <p v-if="errorMessage" class="mt-4 rounded-2xl border border-rose-500/40 bg-rose-950/60 px-4 py-3 text-sm font-bold text-rose-300">
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

const currentPage = ref(1);
const itemsPerPage = ref(5);

const setItemsPerPage = (size) => {
  itemsPerPage.value = size;
  currentPage.value = 1;
};

const handleSearchInput = () => {
  currentPage.value = 1;
};

const overview = computed(() => gymStore.trainerOverview || {});
const schedules = computed(() => overview.value.schedule_monitor || []);
const stats = computed(() => overview.value.stats || {});

const cards = computed(() => [
  { label: 'Clientes', value: stats.value.clientes_en_horario || 0, detail: 'con horario activo', tone: 'text-emerald-500 dark:text-emerald-400', icon: 'fa-solid fa-users' },
  { label: 'Matriculas', value: stats.value.matriculas_activas || 0, detail: 'activas', tone: 'text-red-500 dark:text-red-400', icon: 'fa-solid fa-id-card' },
  { label: 'Rutinas', value: stats.value.rutinas || 0, detail: 'catalogadas', tone: 'text-red-500 dark:text-red-400', icon: 'fa-solid fa-dumbbell' },
  { label: 'Asignaciones', value: stats.value.rutinas_asignadas || 0, detail: 'en supervision', tone: 'text-red-500 dark:text-red-400', icon: 'fa-solid fa-layer-group' },
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

const totalPages = computed(() => Math.ceil(filteredSchedules.value.length / itemsPerPage.value) || 1);

const paginatedSchedules = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value;
  return filteredSchedules.value.slice(start, start + itemsPerPage.value);
});

const showingStart = computed(() => (filteredSchedules.value.length === 0 ? 0 : (currentPage.value - 1) * itemsPerPage.value + 1));
const showingEnd = computed(() => Math.min(currentPage.value * itemsPerPage.value, filteredSchedules.value.length));

const serviceLabel = (service) => ({ fitness: 'Fitness', musculacion: 'Musculación', cardio: 'Cardio', baile: 'Baile' })[service] || service || 'Servicio';
const dayLabel = (day) => ({ lunes: 'Lunes', martes: 'Martes', miercoles: 'Miércoles', jueves: 'Jueves', viernes: 'Viernes', sabado: 'Sábado', domingo: 'Domingo' })[day] || day || 'Día';

const attendanceLabel = (item) => {
  const records = Array.isArray(item.asistencias) ? item.asistencias : [];
  if (!records.length) return 'Sin asistencia registrada';
  const last = records[0] || {};
  return `Última: ${last.fecha || last.Fecha || 'fecha'} ${last.hora_entrada || last.hora || last.Hora || ''}`.trim();
};

const refresh = async () => {
  try {
    errorMessage.value = '';
    await gymStore.fetchTrainerOverview();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'No se pudo cargar la supervisión.';
  }
};

onMounted(refresh);
</script>

<style scoped>
.field-input {
  width: 100%;
  border: 1px solid var(--app-border, rgba(255, 255, 255, 0.1));
  border-radius: 1rem;
  background: var(--app-input, rgba(2, 6, 23, 0.9));
  padding: 0.75rem 1rem;
  color: var(--app-text, white);
  outline: none;
}

[data-theme="light"] .field-input {
  background-color: #ffffff !important;
  color: #0f172a !important;
  border-color: #cbd5e1 !important;
}

.search-input {
  padding-left: 2.75rem !important;
}
</style>
