<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Ventas</p>
          <h1 class="mt-2 text-3xl font-black text-white">Promociones y descuentos</h1>
          <p class="mt-2 text-slate-300">Administra ofertas por vigencia y por plan para acelerar conversiones.</p>
        </div>
        <button class="flex items-center gap-2 rounded-2xl bg-rose-500 px-5 py-3 font-black text-white transition hover:bg-rose-400 shadow-lg shadow-rose-500/20" @click="openNewModal">
          <i class="fa-solid fa-plus"></i> Nueva promoción
        </button>
      </div>
    </section>

    <p v-if="feedback" class="rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">{{ feedback }}</p>

    <!-- KPIs Section -->
    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-5 relative overflow-hidden">
        <div class="flex justify-between items-start">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400 w-3/4">Promociones Activas</p>
          <i class="fa-solid fa-check text-emerald-400 bg-emerald-400/10 p-2 rounded-full text-xs"></i>
        </div>
        <p class="mt-4 text-4xl font-black text-white">{{ activePromotionsCount }}</p>
        <p class="mt-2 text-xs text-emerald-400">Reglas comerciales vigentes</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-5 relative overflow-hidden">
        <div class="flex justify-between items-start">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400 w-3/4">Descuentos Aplicados</p>
          <i class="fa-solid fa-dollar-sign text-purple-400 bg-purple-400/10 p-2 rounded-full text-xs px-3"></i>
        </div>
        <p class="mt-4 text-4xl font-black text-white">S/. {{ totalAhorrado.toFixed(2) }}</p>
        <p class="mt-2 text-xs text-slate-400">Ahorrados a clientes este mes</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-5 relative overflow-hidden">
        <div class="flex justify-between items-start">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400 w-3/4">Conversión en Caja</p>
          <i class="fa-solid fa-arrow-trend-up text-rose-400 bg-rose-400/10 p-2 rounded-full text-xs"></i>
        </div>
        <p class="mt-4 text-4xl font-black text-white">{{ porcentajeVentasConPromo.toFixed(1) }}%</p>
        <p class="mt-2 text-xs text-slate-400">Ventas con cupón o promo</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-slate-950/70 p-5 relative overflow-hidden">
        <div class="flex justify-between items-start">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400 w-3/4">Ticket Promedio</p>
          <i class="fa-solid fa-lock text-cyan-400 bg-cyan-400/10 p-2 rounded-full text-xs"></i>
        </div>
        <p class="mt-4 text-4xl font-black text-white">S/. {{ ticketMedioConDescuento.toFixed(2) }}</p>
        <p class="mt-2 text-xs text-slate-400">Ticket medio con descuento</p>
      </div>
    </section>

    <!-- Chart Section -->
    <section class="rounded-2xl border border-white/10 bg-slate-950/70 p-6">
      <h2 class="text-lg font-bold text-white mb-4">Impacto en Caja Semanal</h2>
      <div class="h-64 w-full">
        <Bar :data="chartData" :options="chartOptions" />
      </div>
    </section>

    <!-- Promotions Table Section -->
    <section class="rounded-2xl border border-white/10 bg-slate-950/70 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm text-slate-300">
          <thead class="border-b border-white/10 bg-white/5 text-xs uppercase tracking-wider text-slate-400">
            <tr>
              <th class="px-6 py-4 font-semibold">ID</th>
              <th class="px-6 py-4 font-semibold">Nombre</th>
              <th class="px-6 py-4 font-semibold">Descuento</th>
              <th class="px-6 py-4 font-semibold">Vigencia</th>
              <th class="px-6 py-4 font-semibold">Planes aplicables</th>
              <th class="px-6 py-4 font-semibold text-center">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr v-for="promo in promotions" :key="promo.id" class="transition hover:bg-white/5">
              <td class="px-6 py-4">
                <span class="rounded-full bg-fuchsia-400/10 px-2.5 py-1 text-xs font-bold text-fuchsia-300">
                  #{{ promo.id_promocion }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <span class="font-bold text-white">{{ promo.name }}</span>
                  <i v-if="promo.active" class="fa-solid fa-circle-check text-emerald-400" title="Activa"></i>
                  <i v-else class="fa-solid fa-circle-pause text-slate-500" title="Pausada"></i>
                </div>
              </td>
              <td class="px-6 py-4 font-bold text-emerald-300">
                {{ promo.discountType === 'fixed' ? `S/. ${promo.discountValue}` : `${promo.discountValue}%` }}
              </td>
              <td class="px-6 py-4 text-slate-400">
                {{ promo.startsAt || 'Desde hoy' }} - {{ promo.validUntil || 'Sin fin' }}
              </td>
              <td class="px-6 py-4 text-cyan-100 text-xs">
                {{ planNames(promo).join(', ') || 'Todos los planes' }}
              </td>
              <td class="px-6 py-4 text-center">
                <div class="flex items-center justify-center gap-3">
                  <button class="text-slate-400 hover:text-white transition" @click="editModal(promo)" title="Editar">
                    <i class="fa-solid fa-pen"></i>
                  </button>
                  <button class="text-rose-400/70 hover:text-rose-400 transition" @click="remove(promo)" title="Eliminar">
                    <i class="fa-solid fa-trash-can"></i>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="promotions.length === 0">
              <td colspan="6" class="px-6 py-8 text-center text-slate-500">
                No hay reglas comerciales configuradas.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Modal Form -->
    <Teleport to="body">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm transition-opacity">
        <form class="w-full max-w-5xl rounded-3xl border border-white/10 bg-[#0f111a] p-0 shadow-2xl overflow-y-auto max-h-[90vh]" @submit.prevent="save">
          <!-- Top gradient border -->
          <div class="h-1 w-full bg-gradient-to-r from-rose-500 via-purple-500 to-indigo-500 rounded-t-3xl"></div>
          
          <div class="p-8">
            <div class="flex justify-between items-center mb-8">
              <div class="flex items-center gap-4">
                <div class="h-12 w-12 rounded-2xl bg-rose-500/10 flex items-center justify-center text-rose-400">
                  <i class="fa-solid fa-tag"></i>
                </div>
                <div>
                  <p class="text-xs uppercase tracking-widest text-slate-400 font-bold">{{ form.id_promocion ? 'EDITAR' : 'CREAR' }}</p>
                  <h2 class="mt-1 text-2xl font-black text-white">Regla comercial</h2>
                </div>
              </div>
              <button type="button" class="text-slate-400 hover:text-white text-xl transition" @click="closeModal">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
              <!-- Left Column -->
              <div class="space-y-6">
                <div>
                  <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2"><i class="fa-solid fa-wand-magic-sparkles text-rose-400"></i> NOMBRE DE LA PROMOCIÓN</label>
                  <input v-model="form.name" class="w-full rounded-xl border border-white/5 bg-[#161925] px-4 py-3 text-white placeholder-slate-500 focus:border-rose-400 focus:outline-none focus:ring-1 focus:ring-rose-400 transition" placeholder="Ej. Promo Verano" />
                </div>
                
                <div>
                  <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2"><i class="fa-regular fa-file-lines text-slate-400"></i> DESCRIPCIÓN INTERNA <span class="text-slate-500 lowercase normal-case">(opcional)</span></label>
                  <textarea v-model="form.description" rows="2" class="w-full rounded-xl border border-white/5 bg-[#161925] px-4 py-3 text-white placeholder-slate-500 focus:border-rose-400 focus:outline-none focus:ring-1 focus:ring-rose-400 transition" placeholder="Detalle o notas internas del descuento..."></textarea>
                </div>
                
                <div class="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2"><i class="fa-solid fa-chart-pie text-slate-400"></i> TIPO</label>
                    <select v-model="form.discountType" class="w-full rounded-xl border border-white/5 bg-[#161925] px-4 py-3 text-white focus:border-rose-400 focus:outline-none focus:ring-1 focus:ring-rose-400 transition">
                      <option value="percent">Porcentaje (%)</option>
                      <option value="fixed">Monto fijo (S/.)</option>
                    </select>
                  </div>
                  <div>
                    <label class="flex items-center gap-2 text-xs font-bold text-rose-400 uppercase tracking-widest mb-2"><i class="fa-regular fa-square-check"></i> VALOR</label>
                    <div class="relative">
                      <input v-model.number="form.discountValue" type="number" min="0" step="0.01" class="w-full rounded-xl border border-white/5 bg-[#161925] px-4 py-3 text-white focus:border-rose-400 focus:outline-none focus:ring-1 focus:ring-rose-400 transition pr-10" placeholder="0.00" />
                      <span class="absolute right-4 top-3.5 text-slate-400 font-bold text-sm">{{ form.discountType === 'percent' ? '%' : 'S/.' }}</span>
                    </div>
                  </div>
                </div>
                
                <div class="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2"><i class="fa-regular fa-calendar text-slate-400"></i> INICIO <span class="text-slate-500 lowercase normal-case">(opcional)</span></label>
                    <input v-model="form.startsAt" type="date" class="w-full rounded-xl border border-white/5 bg-[#161925] px-4 py-3 text-white focus:border-rose-400 focus:outline-none focus:ring-1 focus:ring-rose-400 transition" />
                  </div>
                  <div>
                    <label class="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-widest mb-2"><i class="fa-regular fa-calendar text-slate-400"></i> FIN <span class="text-slate-500 lowercase normal-case">(opcional)</span></label>
                    <input v-model="form.validUntil" type="date" class="w-full rounded-xl border border-white/5 bg-[#161925] px-4 py-3 text-white focus:border-rose-400 focus:outline-none focus:ring-1 focus:ring-rose-400 transition" />
                  </div>
                </div>
              </div>
              
              <!-- Right Column -->
              <div class="space-y-6">
                <div class="rounded-3xl border border-white/5 bg-[#161925]/50 p-6">
                  <div class="flex items-center justify-between mb-4">
                    <label class="flex items-center gap-2 text-xs font-bold text-rose-400 uppercase tracking-widest"><i class="fa-regular fa-credit-card"></i> PLANES APLICABLES</label>
                    <span class="text-xs text-slate-500">Selecciona al menos uno</span>
                  </div>
                  <div class="grid grid-cols-2 gap-3">
                    <label v-for="plan in plans" :key="plan.id" :class="form.appliesTo.includes(plan.id) ? 'border-rose-500 bg-rose-500/5' : 'border-white/5 hover:bg-white/5'" class="relative flex cursor-pointer flex-col justify-between rounded-2xl border p-4 transition-colors">
                      <div class="flex justify-between items-start">
                        <div class="flex items-center gap-2">
                          <input type="checkbox" v-model="form.appliesTo" :value="plan.id" class="text-rose-500 focus:ring-rose-500 bg-slate-800 border-white/10 rounded" />
                          <span class="text-sm font-black text-white uppercase">{{ plan.name }}</span>
                        </div>
                        <div v-if="form.appliesTo.includes(plan.id)" class="bg-rose-500/20 text-rose-400 text-xs font-black px-2 py-1 rounded-lg">S/. {{ Number(plan.price || 0).toFixed(2) }}</div>
                        <div v-else class="text-slate-300 text-xs font-black px-2 py-1">S/. {{ Number(plan.price || 0).toFixed(2) }}</div>
                      </div>
                      <p class="mt-2 text-xs text-slate-400 ml-6">{{ plan.duration_days || 30 }} días de acceso</p>
                    </label>
                  </div>
                </div>
                
                <label class="flex items-center justify-between rounded-3xl border border-white/5 bg-[#161925]/50 p-6 cursor-pointer hover:bg-white/5 transition-colors">
                  <div class="flex items-center gap-4">
                    <div class="h-2 w-2 rounded-full" :class="form.active ? 'bg-emerald-400' : 'bg-slate-500'"></div>
                    <div>
                      <p class="text-sm font-bold text-white">Promoción activa</p>
                      <p class="text-xs text-slate-400 mt-1">Estará disponible de inmediato tras guardar</p>
                    </div>
                  </div>
                  <div class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors" :class="form.active ? 'bg-rose-500' : 'bg-slate-600'">
                    <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" :class="form.active ? 'translate-x-6' : 'translate-x-1'"></span>
                    <input v-model="form.active" type="checkbox" class="sr-only" />
                  </div>
                </label>
              </div>
            </div>
            
            <!-- Actions -->
            <div class="mt-10 flex justify-end items-center gap-6">
              <button type="button" class="text-sm font-bold text-slate-300 hover:text-white transition" @click="closeModal">Cancelar</button>
              <button type="submit" class="flex items-center gap-2 rounded-xl bg-rose-500 px-6 py-3 text-sm font-black text-white hover:bg-rose-400 transition shadow-lg shadow-rose-500/20">
                <i class="fa-solid fa-check"></i> Guardar y Activar Regla
              </button>
            </div>
          </div>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../stores/gymStore';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from 'chart.js';
