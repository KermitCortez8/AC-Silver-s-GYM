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

    <!-- Aviso al volver de Stripe (cancelación, pago sin confirmar o error). -->
    <section v-if="returnNotice && !isVerifying" class="rounded-2xl border px-6 py-5" :class="noticeClass" data-test="return-notice">
      <p class="font-bold">{{ returnNotice.message }}</p>
      <div v-if="returnNotice.canRetry" class="mt-4">
        <button class="rounded-2xl bg-amber-400 px-5 py-3 font-bold text-slate-950" data-test="retry-return" @click="retryReturn">
          Verificar de nuevo
        </button>
      </div>
    </section>

    <section v-if="isVerifying" class="rounded-2xl border border-white/10 bg-white/5 p-10 text-center" data-test="verifying">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Pasarela</p>
      <h2 class="mt-2 text-2xl font-black text-white">{{ verifyingMessage }}</h2>
      <p class="mt-2 text-slate-400">Por favor, no cierres esta pantalla.</p>
    </section>

    <section v-else-if="orderCreated" class="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-6" data-test="order-created">
      <p class="text-sm uppercase tracking-[0.35em] text-emerald-100">Pago registrado</p>
      <h2 class="mt-2 text-2xl font-black text-white">Pedido #{{ orderCreated.id_pedido }}</h2>
      <p class="mt-2 text-emerald-50">{{ orderCreatedMessage }}</p>
      <div class="mt-5 flex flex-col gap-3 sm:flex-row">
        <button class="rounded-2xl bg-amber-400 px-5 py-3 font-bold text-slate-950" @click="router.push('/user/store')">
          Seguir comprando
        </button>
        <button class="rounded-2xl border border-white/10 px-5 py-3 font-bold text-white" @click="router.push('/user/dashboard')">
          Ir al inicio
        </button>
      </div>
    </section>

    <section v-else-if="!cart.length && !returnNotice" class="rounded-2xl border border-white/10 bg-white/5 p-10 text-center" data-test="empty-cart">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Carrito</p>
      <h2 class="mt-2 text-2xl font-black text-white">No hay productos para pagar</h2>
      <p class="mt-2 text-slate-400">Agrega articulos desde tienda para iniciar una compra.</p>
      <button class="mt-6 rounded-2xl bg-amber-400 px-5 py-3 font-bold text-slate-950" @click="router.push('/user/store')">
        Ver tienda
      </button>
    </section>

    <section v-else-if="cart.length" class="grid gap-6 xl:grid-cols-[1fr_420px]">
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
            <select v-model="payment.method" class="field-input" data-test="method">
              <option value="tarjeta">Tarjeta</option>
              <option value="yape">Yape</option>
              <option value="plin">Plin</option>
              <option value="transferencia">Transferencia</option>
            </select>
          </label>
          <!-- Con tarjeta, la referencia la genera Stripe. -->
          <label v-if="!isCard" class="space-y-2">
            <span class="text-sm text-slate-300">Referencia</span>
            <input v-model="payment.reference" class="field-input" data-test="reference" required />
          </label>
        </div>

        <div class="mt-5 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-50">
          {{ infoMessage }}
        </div>

        <p v-if="feedback" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackClass">
          {{ feedback }}
        </p>

        <button type="submit" class="mt-6 w-full rounded-2xl bg-amber-400 px-4 py-3 font-black text-slate-950 transition hover:bg-amber-300 disabled:opacity-60" data-test="submit" :disabled="isSubmitting">
          {{ submitLabel }}
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
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '../composables/useAuth';
import { useGymStore } from '../stores/gymStore';
import { findClientForUser } from '../utils/clientIdentity';

const route = useRoute();
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

// Estado del regreso desde Stripe (?result=success / ?result=cancel).
const isVerifying = ref(false);
const verifyingMessage = ref('Verificando tu pago...');
const returnNotice = ref(null);

const payment = reactive({
  customerName: '',
  customerEmail: '',
  dni: '',
  method: 'tarjeta',
  reference: `PAY-${Date.now()}`,
});

const isCard = computed(() => payment.method === 'tarjeta');

