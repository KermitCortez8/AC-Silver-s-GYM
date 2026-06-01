<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Agenda</p>
      <h1 class="mt-2 text-3xl font-black text-white">Horarios y rutinas</h1>
      <p class="mt-2 max-w-3xl text-slate-300">Consulta la programación semanal, crea rutinas y asigna horarios personalizados a cada cliente.</p>
    </section>

    <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article v-for="slot in schedule" :key="slot.day" class="rounded-[1.75rem] border border-white/10 bg-slate-950/70 p-5">
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-cyan-300/80">{{ slot.day }}</p>
        <p class="mt-3 text-lg font-bold text-white">{{ slot.hours }}</p>
        <p class="mt-2 text-sm text-slate-300">{{ slot.focus }}</p>
      </article>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Rutina asignada</p>
        <h2 class="mt-2 text-2xl font-black text-white">{{ member ? member.name : 'Selecciona un cliente' }}</h2>

        <form v-if="member" class="mt-5 space-y-4" @submit.prevent="handleScheduleSubmit">
          <div class="grid gap-4 sm:grid-cols-2">
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Día</span>
              <select v-model="routineForm.dia_semana" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
                <option v-for="day in days" :key="day">{{ day }}</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Rutina</span>
              <select v-model.number="routineForm.id_rutina" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
                <option v-for="routine in routines" :key="routine.id_rutina" :value="routine.id_rutina">{{ routine.nombre_rutina }}</option>
              </select>
            </label>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Inicio</span>
              <input v-model="routineForm.hora_inicio" type="time" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Fin</span>
              <input v-model="routineForm.hora_fin" type="time" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
            </label>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Rutina nueva</span>
              <input v-model="routineDraft.nombre_rutina" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Fuerza inicial" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Zonas musculares</span>
              <input v-model="routineDraft.zonas_musculares" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Piernas, core" />
            </label>
          </div>

          <button type="button" class="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 font-semibold text-white transition hover:bg-white/10" @click="createRoutine">
            Crear rutina
          </button>

          <button type="submit" class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
            Asignar horario
          </button>
        </form>

        <div v-else class="mt-4 rounded-[1.75rem] border border-amber-400/20 bg-amber-400/10 p-4 text-amber-100">
          Selecciona un cliente en la vista de usuarios para asignarle horarios personalizados.
        </div>
      </div>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-[0.65rem] uppercase tracking-[0.5em] text-slate-400">Horario por cliente</p>
            <h2 class="mt-2 text-2xl font-black text-white">Asignaciones activas</h2>
          </div>
          <div class="rounded-2xl bg-slate-950/70 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Rutinas</p>
            <p class="text-xl font-black text-white">{{ routines.length }}</p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="slot in memberSchedules" :key="slot.id_horario" class="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-4">
            <p class="font-semibold text-white">{{ slot.dia_semana }} · {{ slot.hora_inicio }} - {{ slot.hora_fin }}</p>
            <p class="text-sm text-slate-400">Rutina #{{ slot.id_rutina }}</p>
          </article>
          <p v-if="!memberSchedules.length" class="text-sm text-slate-400">Aún no hay horarios asignados para este cliente.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';

const { user } = useAuth();
const gymStore = useGymStore();
const schedule = computed(() => Array.isArray(gymStore.schedule) ? gymStore.schedule : []);
const routines = computed(() => Array.isArray(gymStore.routines) ? gymStore.routines : []);
const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const member = computed(() => gymStore.memberByEmail(user.value?.email));
const memberSchedules = computed(() => (member.value ? gymStore.memberSchedules(member.value.id) : []));

const routineForm = reactive({
  dia_semana: 'Lunes',
  hora_inicio: '06:00',
  hora_fin: '07:00',
  id_rutina: 1,
});

const routineDraft = reactive({
  nombre_rutina: '',
  zonas_musculares: '',
  color: 'Azul',
});

const createRoutine = async () => {
  if (!routineDraft.nombre_rutina.trim()) {
    return;
  }

  await gymStore.upsertRutina(routineDraft);
  routineDraft.nombre_rutina = '';
  routineDraft.zonas_musculares = '';
};

const handleScheduleSubmit = async () => {
  if (!member.value) {
    return;
  }

  await gymStore.upsertHorario({
    id_cliente: member.value.id_cliente,
    id_rutina: routineForm.id_rutina,
    dia_semana: routineForm.dia_semana,
    hora_inicio: routineForm.hora_inicio,
    hora_fin: routineForm.hora_fin,
  });
};
</script>
