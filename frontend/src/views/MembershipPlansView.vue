<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Membresias</p>
          <h1 class="mt-2 text-3xl font-black text-white">Planes de membresia</h1>
          <p class="mt-2 text-slate-300">Configura precios, vigencia, beneficios y disponibilidad comercial.</p>
        </div>
        <button class="rounded-2xl bg-cyan-400 px-5 py-3 font-black text-slate-950" @click="newPlan">Nuevo plan</button>
      </div>
    </section>

    <p v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">{{ feedback }}</p>

    <section class="grid gap-5 lg:grid-cols-[1fr_420px]">
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <article v-for="plan in plans" :key="plan.id" class="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.25em] text-cyan-300">Plan #{{ plan.id_pm }}</p>
              <h2 class="mt-2 text-2xl font-black text-white">{{ plan.name }}</h2>
            </div>
            <span class="rounded-full px-3 py-1 text-xs font-black" :class="plan.active ? 'bg-emerald-400/15 text-emerald-200' : 'bg-slate-700 text-slate-300'">
              {{ plan.active ? 'Activo' : 'Inactivo' }}
            </span>
          </div>
          <p class="mt-4 text-3xl font-black text-emerald-300">S/. {{ Number(plan.price || 0).toFixed(2) }}</p>
          <p class="mt-2 text-sm text-slate-300">{{ plan.duration }}</p>
          <p class="mt-4 min-h-12 text-sm leading-6 text-slate-400">{{ plan.description || 'Sin descripcion comercial.' }}</p>
          <p class="mt-3 text-xs text-cyan-100">{{ plan.benefits || 'Beneficios por definir.' }}</p>
          <div class="mt-5 flex gap-2">
            <button class="flex-1 rounded-xl border border-white/10 px-3 py-2 font-bold text-white hover:bg-white/10" @click="editPlan(plan)">Editar</button>
            <button class="rounded-xl border border-rose-400/30 px-3 py-2 font-bold text-rose-100 hover:bg-rose-400/10" @click="removePlan(plan)">Eliminar</button>
          </div>
        </article>
      </div>

      <form class="h-fit rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="savePlan">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">{{ form.id_pm ? 'Editar' : 'Crear' }}</p>
        <h2 class="mt-2 text-2xl font-black text-white">Detalle del plan</h2>
        <div class="mt-5 space-y-4">
          <input v-model="form.name" class="field-input" placeholder="Nombre del plan" />
          <input v-model="form.duration" class="field-input" placeholder="Duracion: 30 dias, 90 dias..." />
          <input v-model.number="form.price" type="number" min="0" step="0.01" class="field-input" placeholder="Precio" />
          <textarea v-model="form.description" rows="3" class="field-input" placeholder="Descripcion visible para administracion y clientes"></textarea>
          <textarea v-model="form.benefits" rows="3" class="field-input" placeholder="Beneficios: acceso, clases, evaluacion, etc."></textarea>
          <label class="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-200">
            <input v-model="form.active" type="checkbox" class="h-4 w-4" />
            Disponible para nuevas ventas
          </label>
        </div>
        <button class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-black text-slate-950">{{ form.id_pm ? 'Guardar cambios' : 'Crear plan' }}</button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const feedback = ref('');
const feedbackTone = ref('success');
const plans = computed(() => gymStore.planCatalog);
const feedbackClass = computed(() => feedbackTone.value === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50');
const form = reactive({ id_pm: null, name: '', duration: '30 dias', price: 0, description: '', benefits: '', active: true });

const reset = () => Object.assign(form, { id_pm: null, name: '', duration: '30 dias', price: 0, description: '', benefits: '', active: true });
const newPlan = () => reset();
const editPlan = (plan) => Object.assign(form, { id_pm: plan.id_pm, name: plan.name, duration: plan.duration, price: plan.price, description: plan.description, benefits: plan.benefits, active: plan.active });

const savePlan = async () => {
  try {
    await gymStore.upsertPlan({ ...form });
    feedbackTone.value = 'success';
    feedback.value = 'Plan guardado correctamente.';
    reset();
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar el plan.';
  }
};

const removePlan = async (plan) => {
  if (!window.confirm(`Eliminar el plan ${plan.name}?`)) return;
  try {
    await gymStore.deletePlan(plan.id);
    feedbackTone.value = 'success';
    feedback.value = 'Plan eliminado.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo eliminar el plan.';
  }
};

onMounted(() => gymStore.fetchFromBackend?.().catch(() => {}));
</script>

<style scoped>
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
.field-input::placeholder { color: #64748b; }
</style>
