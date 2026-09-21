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

    <section>
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
    </section>

    <Teleport to="body">
      <dialog
        ref="editor"
        aria-labelledby="plan-detail-title"
        :aria-busy="saving"
        class="plan-dialog w-[calc(100%-2rem)] max-w-xl rounded-2xl border border-white/10 bg-slate-950 p-6 text-white shadow-2xl"
        @cancel.prevent="closeEditor"
        @click="handleBackdrop"
      >
        <form @submit.prevent="savePlan">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">{{ form.id_pm ? 'Editar' : 'Crear' }}</p>
              <h2 id="plan-detail-title" class="mt-2 text-2xl font-black text-white">Detalle del plan</h2>
            </div>
            <button type="button" :disabled="saving" class="rounded-xl border border-white/10 px-3 py-2 font-bold hover:bg-white/10 disabled:opacity-50" @click="closeEditor">Cerrar</button>
          </div>
          <p v-if="editorError" role="alert" class="mt-4 rounded-xl border border-rose-400/20 bg-rose-400/10 p-3 text-sm text-rose-50">{{ editorError }}</p>
          <fieldset :disabled="saving" class="mt-5 space-y-4">
            <label class="block space-y-2">
              <span class="text-sm text-slate-300">Nombre del plan</span>
              <input v-model="form.name" autofocus class="field-input" placeholder="Nombre del plan" />
            </label>
            <label class="block space-y-2">
              <span class="text-sm text-slate-300">Duración</span>
              <input v-model="form.duration" class="field-input" placeholder="30 días, 90 días..." />
            </label>
            <label class="block space-y-2">
              <span class="text-sm text-slate-300">Precio (S/.)</span>
              <input v-model.number="form.price" type="number" min="0" step="0.01" class="field-input" placeholder="Precio" />
            </label>
            <label class="block space-y-2">
              <span class="text-sm text-slate-300">Descripción</span>
              <textarea v-model="form.description" rows="3" class="field-input" placeholder="Descripción visible para administración y clientes"></textarea>
            </label>
            <label class="block space-y-2">
              <span class="text-sm text-slate-300">Beneficios</span>
              <textarea v-model="form.benefits" rows="3" class="field-input" placeholder="Acceso, clases, evaluación, etc."></textarea>
            </label>
            <label class="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-200">
              <input v-model="form.active" type="checkbox" class="h-4 w-4" />
              Disponible para nuevas ventas
            </label>
          </fieldset>
          <div class="mt-5 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button type="button" :disabled="saving" class="rounded-2xl border border-white/10 px-4 py-3 font-bold hover:bg-white/10 disabled:opacity-50" @click="closeEditor">Cancelar</button>
            <button type="submit" :disabled="saving" class="rounded-2xl bg-cyan-400 px-4 py-3 font-black text-slate-950 disabled:opacity-50">{{ saving ? 'Guardando...' : form.id_pm ? 'Guardar cambios' : 'Crear plan' }}</button>
          </div>
        </form>
      </dialog>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';

const gymStore = useGymStore();
const feedback = ref('');
const feedbackTone = ref('success');
const editor = ref(null);
const editorError = ref('');
const saving = ref(false);
const plans = computed(() => gymStore.planCatalog);
const feedbackClass = computed(() => feedbackTone.value === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50');
const form = reactive({ id_pm: null, name: '', duration: '30 dias', price: 0, description: '', benefits: '', active: true });

/**
 * Gestiona esta acción de la vista.
 */
const reset = () => Object.assign(form, { id_pm: null, name: '', duration: '30 dias', price: 0, description: '', benefits: '', active: true });
/**
 * Gestiona esta acción de la vista.
 */
const openEditor = () => {
  editorError.value = '';
  feedback.value = '';
  editor.value.showModal();
};
const closeEditor = () => {
  if (!saving.value) editor.value?.close();
};
const handleBackdrop = (event) => {
  if (event.target !== editor.value) return;
  const bounds = editor.value.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) closeEditor();
};
const newPlan = () => {
  reset();
  openEditor();
};
/**
 * Gestiona esta acción de la vista.
 */
const editPlan = (plan) => {
  Object.assign(form, { id_pm: plan.id_pm, name: plan.name, duration: plan.duration, price: plan.price, description: plan.description, benefits: plan.benefits, active: plan.active });
  openEditor();
};

/**
 * Gestiona esta acción de la vista.
 */
const savePlan = async () => {
  if (saving.value) return;
  saving.value = true;
  editorError.value = '';
  try {
    await gymStore.upsertPlan({ ...form });
    feedbackTone.value = 'success';
    feedback.value = 'Plan guardado correctamente.';
    editor.value?.close();
    reset();
  } catch (error) {
    editorError.value = error instanceof Error ? error.message : 'No se pudo guardar el plan.';
  } finally {
    saving.value = false;
  }
};

/**
 * Elimina el registro indicado.
 */
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
onBeforeUnmount(() => editor.value?.close());
</script>

<style scoped>
.plan-dialog { margin: auto; max-height: 90dvh; overflow-y: auto; }
.plan-dialog::backdrop { background: rgb(2 6 23 / 75%); backdrop-filter: blur(4px); }
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
.field-input:focus-visible { border-color: #22d3ee; outline: 2px solid #22d3ee; outline-offset: 2px; }
.field-input::placeholder { color: #64748b; }
</style>
