<template>
  <div class="workspace-view membership-plans space-y-6">
    <header class="ws-panel plan-hero">
      <div class="plan-hero-top">
        <div>
          <p class="ws-eyebrow">Administración · Membresías</p>
          <h1 class="ws-title">Planes de membresía</h1>
          <p class="ws-description">Organiza la oferta de tu gimnasio y los planes disponibles para tus clientes.</p>
        </div>
        <button type="button" class="ws-btn ws-primary plan-new" :disabled="loading" @click="newPlan"><Plus :size="18" />Nuevo plan</button>
      </div>
      <div class="plan-summary" role="list" aria-label="Resumen de planes">
        <div role="listitem"><span class="plan-summary-icon"><Layers3 :size="19" /></span><div><span class="ws-muted">En catálogo</span><strong>{{ (loading || loadError) && !plans.length ? '—' : plans.length }}</strong></div></div>
        <div role="listitem"><span class="plan-summary-icon ws-tint-success ws-success"><CircleCheck :size="19" /></span><div><span class="ws-muted">Activos</span><strong>{{ (loading || loadError) && !plans.length ? '—' : activeCount }}</strong></div></div>
        <div role="listitem"><span class="plan-summary-icon"><PauseCircle :size="19" /></span><div><span class="ws-muted">Inactivos</span><strong>{{ (loading || loadError) && !plans.length ? '—' : plans.length - activeCount }}</strong></div></div>
      </div>
    </header>

    <p v-if="feedback" :role="feedbackTone === 'error' ? 'alert' : 'status'" class="ws-notice" :class="feedbackClass">{{ feedback }}</p>
    <div v-if="loadError" role="alert" class="ws-notice app-notice app-notice--error plan-load-error">
      <div><strong>No se pudieron actualizar los planes.</strong><p>{{ loadError }}</p></div>
      <button type="button" class="ws-btn" :disabled="loading" @click="loadPlans"><RefreshCw :size="16" />Reintentar</button>
    </div>

    <section class="plan-catalog" aria-labelledby="plan-catalog-title" :aria-busy="loading">
      <div class="ws-panel plan-catalog-tools">
        <div class="plan-catalog-top">
          <div><h2 id="plan-catalog-title" class="ws-heading">Catálogo de planes</h2><p class="ws-muted plan-result-count" role="status">{{ filteredPlans.length }} de {{ plans.length }} planes</p></div>
          <div class="plan-tools">
            <label class="ws-search plan-search"><span class="sr-only">Buscar planes</span><Search :size="18" /><SearchInput v-model="search" aria-label="Buscar planes" class="ws-input" placeholder="Nombre, duración o descripción" /></label>
            <label class="plan-sort"><span class="sr-only">Ordenar planes</span><select v-model="sort" class="ws-input"><option value="name">Nombre: A–Z</option><option value="price-asc">Menor precio</option><option value="price-desc">Mayor precio</option></select></label>
          </div>
        </div>
        <div class="plan-filters" role="group" aria-label="Filtrar planes por estado">
          <button type="button" class="ws-chip" :aria-pressed="status === 'all'" @click="status = 'all'">Todos <span>{{ plans.length }}</span></button>
          <button type="button" class="ws-chip" :aria-pressed="status === 'active'" @click="status = 'active'">Activos <span>{{ activeCount }}</span></button>
          <button type="button" class="ws-chip" :aria-pressed="status === 'inactive'" @click="status = 'inactive'">Inactivos <span>{{ plans.length - activeCount }}</span></button>
          <button v-if="hasFilters" type="button" class="plan-clear" @click="clearFilters"><X :size="14" />Limpiar filtros</button>
        </div>
      </div>

      <div v-if="loading && !plans.length" class="plan-loading" role="status"><LoaderCircle :size="22" class="ws-spin" />Cargando planes de membresía…</div>
      <div v-else-if="filteredPlans.length" class="plan-grid">
        <article v-for="plan in filteredPlans" :key="plan.id" class="plan-card" :class="{ 'plan-card--inactive': !plan.active }" :aria-labelledby="`plan-title-${plan.id_pm}`">
          <div class="plan-card-top"><span class="plan-card-icon"><CreditCard :size="22" /></span><span class="ws-badge" :class="plan.active ? 'ws-tint-success ws-success' : 'ws-inset ws-muted'"><span class="plan-status-dot" />{{ plan.active ? 'Activo' : 'Inactivo' }}</span></div>
          <div class="plan-card-heading"><h3 :id="`plan-title-${plan.id_pm}`">{{ plan.name }}</h3><span class="plan-duration"><Clock3 :size="15" />{{ plan.duration }}</span></div>
          <div class="plan-price"><span class="ws-muted">Precio del plan</span><p>{{ money(plan.price) }}</p></div>
          <p class="plan-description" :class="plan.description ? 'ws-soft' : 'ws-muted'">{{ plan.description || 'Sin descripción comercial.' }}</p>
          <div class="plan-benefits"><p class="plan-benefits-label">Incluye</p><p v-if="plan.benefits" class="ws-soft"><Check :size="16" /><span>{{ plan.benefits }}</span></p><p v-else class="ws-muted">Beneficios por definir.</p></div>
          <footer class="plan-card-actions"><button type="button" class="ws-btn plan-edit" :disabled="deletingId === plan.id" @click="editPlan(plan)"><Pencil :size="16" />Editar</button><button type="button" class="ws-btn plan-delete" :aria-label="`Eliminar ${plan.name}`" :title="`Eliminar ${plan.name}`" :disabled="Boolean(deletingId)" @click="removePlan(plan)"><LoaderCircle v-if="deletingId === plan.id" :size="17" class="ws-spin" /><Trash2 v-else :size="17" /></button></footer>
        </article>
      </div>
      <div v-else-if="!loadError" class="ws-panel plan-empty">
        <span class="plan-empty-icon"><SearchX v-if="hasFilters" :size="30" /><CreditCard v-else :size="30" /></span>
        <h3>{{ hasFilters ? 'No encontramos planes' : 'Tu catálogo empieza aquí' }}</h3>
        <p class="ws-muted">{{ hasFilters ? 'Prueba otro nombre o cambia el estado seleccionado.' : 'Crea tu primer plan con su precio, duración y beneficios.' }}</p>
        <button v-if="hasFilters" type="button" class="ws-btn" @click="clearFilters">Limpiar filtros</button>
        <button v-else type="button" class="ws-btn ws-primary" @click="newPlan"><Plus :size="17" />Crear primer plan</button>
      </div>
    </section>

    <Teleport to="body">
      <dialog
        ref="editor"
        aria-labelledby="plan-detail-title"
        :aria-busy="saving"
        class="workspace-view plan-dialog w-[calc(100%-2rem)] max-w-xl rounded-2xl border border-white/10 bg-slate-950 p-6 text-white shadow-2xl"
        @cancel.prevent="closeEditor"
        @click="handleBackdrop"
      >
        <form novalidate @submit.prevent="savePlan">
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
              <input
                :maxlength="FORM_LIMITS.shortText" v-model="form.name" autofocus required
                :aria-invalid="Boolean(fieldErrors.name)"
                :aria-describedby="fieldErrors.name ? 'plan-name-error' : undefined"
                @blur="validateField('name')" @input="revalidateField('name')"
                class="field-input" placeholder="Nombre del plan"
              />
              <FieldError id="plan-name-error" :message="fieldErrors.name" />
            </label>
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="block space-y-2">
                <span class="text-sm text-slate-300">Duración</span>
                <select
                  v-model="form.duration" required class="field-input"
                  :aria-invalid="Boolean(fieldErrors.duration)"
                  :aria-describedby="fieldErrors.duration ? 'plan-duration-error' : undefined"
                  @change="revalidateField('duration')" @blur="validateField('duration')"
                >
                  <option disabled value="">Selecciona una duración</option>
                  <option v-for="option in durationOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
                <FieldError id="plan-duration-error" :message="fieldErrors.duration" />
              </label>
              <label class="block space-y-2">
                <span class="text-sm text-slate-300">Precio (S/.)</span>
                <input
                  v-model.number="form.price" type="number" min="0" step="0.01" inputmode="decimal" required
                  :aria-invalid="Boolean(fieldErrors.price)"
                  :aria-describedby="fieldErrors.price ? 'plan-price-error' : undefined"
                  @blur="validateField('price')" @input="revalidateField('price')"
                  class="field-input" placeholder="0.00"
                />
                <FieldError id="plan-price-error" :message="fieldErrors.price" />
              </label>
            </div>
            <label class="block space-y-2">
              <span class="text-sm text-slate-300">Descripción <span class="text-xs text-slate-400">(opcional)</span></span>
              <textarea :maxlength="FORM_LIMITS.longText" v-model="form.description" rows="3" class="field-input" placeholder="Descripción visible para administración y clientes"></textarea>
            </label>
            <label class="block space-y-2">
              <span class="text-sm text-slate-300">Beneficios <span class="text-xs text-slate-400">(opcional)</span></span>
              <textarea :maxlength="FORM_LIMITS.longText" v-model="form.benefits" rows="3" class="field-input" placeholder="Acceso, clases, evaluación, etc."></textarea>
            </label>
            <label class="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-200">
              <input v-model="form.active" type="checkbox" class="h-4 w-4" />
              Disponible para nuevas ventas
            </label>
          </fieldset>
          <div class="mt-5 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button type="button" :disabled="saving" class="rounded-2xl border border-white/10 px-4 py-3 font-bold hover:bg-white/10 disabled:opacity-50" @click="closeEditor">Cancelar</button>
            <button type="submit" :disabled="saving" class="ws-btn ws-primary">{{ saving ? 'Guardando...' : form.id_pm ? 'Guardar cambios' : 'Crear plan' }}</button>
          </div>
        </form>
      </dialog>
    </Teleport>
  </div>
