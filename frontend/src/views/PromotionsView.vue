<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Ventas</p>
          <h1 class="mt-2 text-3xl font-black text-white">Promociones y descuentos</h1>
          <p class="mt-2 text-slate-300">Administra ofertas por vigencia y por plan para acelerar conversiones.</p>
        </div>
        <button class="rounded-2xl bg-fuchsia-400 px-5 py-3 font-black text-slate-950" @click="reset">Nueva promocion</button>
      </div>
    </section>

    <p v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">{{ feedback }}</p>

    <section class="grid gap-5 xl:grid-cols-[1fr_440px]">
      <div class="grid gap-4 lg:grid-cols-2">
        <article v-for="promo in promotions" :key="promo.id" class="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.25em] text-fuchsia-300">Promo #{{ promo.id_promocion }}</p>
              <h2 class="mt-2 text-xl font-black text-white">{{ promo.name }}</h2>
            </div>
            <span class="rounded-full px-3 py-1 text-xs font-black" :class="promo.active ? 'bg-emerald-400/15 text-emerald-200' : 'bg-slate-700 text-slate-300'">
              {{ promo.active ? 'Activa' : 'Pausada' }}
            </span>
          </div>
          <p class="mt-4 text-3xl font-black text-fuchsia-200">{{ promo.discountType === 'fixed' ? `S/. ${promo.discountValue}` : `${promo.discountValue}%` }}</p>
          <p class="mt-2 text-sm text-slate-300">{{ promo.startsAt || 'desde hoy' }} - {{ promo.validUntil || 'sin fin' }}</p>
          <p class="mt-4 text-sm leading-6 text-slate-400">{{ promo.description || 'Sin descripcion.' }}</p>
          <p class="mt-3 text-xs text-cyan-100">{{ planNames(promo).join(', ') || 'Todos los planes' }}</p>
          <div class="mt-5 flex gap-2">
            <button class="flex-1 rounded-xl border border-white/10 px-3 py-2 font-bold text-white hover:bg-white/10" @click="edit(promo)">Editar</button>
            <button class="rounded-xl border border-rose-400/30 px-3 py-2 font-bold text-rose-100 hover:bg-rose-400/10" @click="remove(promo)">Eliminar</button>
          </div>
        </article>
      </div>

      <form class="h-fit rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="save">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">{{ form.id_promocion ? 'Editar' : 'Crear' }}</p>
        <h2 class="mt-2 text-2xl font-black text-white">Regla comercial</h2>
        <div class="mt-5 space-y-4">
          <input v-model="form.name" class="field-input" placeholder="Nombre de la promocion" />
          <textarea v-model="form.description" rows="3" class="field-input" placeholder="Descripcion interna"></textarea>
          <div class="grid gap-3 sm:grid-cols-2">
            <select v-model="form.discountType" class="field-input">
              <option value="percent">Porcentaje</option>
              <option value="fixed">Monto fijo</option>
            </select>
            <input v-model.number="form.discountValue" type="number" min="0" step="0.01" class="field-input" placeholder="Valor" />
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <input v-model="form.startsAt" type="date" class="field-input" />
            <input v-model="form.validUntil" type="date" class="field-input" />
          </div>
          <div class="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
            <p class="text-xs uppercase tracking-[0.22em] text-slate-400">Planes aplicables</p>
            <label v-for="plan in plans" :key="plan.id" class="mt-3 flex items-center gap-3 text-sm text-slate-200">
              <input v-model="form.appliesTo" type="checkbox" :value="plan.id" />
              {{ plan.name }} - S/. {{ Number(plan.price || 0).toFixed(2) }}
            </label>
          </div>
          <label class="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-200">
            <input v-model="form.active" type="checkbox" class="h-4 w-4" />
            Promocion activa
          </label>
        </div>
        <button class="mt-5 w-full rounded-2xl bg-fuchsia-400 px-4 py-3 font-black text-slate-950">Guardar promocion</button>
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
const promotions = computed(() => gymStore.promotions);
const feedbackClass = computed(() => feedbackTone.value === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50');
const form = reactive({ id_promocion: null, name: '', description: '', discountType: 'percent', discountValue: 10, startsAt: '', validUntil: '', appliesTo: [], active: true });

const reset = () => Object.assign(form, { id_promocion: null, name: '', description: '', discountType: 'percent', discountValue: 10, startsAt: '', validUntil: '', appliesTo: [], active: true });
const planNames = (promo) => promo.appliesTo.map((id) => plans.value.find((plan) => plan.id === id)?.name).filter(Boolean);
const edit = (promo) => Object.assign(form, { id_promocion: promo.id_promocion, name: promo.name, description: promo.description, discountType: promo.discountType, discountValue: promo.discountValue, startsAt: promo.startsAt, validUntil: promo.validUntil, appliesTo: [...promo.appliesTo], active: promo.active });

const save = async () => {
  try {
    await gymStore.upsertPromotion({ ...form });
    feedbackTone.value = 'success';
    feedback.value = 'Promocion guardada.';
    reset();
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar la promocion.';
  }
};

const remove = async (promo) => {
  if (!window.confirm(`Eliminar la promocion ${promo.name}?`)) return;
  try {
    await gymStore.deletePromotion(promo.id);
    feedbackTone.value = 'success';
    feedback.value = 'Promocion eliminada.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo eliminar la promocion.';
  }
};

onMounted(() => gymStore.fetchFromBackend?.().catch(() => {}));
</script>

<style scoped>
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
.field-input::placeholder { color: #64748b; }
</style>
