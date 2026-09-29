<template>
  <div class="space-y-6">
    <section
      class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur"
    >
      <div
        class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between"
      >
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">
            Administracion
          </p>
          <h1 class="mt-2 text-3xl font-black text-white">
            Clientes del sistema
          </h1>
          <p class="mt-2 text-slate-300">
            Gestiona clientes, datos de contacto y activacion de membresias.
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-3">
          <div
            class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300"
          >
            <p class="text-slate-400">Total</p>
            <p class="text-xl font-black text-white">{{ clients.length }}</p>
          </div>

          <div
            class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300"
          >
            <p class="text-slate-400">Activos</p>
            <p class="text-xl font-black text-white">{{ activeClients }}</p>
          </div>

          <div
            class="rounded-2xl bg-slate-900/80 px-4 py-3 text-sm text-slate-300"
          >
            <p class="text-slate-400">En tramite</p>
            <p class="text-xl font-black text-white">{{ pendingClients }}</p>
          </div>
        </div>
      </div>
    </section>

    <section
      class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur"
    >
      <div
        class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"
      >
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">
            Lista
          </p>
          <h2 class="mt-2 text-2xl font-black text-white">
            Clientes registrados
          </h2>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row">
          <input
            v-model="search"
            class="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none"
            placeholder="Buscar por ID, nombre, DNI o correo..."
          />

          <button
            class="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950"
            @click="openNewClient"
          >
            Nuevo cliente
          </button>
        </div>
      </div>

      <p
        v-if="feedbackMessage"
        class="mt-4 rounded-2xl border px-4 py-3 text-sm"
        :class="feedbackToneClass"
      >
        {{ feedbackMessage }}
      </p>

      <div class="mt-5 overflow-x-auto">
        <table class="w-full min-w-[960px] text-left text-sm">
          <thead
            class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400"
          >
            <tr>
              <th class="px-5 py-4 font-bold">ID</th>
              <th class="px-5 py-4 font-bold">Cliente</th>
              <th class="px-5 py-4 font-bold">Plan</th>
              <th class="px-5 py-4 font-bold">Membresia</th>
              <th class="px-5 py-4 font-bold">Vigencia</th>
              <th class="px-5 py-4 font-bold">Acciones</th>
            </tr>
          </thead>

          <tbody class="divide-y divide-white/10">
            <tr
              v-for="client in filteredClients"
              :key="client.id"
              class="transition hover:bg-white/[0.04]"
            >
              <td class="px-5 py-4 align-top">
                <span
                  class="rounded-full bg-white/5 px-3 py-1 text-xs font-bold text-cyan-100"
                >
                  {{ client.id }}
                </span>
              </td>

              <td class="px-5 py-4 align-top font-bold text-white">
                {{ client.name || 'Sin nombre' }}
              </td>

              <td class="px-5 py-4 align-top text-slate-300">
                {{ client.plan || 'MENSUAL' }}
              </td>

              <td class="px-5 py-4 align-top">
                <span :class="statusClass(displayMembershipStatus(client))">
                  {{ displayMembershipStatus(client) }}
                </span>
              </td>

              <td class="px-5 py-4 align-top text-slate-400">
                {{ client.membershipStart || 'por activar' }}
                -
                {{ client.membershipEnd || 'por activar' }}
              </td>

              <td class="px-5 py-4 align-top">
                <div class="flex shrink-0 flex-wrap gap-2">
                  <button
                    type="button"
                    class="grid h-9 w-9 place-items-center rounded-xl border border-white/10 text-white hover:bg-white/5"
                    title="Ver detalles"
                    aria-label="Ver detalles"
                    @click="openDetails(client)"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-4 w-4"
                    >
                      <circle cx="12" cy="12" r="9" />
                      <line x1="12" y1="11" x2="12" y2="16" />
                      <circle
                        cx="12"
                        cy="7.5"
                        r="0.75"
                        fill="currentColor"
                        stroke="none"
                      />
                    </svg>
                  </button>

                  <button
                    v-if="isPendingMembership(client)"
                    type="button"
                    class="rounded-xl bg-emerald-400 px-3 py-2 text-xs font-bold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                    :disabled="activatingClientId === client.id"
                    @click="requestActivation(client)"
                  >
                    {{
                      activatingClientId === client.id
                        ? 'Activando...'
                        : 'Activar'
                    }}
                  </button>

                  <button
                    v-if="
                      isActiveStatus(client.status) &&
                      isActiveStatus(client.membershipStatus)
                    "
                    type="button"
                    class="rounded-xl border border-white/20 px-3 py-2 text-xs font-bold text-white disabled:opacity-50"
                    :disabled="Boolean(notifyingClientId)"
                    @click="retryActivationEmail(client)"
                  >
                    {{
                      notifyingClientId === client.id
                        ? 'Enviando...'
                        : 'Notificar activación'
                    }}
                  </button>

                  <button
                    type="button"
                    class="grid h-9 w-9 place-items-center rounded-xl border border-white/10 text-white hover:bg-white/5"
                    title="Editar"
                    @click="editClient(client)"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-4 w-4"
                    >
                      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
                    </svg>
                  </button>

                  <button
                    type="button"
                    class="grid h-9 w-9 place-items-center rounded-xl border border-rose-400/30 text-rose-100 hover:bg-rose-400/10"
                    title="Eliminar"
                    @click="confirmDelete(client)"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      class="h-4 w-4"
                    >
                      <path d="M4 7h16M9 7V4h6v3m-8 0 1 13h8l1-13" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p
        v-if="!filteredClients.length"
        class="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400"
      >
        No hay clientes para mostrar.
      </p>
    </section>

    <WorkspaceDialog
      :open="isEditorOpen"
      :title="editingId ? 'Editar cliente' : 'Nuevo cliente'"
      @close="closeEditor"
    >
      <form @submit.prevent="handleSubmit">
        <div class="mt-6 grid gap-4 sm:grid-cols-2">
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm ws-soft">Nombre</span>

            <input
              v-model="form.nombre"
              class="ws-input"
              placeholder="Jose Perez"
            />
          </label>

          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm ws-soft">Correo</span>

            <input
              v-model="form.correo"
              type="email"
              class="ws-input"
              placeholder="cliente@correo.com"
            />
          </label>

          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm ws-soft">Contraseña</span>

            <input
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              class="ws-input"
              :placeholder="editingId ? 'Dejar vacio para conservar la actual' : 'Minimo 6 caracteres'"
            />
          </label>

          <label class="space-y-2">
            <span class="text-sm ws-soft">Teléfono</span>
            <input
              v-model="form.telefono"
              class="ws-input"
              placeholder="999 111 222"
            />
          </label>

          <label class="space-y-2">
            <span class="text-sm ws-soft">DNI</span>
            <input v-model="form.dni" class="ws-input" placeholder="12345678" />
          </label>

          <label class="space-y-2">
            <span class="text-sm ws-soft">Plan</span>
            <select v-model="form.plan" class="ws-input">
              <option value="MENSUAL">MENSUAL</option>
              <option value="3 MESES">3 MESES</option>
              <option value="ANUAL">ANUAL</option>
            </select>
          </label>

          <label class="space-y-2">
            <span class="text-sm ws-soft">Promocion</span>
            <select v-model="form.id_promocion" class="ws-input">
              <option :value="0">SIN PROMOCION</option>
              <option
                v-for="p in availablePromotions"
                :key="p.id"
                :value="p.id_promocion"
              >
                {{ p.name }}
              </option>
            </select>
            <p class="text-xs ws-muted">
              Precio estimado: S/. {{ estimatedCharge.finalPrice }}
              <span
                v-if="estimatedCharge.discountAmount > 0"
                class="ws-warning"
              >
                (descuento: S/. {{ estimatedCharge.discountAmount }})
              </span>
            </p>
          </label>

          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm ws-soft">Estado</span>
            <select v-model="form.estado" class="ws-input">
              <option value="EN_TRAMITE">EN_TRAMITE</option>
              <option value="ACTIVO" :disabled="editingNeedsActivation">
                ACTIVO
              </option>
              <option value="INACTIVO">INACTIVO</option>
            </select>
            <p v-if="editingNeedsActivation" class="text-xs ws-muted">
              La preinscripción se activa desde «Activar», después de confirmar
              el pago.
            </p>
          </label>
        </div>

        <button
          type="submit"
          class="mt-6 w-full rounded-2xl ws-primary px-4 py-3 font-bold transition"
        >
          {{ editingId ? 'Guardar cambios' : 'Registrar cliente' }}
        </button>
      </form>
    </WorkspaceDialog>

    <WorkspaceDialog
      :open="isDetailsOpen && Boolean(viewingClient)"
      title="Detalles del cliente"
      @close="closeDetails"
    >
      <template v-if="viewingClient">
        <div class="mb-6 border-b ws-border pb-5">
          <h3 class="text-2xl font-black ws-text break-words">
            {{ viewingClient.name || 'Sin nombre' }}
          </h3>
          <span class="ws-badge ws-tint-info ws-info mt-3">{{
            viewingClient.id
          }}</span>
        </div>
        <dl class="client-detail-grid">
          <div class="client-detail-wide">
            <dt>Correo electrónico</dt>
            <dd>{{ viewingClient.email || 'Sin correo' }}</dd>
          </div>
          <div>
            <dt>DNI</dt>
            <dd>{{ viewingClient.dni || 'Sin DNI' }}</dd>
          </div>
          <div>
            <dt>Teléfono</dt>
            <dd>{{ viewingClient.phone || 'Sin teléfono' }}</dd>
          </div>
          <div>
            <dt>Plan</dt>
            <dd>{{ viewingClient.plan || 'MENSUAL' }}</dd>
          </div>
          <div>
            <dt>Promoción</dt>
            <dd>{{ viewingClient.promocion || 'SIN PROMOCION' }}</dd>
          </div>
          <div>
            <dt>Membresía</dt>
            <dd>
              <span
                class="ws-badge"
                :class="
                  isActiveStatus(displayMembershipStatus(viewingClient))
                    ? 'ws-success ws-tint-success'
                    : isPendingStatus(displayMembershipStatus(viewingClient))
                      ? 'ws-warning ws-tint-warning'
                      : 'ws-soft ws-inset'
                "
                >{{ displayMembershipStatus(viewingClient) }}</span
              >
            </dd>
          </div>
          <div>
            <dt>Vigencia</dt>
            <dd>
              {{ viewingClient.membershipStart || 'Por activar' }}
              <span class="block ws-muted text-xs mt-1">
                hasta {{ viewingClient.membershipEnd || 'Por activar' }}
              </span>
            </dd>
          </div>

          <div
            v-if="viewingClient.paymentReference || viewingClient.paymentStatus"
            class="client-detail-wide"
          >
            <dt>Pago</dt>
            <dd>
              {{ viewingClient.paymentStatus || 'PENDIENTE' }}
              <span
                v-if="viewingClient.paymentReference"
                class="block ws-muted text-sm mt-1"
              >
                {{ viewingClient.paymentReference }}
              </span>
            </dd>
          </div>

          <div
            v-if="
              Number(viewingClient.membershipPrice || 0) > 0 &&
              getPlanPrice(viewingClient.plan) > Number(viewingClient.membershipPrice || 0)
            "
            class="client-detail-wide"
          >
            <dt>Descuento aplicado</dt>
            <dd>
              Precio base: S/. {{ getPlanPrice(viewingClient.plan).toFixed(2) }}
              <span class="block ws-success text-sm mt-1">
                Pagado: S/. {{ Number(viewingClient.membershipPrice || 0).toFixed(2) }}
                · Ahorro: S/. {{ (getPlanPrice(viewingClient.plan) - Number(viewingClient.membershipPrice || 0)).toFixed(2) }}
              </span>
            </dd>
          </div>
        </dl>

        <div class="mt-6 flex flex-col gap-3">
          <button
            v-if="viewingClient.paymentStatus === 'PENDIENTE'"
            type="button"
            class="w-full rounded-xl border ws-border-warning ws-tint-warning px-4 py-3 font-bold ws-warning transition ws-hover"
            @click="markAsPaidManual(viewingClient)"
          >
            Confirmar Pago (Manual/Efectivo)
          </button>
          <button
            v-if="viewingClient.paymentStatus === 'PAGADO' && !isActiveStatus(viewingClient.status)"
            type="button"
            class="w-full rounded-xl border ws-border-success ws-tint-success px-4 py-3 font-bold ws-success transition ws-hover"
            @click="requestActivation(viewingClient)"
          >
            Activar Membresía
          </button>
        </div>
      </template>
    </WorkspaceDialog>
    <ConfirmDialog
      v-if="pendingActivation"
      title="¿Estás seguro de la activación?"
      :message="`Se activará la cuenta de ${pendingActivation.name || pendingActivation.id} y se enviará un correo a ${pendingActivation.email || 'su correo registrado'}.`"
      confirm-label="Sí, activar"
      :busy="Boolean(activatingClientId)"
      :error="activationError"
      @cancel="cancelActivation"
      @confirm="activateMembership(pendingActivation)"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';