const feedbackClass = computed(() => {
  if (feedbackTone.value === 'error') return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

const noticeClass = computed(() => {
  const tone = returnNotice.value?.tone;
  if (tone === 'error') return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  if (tone === 'warn') return 'border-amber-400/20 bg-amber-400/10 text-amber-50';
  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

const infoMessage = computed(() =>
  isCard.value
    ? 'Serás redirigido a Stripe para pagar con tarjeta de forma segura. Reservamos tus productos mientras pagas y tu pedido se registra cuando el pago se confirma.'
    : 'Esta pasarela registra el pago en el sistema y descuenta stock del producto.',
);

const submitLabel = computed(() => {
  if (isSubmitting.value) return isCard.value ? 'Redirigiendo a Stripe...' : 'Procesando...';
  const total = `S/. ${cartTotal.value.total.toFixed(2)}`;
  return isCard.value ? `Pagar con tarjeta ${total}` : `Pagar ${total}`;
});

const orderCreatedMessage = computed(() =>
  orderCreated.value?.metodo_pago === 'tarjeta'
    ? 'Tu pago con tarjeta fue confirmado y tu compra ya aparece en pedidos del administrador.'
    : 'Tu compra fue registrada y ya aparece en pedidos del administrador.',
);

/**
 * Sincroniza los datos disponibles.
 */
const syncCustomer = () => {
  const currentUser = user.value || {};
  const currentClient = client.value || {};
  payment.customerName = currentClient.name || currentClient.nombre || currentUser.name || currentUser.nombre || '';
  payment.customerEmail = currentClient.email || currentClient.correo || currentUser.email || currentUser.correo || '';
  payment.dni = currentClient.dni || currentUser.dni || '';
};

/**
 * Envía los datos del formulario.
 * Con tarjeta, el backend crea el pedido pendiente y la sesión de Stripe, y se redirige al checkout.
 */
const submitPayment = async () => {
  feedback.value = '';
  isSubmitting.value = true;
  let redirecting = false;
  try {
    if (isCard.value) {
      const { payment: checkout } = await gymStore.createStoreCheckout({
        cliente_nombre: payment.customerName,
        cliente_correo: payment.customerEmail,
        cliente_dni: payment.dni,
        items: cart.value,
      });
      redirecting = true;
      window.location.assign(checkout.checkout_url);
      return;
    }

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
    // Si se redirige a Stripe, el botón queda bloqueado hasta que cambie la página.
    if (!redirecting) isSubmitting.value = false;
  }
};

const errorMessage = (error, fallback) => (error instanceof Error && error.message ? error.message : fallback);

/**
 * Quita ?result=... de la dirección para que recargar la página no repita el proceso.
 */
const clearReturnQuery = () => router.replace({ path: route.path, query: {} }).catch(() => {});

/**
 * El cliente volvió de Stripe tras pagar: se confirma el pago con el backend.
 */
const verifyPayment = async (sessionId) => {
  isVerifying.value = true;
  verifyingMessage.value = 'Verificando tu pago...';
  returnNotice.value = null;
  try {
    const result = await gymStore.confirmStoreCheckoutReturn(sessionId);
    if (result.confirmed) {
      orderCreated.value = { id_pedido: result.id_pedido, total: result.total, metodo_pago: 'tarjeta' };
      await clearReturnQuery();
    } else {
      returnNotice.value = {
        tone: 'warn',
        message: 'Aún no podemos confirmar tu pago. Si ya pagaste, espera unos segundos y verifica de nuevo.',
        canRetry: true,
      };
    }
  } catch (error) {
    const message = errorMessage(error, 'No se pudo verificar el pago.');
    if (/reembolso/i.test(message)) {
      returnNotice.value = {
        tone: 'error',
        message: 'Recibimos tu pago, pero el pedido ya había sido cancelado. Comunícate con el gimnasio y menciona esta compra.',
        canRetry: false,
      };
    } else {
      returnNotice.value = { tone: 'error', message, canRetry: true };
    }
  } finally {
    isVerifying.value = false;
  }
};

/**
 * El cliente canceló en Stripe: se cancela el pedido pendiente y se restaura el carrito.
 */
const cancelPayment = async (idPedido) => {
  isVerifying.value = true;
  verifyingMessage.value = 'Cancelando el pago y restaurando tu carrito...';
  returnNotice.value = null;
  try {
    const result = await gymStore.cancelStoreCheckout(idPedido);
    if (result.paid) {
      // Pagó justo antes de cancelar: se respeta el pago.
      orderCreated.value = { id_pedido: result.id_pedido, metodo_pago: 'tarjeta' };
    } else {
      const parts = [];
      if (result.restored?.length) parts.push('Cancelaste el pago y restauramos tu carrito.');
      else if (result.already_cancelled) parts.push('Este pago ya había sido cancelado.');
      else parts.push('Cancelaste el pago.');
      if (result.skipped?.length) {
        const detail = result.skipped
          .map((entry) => (entry.disponible > 0 ? `${entry.nombre} (quedan ${entry.disponible})` : `${entry.nombre} (agotado)`))
          .join(', ');
        parts.push(`Sin stock suficiente para: ${detail}.`);
      }
      returnNotice.value = { tone: 'info', message: parts.join(' ') };
    }
    await clearReturnQuery();
  } catch (error) {
    returnNotice.value = { tone: 'error', message: errorMessage(error, 'No se pudo cancelar el pago.'), canRetry: false };
  } finally {
    isVerifying.value = false;
  }
};

/**
 * Lee la dirección al volver de Stripe y ejecuta la acción correspondiente.
 */
const handleReturn = async () => {
  const result = String(route.query.result || '');
  const sessionId = String(route.query.session_id || '');
  const idPedido = Number(route.query.pedido || 0);
  if (result === 'success' && sessionId) return verifyPayment(sessionId);
  if (result === 'cancel' && idPedido > 0) return cancelPayment(idPedido);
  return undefined;
};

const retryReturn = () => handleReturn();

// Si el navegador restaura la página desde la memoria (botón "atrás" desde Stripe), se desbloquea el botón.
const handlePageShow = (event) => {
  if (event.persisted) isSubmitting.value = false;
};

onMounted(() => {
  window.addEventListener('pageshow', handlePageShow);
  syncCustomer();
  gymStore.fetchFromBackend?.().catch(() => {});
  handleReturn();
});

onBeforeUnmount(() => {
  window.removeEventListener('pageshow', handlePageShow);
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