import { Bar } from 'vue-chartjs';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const gymStore = useGymStore();
const feedback = ref('');
const feedbackTone = ref('success');
const plans = computed(() => gymStore.planCatalog);
const promotions = computed(() => gymStore.promotions);
const feedbackClass = computed(() => feedbackTone.value === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-50' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50');
const form = reactive({ id_promocion: null, name: '', description: '', discountType: 'percent', discountValue: 10, startsAt: '', validUntil: '', appliesTo: [], active: true });

const activePromotionsCount = computed(() => promotions.value.filter(p => p.active).length);

const activeClients = computed(() => gymStore.members.filter(m => m.status === 'ACTIVO' && m.membershipPrice > 0));

const totalAhorrado = computed(() => {
  return activeClients.value.reduce((acc, client) => {
    const plan = plans.value.find(p => p.name === client.plan);
    if (plan && client.membershipPrice < plan.price) {
      return acc + (plan.price - client.membershipPrice);
    }
    return acc;
  }, 0);
});

const porcentajeVentasConPromo = computed(() => {
  if (activeClients.value.length === 0) return 0;
  const withPromo = activeClients.value.filter(client => {
    const plan = plans.value.find(p => p.name === client.plan);
    return plan && client.membershipPrice < plan.price;
  });
  return (withPromo.length / activeClients.value.length) * 100;
});