import WorkspaceDialog from '../components/WorkspaceDialog.vue';
import { useGymStore } from '../stores/gymStore';
import { useAuthStore } from '../stores/authStore';
import { apiPost } from '../services/apiClient';
import ConfirmDialog from '../components/ConfirmDialog.vue';

const gymStore = useGymStore();
const authStore = useAuthStore();

const clients = computed(() => gymStore.members);

const search = ref('');
const editingId = ref('');
const isEditorOpen = ref(false);
const isDetailsOpen = ref(false);
const viewingClient = ref(null);
const feedbackMessage = ref('');
const feedbackTone = ref('info');
const activatingClientId = ref('');
const pendingActivation = ref(null);
const activationError = ref('');
const notifyingClientId = ref('');
const editingNeedsActivation = computed(() => {
  const client = clients.value.find((entry) => entry.id === editingId.value);
  return (
    client &&
    ['EN_TRAMITE', 'PENDIENTE_PAGO'].includes(
      normalizeStatus(client.membershipStatus),
    )
  );
});

const requestActivation = (client) => {
  if (activatingClientId.value) return;
  pendingActivation.value = { ...client };
  activationError.value = '';
};
const cancelActivation = () => {
  if (activatingClientId.value) return;
  pendingActivation.value = null;
  activationError.value = '';
};
const notificationMessage = (notification) => {
  if (notification?.status === 'sent')
    return 'Correo de activación enviado al cliente.';
  if (notification?.status === 'queued')
    return 'El correo está pendiente de envío y se reintentará automáticamente.';
  return 'El correo no se pudo enviar. Revisa la configuración del servicio y usa Notificar activación para reintentarlo.';
};
const retryActivationEmail = async (client) => {
  if (notifyingClientId.value) return;
  notifyingClientId.value = client.id;
  try {
    const idCliente =
      client.id_cliente || Number(String(client.id).replace(/^SGCLI/i, ''));
    const notification = await apiPost(
      `/clientes/${idCliente}/notificar-activacion`,
      {},
      authStore.token,
    );
    feedbackTone.value = ['sent', 'queued'].includes(notification.status)
      ? 'success'
      : 'info';
    feedbackMessage.value = notificationMessage(notification);
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error.message || 'No se pudo enviar el correo.';
  } finally {
    notifyingClientId.value = '';
  }
};

