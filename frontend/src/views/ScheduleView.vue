<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Agenda</p>
      <h1 class="mt-2 text-3xl font-black text-white">Horarios</h1>
      <p class="mt-2 text-slate-300">Vista pública de clases, apertura y cierre del gimnasio, más rutinas personales asignadas al socio.</p>
    </section>

    <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article v-for="slot in schedule" :key="slot.day" class="rounded-3xl border border-white/10 bg-slate-900/80 p-5">
        <p class="text-sm uppercase tracking-[0.35em] text-cyan-300/80">{{ slot.day }}</p>
        <p class="mt-3 text-lg font-bold text-white">{{ slot.hours }}</p>
        <p class="mt-2 text-sm text-slate-300">{{ slot.focus }}</p>
      </article>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Rutina asignada</p>
        <h2 class="mt-2 text-2xl font-black text-white">{{ member ? member.name : 'Sin socio identificado' }}</h2>

        <form v-if="member" class="mt-5 space-y-4" @submit.prevent="handleRoutineSubmit">
          <div class="grid gap-4 sm:grid-cols-3">
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Día</span>
              <select v-model="routineForm.day" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
                <option>Lunes</option>
                <option>Martes</option>
                <option>Miércoles</option>
                <option>Jueves</option>
                <option>Viernes</option>
                <option>Sábado</option>
                <option>Domingo</option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Inicio</span>
              <input v-model="routineForm.startTime" type="time" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Fin</span>
              <input v-model="routineForm.endTime" type="time" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
            </label>
          </div>

          <label class="space-y-2 block">
            <span class="text-sm text-slate-300">Observación</span>
            <input v-model="routineForm.note" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Ej. rutina de pierna o cardio" />
          </label>

          <button type="submit" class="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
            Asignar horario
          </button>
        </form>

        <div v-else class="mt-4 rounded-3xl border border-amber-400/20 bg-amber-400/10 p-4 text-amber-100">
          Inicia sesión con un socio registrado para asignar una rutina personal.
        </div>
      </div>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Rutinas del socio</p>
        <div class="mt-4 space-y-3">
          <article v-for="routine in memberSchedules" :key="routine.id" class="rounded-3xl border border-white/10 bg-slate-900/80 p-4">
            <p class="font-semibold text-white">{{ routine.day }} · {{ routine.startTime }} - {{ routine.endTime }}</p>
            <p class="text-sm text-slate-400">{{ routine.note || 'Sin observación' }}</p>
          </article>
          <p v-if="!memberSchedules.length" class="text-sm text-slate-400">Aún no hay horarios asignados para este socio.</p>
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
const schedule = computed(() => gymStore.schedule);
const member = computed(() => gymStore.memberByEmail(user.value?.email));
const memberSchedules = computed(() => (member.value ? gymStore.memberSchedules(member.value.id) : []));

const routineForm = reactive({
  day: 'Lunes',
  startTime: '06:00',
  endTime: '07:00',
  note: '',
});

const handleRoutineSubmit = () => {
  if (!member.value) return;

  gymStore.assignMemberSchedule(member.value.id, routineForm);
  routineForm.note = '';
};
</script>
