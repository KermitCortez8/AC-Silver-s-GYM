<template>
  <div class="workspace-view space-y-6">
    <section class="ws-panel ws-hero">
      <div class="ws-toolbar">
        <div>
          <p class="ws-eyebrow">Membresías</p>
          <h1 class="ws-title">Pagos de membresías</h1>
          <p class="ws-description">Consulta los pagos del registro de clientes. Los cobros de Stripe se registran cuando se confirma el pago.</p>
        </div>
        <button type="button" class="ws-btn" :disabled="loading || gymStore.isSyncing" @click="refresh">
          <RefreshCw :size="17" aria-hidden="true" />
          {{ loading ? 'Actualizando…' : 'Actualizar' }}
        </button>
      </div>
    </section>

    <p v-if="error" role="alert" class="ws-notice ws-tint-danger ws-danger">{{ error }}</p>

    <section class="grid gap-4 md:grid-cols-3" aria-label="Resumen de pagos">
      <article class="ws-metric">
        <p class="ws-muted text-sm">Membresías registradas</p>
        <p class="ws-metric-value">{{ summary.total }}</p>
        <p class="ws-muted text-xs">{{ summary.paid }} pagos confirmados</p>
      </article>
      <article class="ws-metric">
        <p class="ws-muted text-sm">Importe cobrado</p>
        <p class="ws-metric-value ws-success">{{ money(summary.collected) }}</p>
        <p class="ws-muted text-xs">Pagos confirmados de membresías</p>
      </article>
      <article class="ws-metric">
        <p class="ws-muted text-sm">Pendientes de pago</p>
        <p class="ws-metric-value ws-warning">{{ summary.pending }}</p>
        <p class="ws-muted text-xs">{{ money(summary.outstanding) }} por cobrar</p>
      </article>
    </section>

    <section class="ws-panel space-y-5" :aria-busy="loading">
      <div class="ws-toolbar">
        <div>
          <p class="ws-eyebrow">Historial</p>
          <h2 class="ws-heading mt-1">Pagos registrados</h2>
          <p class="ws-muted text-sm mt-1">El resumen corresponde a los filtros seleccionados.</p>
        </div>
        <button v-if="hasFilters" type="button" class="ws-btn" @click="clearFilters">Limpiar filtros</button>
      </div>

      <div class="payment-filters">
        <label class="payment-search">
          <span class="ws-field-label">Buscar</span>
          <input v-model="filters.search" type="search" class="ws-input" placeholder="Cliente, DNI, plan o referencia" />
        </label>
        <label>
          <span class="ws-field-label">Estado del pago</span>
          <select v-model="filters.status" class="ws-input">
            <option value="">Todos los estados</option>
            <option value="PAGADO">Pagado</option>
            <option value="PENDIENTE">Pendiente</option>
            <option value="SIN_REGISTRO">Sin registro</option>
          </select>
        </label>
        <label>
          <span class="ws-field-label">Método</span>
          <select v-model="filters.method" class="ws-input">
            <option value="">Todos los métodos</option>
            <option v-for="method in methods" :key="method" :value="method">{{ methodLabel(method) }}</option>
          </select>
        </label>
        <label>
          <span class="ws-field-label">Fecha de pago desde</span>
          <input v-model="filters.from" type="date" class="ws-input" :max="filters.to || undefined" />
        </label>
        <label>
          <span class="ws-field-label">Fecha de pago hasta</span>
          <input v-model="filters.to" type="date" class="ws-input" :min="filters.from || undefined" />
        </label>
      </div>
      <p v-if="filters.from || filters.to" class="ws-muted text-xs">El rango de fechas muestra únicamente registros con fecha de pago.</p>

      <p v-if="loading && !payments.length" role="status" class="ws-empty">Cargando pagos…</p>
      <div v-else-if="pagination.items.length" class="ws-table-wrap">
        <table class="ws-table payment-table">
          <caption class="sr-only">Historial de pagos de membresías</caption>
          <thead>
            <tr>
              <th scope="col">Cliente</th>
              <th scope="col">Membresía</th>
              <th scope="col">Importe</th>
              <th scope="col">Estado</th>
              <th scope="col">Método</th>
              <th scope="col">Fecha de pago</th>
              <th scope="col">Referencia</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="payment in pagination.items" :key="payment.id_membresia">
              <td>
                <RouterLink class="ws-action-link font-bold" :to="{ path: '/admin/clients', query: { search: payment.id_usuario } }">{{ payment.nombre }}</RouterLink>
                <p class="ws-muted text-xs mt-1">{{ payment.correo || 'Sin correo' }}</p>
                <p class="ws-muted text-xs mt-1">{{ payment.id_usuario }}<span v-if="payment.dni"> · DNI {{ payment.dni }}</span></p>
              </td>
              <td>
                <p class="font-bold">{{ payment.plan }}</p>
                <p class="ws-muted text-xs mt-1">#{{ payment.id_membresia }}</p>
              </td>
              <td class="font-bold whitespace-nowrap">{{ money(payment.monto_pago) }}</td>
              <td><span class="ws-badge" :class="statusClass(payment.estado_pago)">{{ statusLabel(payment.estado_pago) }}</span></td>
              <td>{{ methodLabel(payment.metodo_pago) }}</td>
              <td class="whitespace-nowrap">{{ formatDate(payment.fecha_pago) }}</td>
              <td class="payment-reference">{{ payment.referencia_pago || 'Sin referencia' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="!error" class="ws-empty" role="status">
        <CreditCard :size="30" aria-hidden="true" />
        <h3>{{ hasFilters ? 'No hay pagos que coincidan' : 'Todavía no hay pagos registrados' }}</h3>
        <p>{{ hasFilters ? 'Cambia los filtros para ver otros registros.' : 'Las membresías del registro de clientes aparecerán aquí con su estado de pago.' }}</p>
      </div>

      <div v-if="pagination.total" class="ws-toolbar">
        <p class="ws-muted text-sm" aria-live="polite">{{ pagination.start }}–{{ pagination.end }} de {{ pagination.total }} registros</p>
        <nav class="flex items-center gap-2" aria-label="Páginas del historial de pagos">
          <button type="button" class="ws-btn" :disabled="pagination.page <= 1" @click="page = pagination.page - 1">Anterior</button>
          <span class="ws-muted text-sm">{{ pagination.page }} / {{ pagination.totalPages }}</span>
          <button type="button" class="ws-btn" :disabled="pagination.page >= pagination.totalPages" @click="page = pagination.page + 1">Siguiente</button>
        </nav>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { CreditCard, RefreshCw } from 'lucide-vue-next';
import { useGymStore } from '../stores/gymStore';
import { paginateClients } from '../utils/clientDirectory.js';
import { filterMembershipPayments, summarizeMembershipPayments } from '../utils/membershipPayments.js';

const gymStore = useGymStore();
const loading = ref(false);
const error = ref('');
const page = ref(1);
const filters = reactive({ search: '', status: '', method: '', from: '', to: '' });
const payments = computed(() => gymStore.membershipPayments);
const methods = computed(() => [...new Set(payments.value.map(p => p.metodo_pago).filter(Boolean))].sort());
const filtered = computed(() => filterMembershipPayments(payments.value, filters));
const summary = computed(() => summarizeMembershipPayments(filtered.value));
const pagination = computed(() => paginateClients(filtered.value, page.value));
const hasFilters = computed(() => Object.values(filters).some(Boolean));
const clearFilters = () => Object.keys(filters).forEach(key => { filters[key] = ''; });
watch(filters, () => { page.value = 1; });

const money = (amount) => new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(Number(amount) || 0);
const methodLabel = (method) => ({ stripe: 'Stripe', efectivo: 'Efectivo', tarjeta: 'Tarjeta' })[method] || method || 'Sin registrar';
const statusLabel = (status) => ({ PAGADO: 'Pagado', PENDIENTE: 'Pendiente', SIN_REGISTRO: 'Sin registro' })[status] || status;
const statusClass = (status) => status === 'PAGADO' ? 'ws-success ws-tint-success' : status === 'PENDIENTE' ? 'ws-warning ws-tint-warning' : 'ws-muted';
const formatDate = (value) => {
  if (!value) return 'Sin fecha de pago';
  const date = new Date(`${String(value).slice(0, 10)}T12:00:00-05:00`);
  return Number.isNaN(date.getTime()) ? 'Sin fecha de pago' : new Intl.DateTimeFormat('es-PE', { timeZone: 'America/Lima' }).format(date);
};
const refresh = async () => {
  if (loading.value) return;
  loading.value = true;
  error.value = '';
  try {
    await gymStore.fetchFromBackend({ section: 'payments', force: true });
  } catch (cause) {
    error.value = cause.message || 'No se pudieron cargar los pagos. Inténtalo de nuevo.';
  } finally {
    loading.value = false;
  }
};
onMounted(refresh);
</script>

<style scoped>
.payment-filters { display: grid; gap: 1rem; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.payment-search { grid-column: 1 / -1; }
.payment-table { min-width: 1000px; }
.payment-reference { min-width: 180px; max-width: 260px; overflow-wrap: anywhere; font-size: .75rem; }
@media (min-width: 1280px) {
  .payment-filters { grid-template-columns: minmax(220px, 2fr) repeat(4, minmax(140px, 1fr)); }
  .payment-search { grid-column: auto; }
}
@media (max-width: 480px) {
  .payment-filters { grid-template-columns: minmax(0, 1fr); }
}
</style>