const form = reactive({
  nombre: '',
  correo: '',
  telefono: '',
  dni: '',
  password: '',
  plan: 'MENSUAL',
  id_promocion: 0,
  estado: 'EN_TRAMITE',
});

/**
 * Normaliza el valor recibido.
 */
const normalizeStatus = (value) =>
  String(value || '')
    .trim()
    .toUpperCase();

/**
 * Obtiene el estado de membresía mostrado para el cliente.
 */
const displayMembershipStatus = (client) =>
  normalizeStatus(client.membershipStatus || client.status || 'EN_TRAMITE');

/**
 * Valida si el estado corresponde a una membresía activa.
 */
const isActiveStatus = (value) =>
  ['ACTIVO', 'ACTIVA'].includes(normalizeStatus(value));

/**
 * Valida si el estado corresponde a una membresía en trámite.
 */
const isPendingStatus = (value) => normalizeStatus(value).includes('TRAMITE');

/**
 * Valida si la membresía del cliente se encuentra pendiente.
 */
const isPendingMembership = (client) =>
  isPendingStatus(displayMembershipStatus(client)) ||
  isPendingStatus(client.status);

/**
 * Obtiene las clases visuales correspondientes al estado.
 */
const statusClass = (value) => {
  if (isActiveStatus(value)) {
    return 'font-semibold text-emerald-300';
  }

  if (isPendingStatus(value)) {
    return 'font-semibold text-amber-300';
  }

  return 'font-semibold text-slate-300';
};