</template>

<script setup>
import { FORM_LIMITS } from "../../domain/utils/formLimits.js";

import { membershipPlanErrors, planDurationOptions } from "../../domain/utils/membershipPlanForm.js";
import { useFormValidation } from "../composables/useFormValidation.js";
import FieldError from "../components/FieldError.vue";
import SearchInput from "../components/SearchInput.vue";
import { usePlanDirectory } from "../composables/memberships/usePlanDirectory.js";
import { Check, CircleCheck, Clock3, CreditCard, Layers3, LoaderCircle, PauseCircle, Pencil, Plus, RefreshCw, Search, SearchX, Trash2, X } from 'lucide-vue-next';
import { feedbackClass as noticeClassFor } from "../utils/feedback.js";
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../../application/stores/gymStore';

const gymStore = useGymStore();
const feedback = ref('');
const feedbackTone = ref('success');
const editor = ref(null);
const editorError = ref('');
const saving = ref(false);
const { plans, search, status, sort, loading, loadError, activeCount, hasFilters, filteredPlans, clearFilters, loadPlans } = usePlanDirectory(gymStore);
const deletingId = ref('');
const money = value => new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(Number(value ?? 0));
const feedbackClass = computed(() => noticeClassFor(feedbackTone.value));
const form = reactive({ id_pm: null, name: '', duration: '30 días', price: '', description: '', benefits: '', active: true });
const registeredDuration = ref('');
const durationOptions = computed(() => planDurationOptions(registeredDuration.value));
const { fieldErrors, validateField, revalidateField, validateForm, resetValidation } = useFormValidation(form, membershipPlanErrors);

