<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Pasarela</p>
          <h1 class="mt-2 text-3xl font-black text-white">Pago de tienda</h1>
          <p class="mt-2 text-slate-300">Confirma tus productos y registra el pago para generar el pedido.</p>
        </div>
        <button class="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/10" @click="router.push('/user/store')">
          Volver a tienda
        </button>
      </div>
    </section>

    <section v-if="orderCreated" class="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-6">
      <p class="text-sm uppercase tracking-[0.35em] text-emerald-100">Pago registrado</p>
      <h2 class="mt-2 text-2xl font-black text-white">Pedido #{{ orderCreated.id_pedido }}</h2>
      <p class="mt-2 text-emerald-50">Tu compra fue registrada y ya aparece en pedidos del administrador.</p>
      <div class="mt-5 flex flex-col gap-3 sm:flex-row">
        <button class="rounded-2xl bg-amber-400 px-5 py-3 font-bold text-slate-950" @click="router.push('/user/store')">
          Seguir comprando
        </button>
        <button class="rounded-2xl border border-white/10 px-5 py-3 font-bold text-white" @click="router.push('/user/dashboard')">
          Ir al inicio
        </button>
      </div>
    </section>

    <section v-else-if="!cart.length" class="rounded-2xl border border-white/10 bg-white/5 p-10 text-center">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Carrito</p>
      <h2 class="mt-2 text-2xl font-black text-white">No hay productos para pagar</h2>
      <p class="mt-2 text-slate-400">Agrega articulos desde tienda para iniciar una compra.</p>
      <button class="mt-6 rounded-2xl bg-amber-400 px-5 py-3 font-bold text-slate-950" @click="router.push('/user/store')">
        Ver tienda
      </button>
    </section>

    <section v-else class="grid gap-6 xl:grid-cols-[1fr_420px]">
      <form class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="submitPayment">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Datos de pago</p>
        <h2 class="mt-2 text-2xl font-black text-white">Confirmar compra</h2>

        <div class="mt-6 grid gap-4 sm:grid-cols-2">
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Cliente</span>
            <input v-model="payment.customerName" class="field-input" required />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Correo</span>
            <input v-model="payment.customerEmail" type="email" class="field-input" required />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">DNI</span>
            <input v-model="payment.dni" class="field-input" maxlength="12" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Metodo de pago</span>
            <select v-model="payment.method" class="field-input">
              <option value="tarjeta">Tarjeta</option>
              <option value="yape">Yape</option>
              <option value="plin">Plin</option>
              <option value="transferencia">Transferencia</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Referencia</span>
            <input v-model="payment.reference" class="field-input" required />
          </label>
        </div>

        <div class="mt-5 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-50">
          Esta pasarela registra el pago en el sistema y descuenta stock del producto.
        </div>

        <p v-if="feedback" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">
          {{ feedback }}
        </p>

        <button type="submit" class="mt-6 w-full rounded-2xl bg-amber-400 px-4 py-3 font-black text-slate-950 transition hover:bg-amber-300 disabled:opacity-60" :disabled="isSubmitting">
          {{ isSubmitting ? 'Procesando...' : `Pagar S/. ${cartTotal.total.toFixed(2)}` }}
        </button>
      </form>

      <aside class="h-fit rounded-2xl border border-white/10 bg-slate-950/60 p-6 backdrop-blur xl:sticky xl:top-6">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Resumen</p>
        <h2 class="mt-2 text-2xl font-black text-white">Productos</h2>

        <div class="mt-5 max-h-[420px] space-y-3 overflow-y-auto">
          <article v-for="item in cart" :key="item.id_producto" class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div class="flex items-start justify-between gap-3">
              <div class="flex min-w-0 items-start gap-3">
                <img
                  v-if="item.imagen_url"
                  :src="item.imagen_url"
                  :alt="item.nombre"
                  class="h-14 w-14 rounded-xl border border-white/10 object-cover"
                />
              <div class="min-w-0">
                <p class="truncate font-bold text-white">{{ item.nombre }}</p>
                <p class="mt-1 text-sm text-slate-400">Cantidad: {{ item.cantidad }}</p>
              </div>
            </div>
              <p class="shrink-0 font-black text-amber-300">S/. {{ (Number(item.precio || 0) * Number(item.cantidad || 0)).toFixed(2) }}</p>
            </div>
          </article>
        </div>

        <div class="mt-6 space-y-3 border-t border-white/10 pt-4">
          <div class="flex justify-between text-sm">
            <span class="text-slate-300">Subtotal</span>
            <span class="font-bold text-white">S/. {{ cartTotal.subtotal.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-slate-300">IGV</span>
            <span class="font-bold text-white">S/. {{ cartTotal.igv.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between border-t border-white/10 pt-3">
            <span class="font-black text-white">Total</span>
            <span class="text-xl font-black text-amber-300">S/. {{ cartTotal.total.toFixed(2) }}</span>
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';
import { findClientForUser } from '../utils/clientIdentity';

const router = useRouter();
const gymStore = useGymStore();
const { user } = useAuth();

const cart = computed(() => gymStore.cart);
const cartTotal = computed(() => gymStore.cartTotal);
const client = computed(() => findClientForUser(user.value, gymStore.members));
const feedback = ref('');
const feedbackTone = ref('info');
const isSubmitting = ref(false);
const orderCreated = ref(null);

const payment = reactive({
  customerName: '',
  customerEmail: '',
  dni: '',
  method: 'tarjeta',
  reference: `PAY-${Date.now()}`,
});

const feedbackClass = computed(() => {
  if (feedbackTone.value === 'error') return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

const syncCustomer = () => {
  const currentUser = user.value || {};
  const currentClient = client.value || {};
  payment.customerName = currentClient.name || currentClient.nombre || currentUser.name || currentUser.nombre || '';
  payment.customerEmail = currentClient.email || currentClient.correo || currentUser.email || currentUser.correo || '';
  payment.dni = currentClient.dni || currentUser.dni || '';
};

const submitPayment = async () => {
  feedback.value = '';
  isSubmitting.value = true;
  try {
    const saved = await gymStore.createStoreOrder({
      id_cliente: client.value?.id_cliente || user.value?.id_cliente || null,
      cliente_nombre: payment.customerName,
      cliente_correo: payment.customerEmail,
      cliente_dni: payment.dni,
      metodo_pago: payment.method,
      referencia_pago: payment.reference,
    });
    orderCreated.value = saved;
  } catch (error) {
    feedbackTone.value = 'error';
    feedback.value = error instanceof Error ? error.message : 'No se pudo registrar el pedido.';
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(() => {
  syncCustomer();
  gymStore.fetchFromBackend?.().catch(() => {});
});
</script>

<style scoped>
.field-input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  background: rgba(2, 6, 23, 0.72);
  padding: 0.75rem 1rem;
  color: white;
  outline: none;
}

.field-input::placeholder {
  color: #64748b;
}
</style>