const getPlanPrice = (planName) => {
  const plan = gymStore.planCatalog.find((p) => p.name === planName);
  return plan ? Number(plan.price || 0) : 0;
};

const availablePromotions = computed(() => {
  const active = gymStore.activePromotions;
  if (form.id_promocion) {
    const current = gymStore.promotions.find(p => Number(p.id_promocion) === Number(form.id_promocion));
    if (current && !active.some(p => Number(p.id_promocion) === Number(current.id_promocion))) {
      return [...active, current];
    }
  }
  return active;
});

const estimatedCharge = computed(() => {
  try {
    const plan = gymStore.planCatalog.find((p) => p.name === form.plan) || gymStore.planCatalog[0];
    if (!plan) return { finalPrice: 0, discountAmount: 0 };
    return gymStore.calculatePlanCharge(plan.id, form.id_promocion ? `promo-${form.id_promocion}` : '');
  } catch (e) {
    return { finalPrice: 0, discountAmount: 0 };
  }
});

const filteredClients = computed(() => {
  const query = search.value.trim().toLowerCase();

  if (!query) {
    return clients.value;
  }

  return clients.value.filter((client) =>
    [
      client.id,
      client.name,
      client.email,
      client.phone,
      client.dni,
      client.plan,
      client.promocion,
      client.status,
      client.membershipStatus,
      client.paymentReference,
    ]
      .join(' ')
      .toLowerCase()
      .includes(query),
  );
});