/**
 * Gestiona esta acción de la vista.
 */
const reset = () => {
  registeredDuration.value = '';
  Object.assign(form, { id_pm: null, name: '', duration: '30 días', price: '', description: '', benefits: '', active: true });
};
/**
 * Gestiona esta acción de la vista.
 */
const openEditor = () => {
  editorError.value = '';
  feedback.value = '';
  resetValidation();
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
  registeredDuration.value = plan.duration;
  Object.assign(form, { id_pm: plan.id_pm, name: plan.name, duration: plan.duration, price: plan.price, description: plan.description, benefits: plan.benefits, active: plan.active });
  openEditor();
};

/**
 * Gestiona esta acción de la vista.
 */
const savePlan = async () => {
  if (saving.value) return;
  if (!validateForm()) return;
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
  if (deletingId.value) return;
  if (!window.confirm(`Eliminar el plan ${plan.name}?`)) return;
  deletingId.value = plan.id;
  try {
    await gymStore.deletePlan(plan.id);
    feedbackTone.value = 'success';
    feedback.value = 'Plan eliminado.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo eliminar el plan.';
  } finally {
    deletingId.value = '';
  }
};

onMounted(loadPlans);
onBeforeUnmount(() => editor.value?.close());
</script>

<style scoped src="../styles/membership-plans.css"></style>