const ticketMedioConDescuento = computed(() => {
  const withPromo = activeClients.value.filter(client => {
    const plan = plans.value.find(p => p.name === client.plan);
    return plan && client.membershipPrice < plan.price;
  });
  if (withPromo.length === 0) return 0;
  const totalPagado = withPromo.reduce((acc, client) => acc + client.membershipPrice, 0);
  return totalPagado / withPromo.length;
});

const isModalOpen = ref(false);
const openNewModal = () => {
  reset();
  isModalOpen.value = true;
};
const closeModal = () => {
  isModalOpen.value = false;
};
const editModal = (promo) => {
  edit(promo);
  isModalOpen.value = true;
};

const chartData = computed(() => {
  const currentMonth = new Date().getMonth();
  const currentYear = new Date().getFullYear();

  // Filtrar clientes que tienen promoción y empezaron su membresía en el mes actual
  const withPromoThisMonth = activeClients.value.filter(client => {
    const plan = plans.value.find(p => p.name === client.plan);
    const hasPromo = plan && client.membershipPrice < plan.price;
    if (!hasPromo) return false;
    
    // Si no tiene fecha, simulamos con la actual para no perder el dato en la demo
    const startDate = client.membershipStart ? new Date(`${client.membershipStart}T00:00:00`) : new Date();
    
    return startDate.getMonth() === currentMonth && startDate.getFullYear() === currentYear;
  });
  
  const baseValuesNeto = [0, 0, 0, 0];
  const baseValuesDesc = [0, 0, 0, 0];

  withPromoThisMonth.forEach((client) => {
    const plan = plans.value.find(p => p.name === client.plan);
    const neto = client.membershipPrice;
    const desc = plan.price - client.membershipPrice;
    
    const startDate = client.membershipStart ? new Date(`${client.membershipStart}T00:00:00`) : new Date();
    const day = startDate.getDate();
    
    // Agrupar en Sem 1 (1-7), Sem 2 (8-14), Sem 3 (15-21), Sem 4 (22+)
    let weekIndex = 0;
    if (day <= 7) weekIndex = 0;
    else if (day <= 14) weekIndex = 1;
    else if (day <= 21) weekIndex = 2;
    else weekIndex = 3;

    baseValuesNeto[weekIndex] += neto;
    baseValuesDesc[weekIndex] += desc;
  });
  
  return {
    labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
    datasets: [
      {
        label: 'Descuento Otorgado (S/.)',
        backgroundColor: '#a855f7', // purple-500
        data: baseValuesDesc,
        borderRadius: 4,
      },
      {
        label: 'Ingreso Neto Caja (S/.)',
        backgroundColor: '#f43f5e', // rose-500
        data: baseValuesNeto,
        borderRadius: 4,
      }
    ]
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: '#cbd5e1' } }
  },
  scales: {
    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } },
    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } }
  }
};