const activeClients = computed(
  () =>
    clients.value.filter((client) =>
      isActiveStatus(displayMembershipStatus(client)),
    ).length,
);

const pendingClients = computed(
  () => clients.value.filter((client) => isPendingMembership(client)).length,
);

const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success') {
    return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50';
  }

  if (feedbackTone.value === 'error') {
    return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  }

  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

/**
 * Restablece los datos del formulario.
 */
const resetForm = () => {
  editingId.value = '';

  form.nombre = '';
  form.correo = '';
  form.telefono = '';
  form.dni = '';
  form.password = '';
  form.plan = 'MENSUAL';
  form.id_promocion = 0;
  form.estado = 'EN_TRAMITE';
};

/**
 * Abre el formulario para registrar un cliente nuevo.
 */
const openNewClient = () => {
  resetForm();
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

/**
 * Cierra el formulario de creación o edición.
 */
const closeEditor = () => {
  isEditorOpen.value = false;
  resetForm();
};

/**
 * Carga los datos de un cliente en el formulario de edición.
 */
const editClient = (client) => {
  editingId.value = client.id;

  form.nombre = client.name || '';
  form.correo = client.email || '';
  form.telefono = client.phone || '';
  form.dni = client.dni || '';
  form.password = '';
  form.plan = client.plan || 'MENSUAL';
  form.id_promocion = Number(client.id_promocion || 0);
  form.estado = client.status || 'ACTIVO';

  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

/**
 * Abre el modal con los detalles del cliente seleccionado.
 */
const openDetails = (client) => {
  viewingClient.value = client;
  isDetailsOpen.value = true;
};

/**
 * Cierra el modal de detalles y limpia el cliente seleccionado.
 */
const closeDetails = () => {
  isDetailsOpen.value = false;
  viewingClient.value = null;
};

/**
 * Gestiona la eliminación de un cliente previa confirmación.
 */
const confirmDelete = async (client) => {
  if (!window.confirm(`Eliminar al cliente ${client.id}?`)) {
    return;
  }

  try {
    await gymStore.deleteClient(client.id);

    feedbackTone.value = 'success';

    feedbackMessage.value = `Cliente ${client.id} eliminado.`;

    if (editingId.value === client.id) {
      closeEditor();
    }
  } catch (error) {
    feedbackTone.value = 'error';

    feedbackMessage.value =
      error instanceof Error
        ? error.message
        : 'No se pudo eliminar el cliente.';
  }
};

/**
 * Marca la membresía como pagada en efectivo manualmente.
 */
const markAsPaidManual = async (client) => {
  if (!client || !window.confirm(`¿Confirmas que recibiste el pago en efectivo para la membresía de ${client.name}?`)) return;
  const idCliente = client.id_cliente || Number(String(client.id || '').replace(/^SGCLI/i, ''));
  
  if (!idCliente) return;

  try {
    const saved = await gymStore.confirmarPagoEfectivo(idCliente);
    if (viewingClient.value && viewingClient.value.id === saved.id) {
      viewingClient.value = { ...saved };
    }
    feedbackTone.value = 'success';
    feedbackMessage.value = `Pago de ${saved.id} confirmado correctamente. Ya puedes activar la membresía.`;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo registrar el pago.';
  }
};

/**
 * Activa la membresía del cliente seleccionado.
 */
const activateMembership = async (client) => {
  if (!client || activatingClientId.value) return;
  const idCliente =
    client.id_cliente || Number(String(client.id || '').replace(/^SGCLI/i, ''));

  if (!idCliente) {
    feedbackTone.value = 'error';

    feedbackMessage.value = 'No se encontro el ID numerico del cliente.';
    activationError.value = feedbackMessage.value;

    return;
  }

  activatingClientId.value = client.id;
  activationError.value = '';

  try {
    const saved = await gymStore.activateClientMembership(idCliente);

    feedbackTone.value = 'success';

    feedbackMessage.value = `Membresía de ${saved.id} activada. ${notificationMessage(saved.notification)}`;
    pendingActivation.value = null;
  } catch (error) {
    feedbackTone.value = 'error';

    feedbackMessage.value =
      error instanceof Error
        ? error.message
        : 'No se pudo activar la membresia.';
    activationError.value = feedbackMessage.value;
  } finally {
    activatingClientId.value = '';
  }
};

/**
 * Registra o actualiza los datos de un cliente.
 */
const handleSubmit = async () => {
  try {
    const saved = await gymStore.upsertClient({
      id_usuario: editingId.value || undefined,

      nombre: form.nombre,

      correo: form.correo,

      telefono: form.telefono,

      dni: form.dni,

      password: form.password,

      plan: form.plan,

      id_promocion: form.id_promocion || undefined,

      estado: form.estado,
    });

    closeEditor();

    feedbackTone.value = 'success';

    feedbackMessage.value = `Cliente ${saved.id} guardado con estado ${saved.status || form.estado}.`;
  } catch (error) {
    feedbackTone.value = 'error';

    feedbackMessage.value =
      error instanceof Error ? error.message : 'No se pudo guardar el cliente.';
  }
};

onMounted(() => {
  gymStore
    .fetchFromBackend?.()
    .catch((error) => console.warn('No se pudo refrescar clientes:', error));
});
</script>

<style scoped>
.client-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.25rem;
}
.client-detail-grid dt {
  color: var(--ws-muted);
  font-size: 0.8rem;
  margin-bottom: 0.4rem;
}
.client-detail-grid dd {
  color: var(--ws-text);
  font-size: 0.95rem;
  font-weight: 600;
  overflow-wrap: anywhere;
}
.client-detail-wide {
  grid-column: 1 / -1;
}
@media (max-width: 380px) {
  .client-detail-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

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