/**
 * Gestiona esta acción de la vista.
 */
const reset = () => Object.assign(form, { id_promocion: null, name: '', description: '', discountType: 'percent', discountValue: 10, startsAt: '', validUntil: '', appliesTo: [], active: true });
/**
 * Gestiona esta acción de la vista.
 */
const planNames = (promo) => promo.appliesTo.map((id) => plans.value.find((plan) => plan.id === id)?.name).filter(Boolean);
/**
 * Gestiona esta acción de la vista.
 */
const edit = (promo) => Object.assign(form, { id_promocion: promo.id_promocion, name: promo.name, description: promo.description, discountType: promo.discountType, discountValue: promo.discountValue, startsAt: promo.startsAt, validUntil: promo.validUntil, appliesTo: [...promo.appliesTo], active: promo.active });

/**
 * Gestiona esta acción de la vista.
 */
const save = async () => {
  try {
    await gymStore.upsertPromotion({ ...form });
    feedbackTone.value = 'success';
    feedback.value = 'Promocion guardada.';
    closeModal();
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar la promocion.';
  }
};

/**
 * Elimina el registro indicado.
 */
const remove = async (promo) => {
  if (!window.confirm(`Eliminar la promocion ${promo.name}?`)) return;
  try {
    await gymStore.deletePromotion(promo.id_promocion);
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
