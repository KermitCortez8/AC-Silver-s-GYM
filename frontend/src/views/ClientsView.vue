<template>
  <div class="workspace-view clients-view space-y-5">
    <header class="ws-panel ws-hero ws-toolbar">
      <div>
        <p class="ws-eyebrow">Administración · Clientes</p>
        <h1 class="ws-title">Tu comunidad, en un solo lugar</h1>
        <p class="ws-description">
          Encuentra a cada cliente y gestiona sus pagos y membresías.
        </p>
      </div>
      <button type="button" class="ws-btn ws-primary" @click="openNewClient">
        <Plus :size="18" aria-hidden="true" /> Nuevo cliente
      </button>
    </header>

    <section class="client-metrics" aria-label="Resumen de clientes">
      <article class="ws-metric">
        <span class="client-metric-icon ws-info ws-tint-info"
          ><Users :size="19" aria-hidden="true"
        /></span>
        <p class="ws-muted text-sm">Clientes registrados</p>
        <p class="ws-metric-value">{{ clients.length }}</p>
        <p class="ws-muted text-xs">Tu comunidad Silver Gym</p>
      </article>
      <article class="ws-metric">
        <span class="client-metric-icon ws-success ws-tint-success"
          ><BadgeCheck :size="19" aria-hidden="true"
        /></span>
        <p class="ws-muted text-sm">Membresías activas</p>
        <p class="ws-metric-value ws-success">{{ activeClients }}</p>
        <p class="ws-muted text-xs">Listos para entrenar</p>
      </article>
      <article class="ws-metric">
        <span class="client-metric-icon ws-warning ws-tint-warning"
          ><Clock3 :size="19" aria-hidden="true"
        /></span>
        <p class="ws-muted text-sm">Por activar</p>
        <p class="ws-metric-value ws-warning">{{ readyToActivateClients }}</p>
        <p class="ws-muted text-xs">Pago confirmado, activación pendiente</p>
      </article>
      <article class="ws-metric">
        <span class="client-metric-icon ws-info ws-tint-info"
          ><CreditCard :size="19" aria-hidden="true"
        /></span>
        <p class="ws-muted text-sm">Pagos pendientes</p>
        <p class="ws-metric-value">{{ unpaidClients }}</p>
        <p class="ws-muted text-xs">Membresías por cobrar</p>
      </article>
    </section>

    <p
      v-if="feedbackMessage && !isEditorOpen"
      role="status"
      class="ws-notice"
      :class="feedbackToneClass"
    >
      <CircleCheck
        v-if="feedbackTone === 'success'"
        :size="18"
        aria-hidden="true"
      />
      <Info v-else :size="18" aria-hidden="true" />
      {{ feedbackMessage }}
    </p>

    <section class="ws-panel client-directory" :aria-busy="isLoading">
      <div class="ws-toolbar">
        <div>
          <h2 class="ws-heading">Clientes registrados</h2>
          <p class="ws-muted text-sm mt-1">
            {{
              sortOrder === 'recent'
                ? 'Los más recientes primero'
                : sortOrder === 'oldest'
                  ? 'Los más antiguos primero'
                  : 'Orden alfabético'
            }}
            · 7 clientes por página
          </p>
        </div>
        <button
          type="button"
          class="ws-btn"
          :disabled="isLoading"
          @click="refreshClients(true)"
        >
          <RefreshCw
            :size="16"
            :class="{ 'ws-spin': isLoading }"
            aria-hidden="true"
          />
          {{ isLoading ? 'Actualizando…' : 'Actualizar' }}
        </button>
      </div>

      <div class="client-filter-bar">
        <label class="ws-search client-search">
          <span class="sr-only"
            >Buscar clientes por nombre, DNI, correo o ID</span
          >
          <Search :size="18" aria-hidden="true" />
          <input
            v-model="search"
            type="search"
            class="ws-input"
            placeholder="Nombre, DNI, correo o ID…"
          />
        </label>
        <label>
          <span id="client-plan-label" class="ws-field-label">Plan</span>
          <select
            v-model="planFilter"
            aria-labelledby="client-plan-label"
            class="ws-input"
          >
            <option value="">Todos los planes</option>
            <option v-for="plan in planOptions" :key="plan" :value="plan">
              {{ plan }}
            </option>
          </select>
        </label>
        <label>
          <span id="client-payment-label" class="ws-field-label">Pago</span>
          <select
            v-model="paymentFilter"
            aria-labelledby="client-payment-label"
            class="ws-input"
          >
            <option value="">Todos los pagos</option>
            <option value="PENDIENTE">Pendiente</option>
            <option value="PAGADO">Pagado</option>
            <option value="UNKNOWN">Sin registro</option>
          </select>
        </label>
        <label>
          <span id="client-sort-label" class="ws-field-label">Ordenar por</span>
          <select
            v-model="sortOrder"
            aria-labelledby="client-sort-label"
            class="ws-input"
          >
            <option value="recent">Más recientes</option>
            <option value="oldest">Más antiguos</option>
            <option value="name">Nombre: A–Z</option>
          </select>
        </label>
      </div>

      <div class="client-status-bar">
        <div
          class="flex flex-wrap gap-2"
          role="group"
          aria-label="Filtrar por estado de membresía"
        >
          <button
            v-for="filter in statusFilters"
            :key="filter.value"
            type="button"
            class="ws-chip"
            :aria-pressed="statusFilter === filter.value"
            @click="statusFilter = filter.value"
          >
            {{ filter.label }}
            <span class="client-filter-count">{{ filter.count }}</span>
          </button>
        </div>
        <button
          v-if="hasFilters"
          type="button"
          class="client-reset"
          @click="resetFilters"
        >
          <X :size="14" aria-hidden="true" /> Limpiar filtros
        </button>
      </div>

      <div class="client-page-bar">
        <p class="ws-muted text-sm" role="status" aria-live="polite">
          <strong class="ws-text"
            >{{ pagination.start }}–{{ pagination.end }}</strong
          >
          de {{ pagination.total }} {{ hasFilters ? 'resultados' : 'clientes' }}
        </p>
        <nav class="client-pagination" aria-label="Páginas de clientes">
          <button
            type="button"
            class="client-page-arrow"
            aria-label="Página anterior"
            :disabled="pagination.page === 1"
            @click="currentPage--"
          >
            <ChevronLeft :size="18" aria-hidden="true" />
          </button>
          <template v-for="page in pagination.pages" :key="page">
            <button
              v-if="typeof page === 'number'"
              type="button"
              class="client-page-number"
              :aria-current="page === pagination.page ? 'page' : undefined"
              :aria-label="`Ir a la página ${page}`"
              @click="currentPage = page"
            >
              {{ page }}
            </button>
            <span v-else class="client-page-gap" aria-hidden="true">…</span>
          </template>
          <button
            type="button"
            class="client-page-arrow"
            aria-label="Página siguiente"
            :disabled="pagination.page === pagination.totalPages"
            @click="currentPage++"
          >
            <ChevronRight :size="18" aria-hidden="true" />
          </button>
        </nav>
      </div>

      <div v-if="isLoading && !clients.length" class="ws-empty" role="status">
        <LoaderCircle :size="28" class="ws-spin ws-info" aria-hidden="true" />
        <h3>Cargando clientes…</h3>
        <p>Estamos preparando tu lista.</p>
      </div>
      <div v-else-if="!pagination.total" class="ws-empty">
        <SearchX v-if="hasFilters" :size="32" aria-hidden="true" />
        <Users v-else :size="32" aria-hidden="true" />
        <h3>
          {{
            hasFilters
              ? 'No encontramos coincidencias'
              : 'Tu comunidad empieza aquí'
          }}
        </h3>
        <p>
          {{
            hasFilters
              ? 'Prueba otra búsqueda o ajusta los filtros.'
              : 'Registra a tu primer cliente para gestionar su membresía.'
          }}
        </p>
        <button
          type="button"
          class="ws-btn mt-4"
          @click="hasFilters ? resetFilters() : openNewClient()"
        >
          {{ hasFilters ? 'Limpiar filtros' : 'Nuevo cliente' }}
        </button>
      </div>
      <div v-else class="ws-table-wrap client-table-wrap">
        <table class="ws-table client-table">
          <caption class="sr-only">
            Clientes registrados, planes, pagos y acciones. Página
            {{
              pagination.page
            }}
            de
            {{
              pagination.totalPages
            }}.
          </caption>
          <thead>
            <tr>
              <th scope="col">Cliente</th>
              <th scope="col">Plan</th>
              <th scope="col">Membresía</th>
              <th scope="col">Pago</th>
              <th scope="col" class="client-actions-heading">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="client in pagination.items" :key="client.id">
              <td class="client-identity-cell">
                <div class="client-identity">
                  <span class="ws-avatar" aria-hidden="true">{{
                    initials(client.name)
                  }}</span>
                  <div class="min-w-0">
                    <button
                      type="button"
                      class="client-name"
                      @click="openDetails(client)"
                    >
                      {{ client.name || 'Sin nombre' }}
                    </button>
                    <p class="ws-muted client-contact">
                      {{ client.email || 'Sin correo' }}
                    </p>
                    <p class="ws-muted client-id">
                      {{ client.id }}
                      <span v-if="client.dni">· DNI {{ client.dni }}</span>
                    </p>
                  </div>
                </div>
              </td>
              <td data-label="Plan">
                <span class="client-plan">{{ client.plan || 'Sin plan' }}</span>
              </td>
              <td data-label="Membresía">
                <span class="ws-badge" :class="membershipBadgeClass(client)"
                  ><span class="client-status-dot" aria-hidden="true"></span
                  >{{ clientMembershipLabel(client) }}</span
                >
              </td>
              <td data-label="Pago">
                <span
                  class="ws-badge"
                  :class="
                    client.paymentStatus === 'PAGADO'
                      ? 'ws-success ws-tint-success'
                      : client.paymentStatus === 'PENDIENTE'
                        ? 'ws-warning ws-tint-warning'
                        : 'ws-muted ws-inset'
                  "
                  ><CircleCheck
                    v-if="client.paymentStatus === 'PAGADO'"
                    :size="13"
                    aria-hidden="true"
                  />{{
                    client.paymentStatus === 'PAGADO'
                      ? 'Pagado'
                      : client.paymentStatus === 'PENDIENTE'
                        ? 'Pendiente'
                        : 'Sin registro'
                  }}</span
                >
              </td>
              <td class="client-actions-cell">
                <div class="client-actions">
                  <button
                    v-if="
                      isPendingMembership(client) &&
                      client.paymentStatus === 'PAGADO'
                    "
                    type="button"
                    class="client-action-primary ws-success ws-tint-success"
                    :disabled="Boolean(activatingClientId)"
                    @click="requestActivation(client)"
                  >
                    <BadgeCheck :size="15" aria-hidden="true" />{{
                      activatingClientId === client.id
                        ? 'Activando…'
                        : 'Activar'
                    }}
                  </button>
                  <button
                    v-if="canPayClientWithStripe(client)"
                    type="button"
                    class="client-action-primary ws-info ws-tint-info"
                    :disabled="Boolean(payingClientId)"
                    @click="payWithStripe(client)"
                  >
                    <CreditCard :size="15" aria-hidden="true" />{{
                      payingClientId === client.id ? 'Abriendo…' : 'Pagar'
                    }}
                  </button>
                  <button
                    type="button"
                    class="client-icon-button"
                    title="Ver detalles"
                    :aria-label="`Ver detalles de ${client.name || client.id}`"
                    @click="openDetails(client)"
                  >
                    <Info :size="17" aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    class="client-icon-button"
                    title="Editar cliente"
                    :aria-label="`Editar a ${client.name || client.id}`"
                    @click="editClient(client)"
                  >
                    <Pencil :size="16" aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    class="client-icon-button client-delete"
                    title="Eliminar cliente"
                    :aria-label="`Eliminar a ${client.name || client.id}`"
                    @click="confirmDelete(client)"
                  >
                    <Trash2 :size="16" aria-hidden="true" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="pagination.total" class="ws-muted text-xs client-directory-note">
        Página {{ pagination.page }} de {{ pagination.totalPages }} · Consulta
        la vigencia y los datos completos en los detalles del cliente.
      </p>
    </section>

    <WorkspaceDialog
      :open="isEditorOpen"
      :busy="savingClient"
      :title="editingId ? 'Editar cliente' : 'Nuevo cliente'"
      @close="closeEditor"
    >
      <form @submit.prevent="handleSubmit">
        <fieldset
          :disabled="savingClient"
          class="mt-6 grid gap-4 sm:grid-cols-2"
        >
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm ws-soft">Nombre</span>

            <input
              v-model="form.nombre"
              required
              class="ws-input"
              placeholder="Jose Perez"
            />
          </label>

          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm ws-soft">Correo</span>

            <input
              v-model="form.correo"
              required
              type="email"
              class="ws-input"
              placeholder="cliente@correo.com"
            />
          </label>

          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm ws-soft">Contraseña</span>

            <input
              v-model="form.password"
              :required="!editingId"
              minlength="6"
              type="password"
              autocomplete="new-password"
              class="ws-input"
              :placeholder="
                editingId
                  ? 'Dejar vacio para conservar la actual'
                  : 'Minimo 6 caracteres'
              "
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
            <input
              v-model="form.dni"
              required
              class="ws-input"
              placeholder="12345678"
            />
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

          <label v-if="editingId" class="space-y-2 sm:col-span-2">
            <span class="text-sm ws-soft">Estado de membresía</span>
            <p class="ws-input">{{ editingMembershipLabel }}</p>
            <p v-if="editingNeedsActivation" class="text-xs ws-muted">
              La preinscripción se activa desde «Activar», después de confirmar
              el pago.
            </p>
            <p v-if="editingExpired" class="text-xs ws-danger">
              La membresía está vencida. Se necesita una nueva membresía pagada
              y activada para recuperar el acceso.
            </p>
          </label>

          <label v-if="!editingId" class="space-y-2 sm:col-span-2">
            <span class="flex items-center gap-3 text-sm ws-text">
              <input v-model="form.pagar_con_stripe" type="checkbox" />
              Realizar el pago con Stripe al registrar
            </span>
            <p class="text-xs ws-muted">
              El cliente quedará en trámite, con pago pendiente. Puedes pagar
              ahora o después desde sus detalles. La membresía se activa después
              de confirmar el pago.
            </p>
          </label>
        </fieldset>

        <p v-if="submitError" role="alert" class="mt-4 text-sm ws-warning">
          {{ submitError }}
        </p>

        <button
          type="submit"
          :disabled="savingClient"
          class="mt-6 w-full rounded-2xl ws-primary px-4 py-3 font-bold transition disabled:opacity-50"
        >
          {{
            savingClient
              ? 'Guardando...'
              : editingId
                ? 'Guardar cambios'
                : form.pagar_con_stripe
                  ? 'Registrar y pagar con Stripe'
                  : 'Registrar cliente'
          }}
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
                :class="membershipBadgeClass(viewingClient)"
                >{{ clientMembershipLabel(viewingClient) }}</span
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
              getPlanPrice(viewingClient.plan) >
                Number(viewingClient.membershipPrice || 0)
            "
            class="client-detail-wide"
          >
            <dt>Descuento aplicado</dt>
            <dd>
              Precio base: S/. {{ getPlanPrice(viewingClient.plan).toFixed(2) }}
              <span class="block ws-success text-sm mt-1">
                Pagado: S/.
                {{ Number(viewingClient.membershipPrice || 0).toFixed(2) }} ·
                Ahorro: S/.
                {{
                  (
                    getPlanPrice(viewingClient.plan) -
                    Number(viewingClient.membershipPrice || 0)
                  ).toFixed(2)
                }}
              </span>
            </dd>
          </div>
        </dl>

        <p
          v-if="clientMembershipGroup(viewingClient) === 'expired'"
          class="mt-6 rounded-xl ws-tint-danger ws-danger p-4 text-sm"
          role="status"
        >
          Acceso bloqueado por membresía vencida. Para recuperar el acceso, el
          cliente necesita una nueva membresía pagada y activada.
        </p>

        <div class="mt-6 flex flex-col gap-3">
          <button
            v-if="
              isActiveStatus(viewingClient.status) &&
              isActiveStatus(viewingClient.membershipStatus)
            "
            type="button"
            class="ws-btn"
            :disabled="Boolean(notifyingClientId)"
            @click="retryActivationEmail(viewingClient)"
          >
            <Mail :size="17" aria-hidden="true" />{{
              notifyingClientId === viewingClient.id
                ? 'Enviando…'
                : 'Notificar activación'
            }}
          </button>
          <p v-if="paymentError" role="alert" class="text-sm ws-warning">
            {{ paymentError }}
          </p>
          <button
            v-if="canPayClientWithStripe(viewingClient)"
            type="button"
            class="w-full rounded-xl ws-primary px-4 py-3 font-bold disabled:opacity-50"
            :disabled="Boolean(payingClientId)"
            @click="payWithStripe(viewingClient)"
          >
            {{
              payingClientId
                ? 'Abriendo Stripe...'
                : `Pagar S/. ${Number(viewingClient.membershipPrice || 0).toFixed(2)} con Stripe`
            }}
          </button>
          <button
            v-if="viewingClient.paymentStatus === 'PENDIENTE'"
            type="button"
            class="w-full rounded-xl border ws-border-warning ws-tint-warning px-4 py-3 font-bold ws-warning transition ws-hover"
            @click="markAsPaidManual(viewingClient)"
          >
            Confirmar Pago (Manual/Efectivo)
          </button>
          <button
            v-if="
              viewingClient.paymentStatus === 'PAGADO' &&
              clientMembershipGroup(viewingClient) === 'pending'
            "
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
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import WorkspaceDialog from '../components/WorkspaceDialog.vue';
import { useGymStore } from '../stores/gymStore';
import { useAuthStore } from '../stores/authStore';
import { apiPost } from '../services/apiClient';
import ConfirmDialog from '../components/ConfirmDialog.vue';
import { canPayClientWithStripe } from '../utils/adminClientPayment.js';
import {
  clientMembershipGroup,
  clientMembershipLabel,
  filterClientDirectory,
  paginateClients,
} from '../utils/clientDirectory.js';
import {
  BadgeCheck,
  ChevronLeft,
  ChevronRight,
  CircleCheck,
  Clock3,
  CreditCard,
  Info,
  LoaderCircle,
  Mail,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  SearchX,
  Trash2,
  Users,
  X,
} from 'lucide-vue-next';

const gymStore = useGymStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const clients = computed(() => gymStore.members);

const search = ref('');
const statusFilter = ref(
  ['active', 'pending', 'expired'].includes(route.query.status)
    ? route.query.status
    : '',
);
const planFilter = ref('');
const paymentFilter = ref(
  ['PAGADO', 'PENDIENTE', 'UNKNOWN'].includes(route.query.payment)
    ? route.query.payment
    : '',
);
const sortOrder = ref('recent');
const currentPage = ref(1);
const isLoading = ref(true);
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
const savingClient = ref(false);
const payingClientId = ref('');
const paymentError = ref('');
const submitError = ref('');
const editingClient = computed(() =>
  clients.value.find((entry) => entry.id === editingId.value),
);
const editingMembershipLabel = computed(() =>
  clientMembershipLabel(editingClient.value || {}),
);
const editingNeedsActivation = computed(
  () =>
    editingClient.value &&
    clientMembershipGroup(editingClient.value) === 'pending',
);
const editingExpired = computed(() => {
  const client = clients.value.find((entry) => entry.id === editingId.value);
  return (
    client &&
    (clientMembershipGroup(client) === 'expired' ||
      normalizeStatus(client.status) === 'VENCIDA')
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
  pagar_con_stripe: false,
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
 * Valida si la membresía del cliente se encuentra pendiente.
 */
const isPendingMembership = (client) =>
  clientMembershipGroup(client) === 'pending';

const getPlanPrice = (planName) => {
  const plan = gymStore.planCatalog.find((p) => p.name === planName);
  return plan ? Number(plan.price || 0) : 0;
};

const availablePromotions = computed(() => {
  const active = gymStore.activePromotions;
  if (form.id_promocion) {
    const current = gymStore.promotions.find(
      (p) => Number(p.id_promocion) === Number(form.id_promocion),
    );
    if (
      current &&
      !active.some(
        (p) => Number(p.id_promocion) === Number(current.id_promocion),
      )
    ) {
      return [...active, current];
    }
  }
  return active;
});

const estimatedCharge = computed(() => {
  try {
    const plan =
      gymStore.planCatalog.find((p) => p.name === form.plan) ||
      gymStore.planCatalog[0];
    if (!plan) return { finalPrice: 0, discountAmount: 0 };
    return gymStore.calculatePlanCharge(
      plan.id,
      form.id_promocion ? `promo-${form.id_promocion}` : '',
    );
  } catch (e) {
    return { finalPrice: 0, discountAmount: 0 };
  }
});

const filteredClients = computed(() =>
  filterClientDirectory(clients.value, {
    search: search.value,
    status: statusFilter.value,
    plan: planFilter.value,
    payment: paymentFilter.value,
    sort: sortOrder.value,
  }),
);
const pagination = computed(() =>
  paginateClients(filteredClients.value, currentPage.value),
);
const hasFilters = computed(() =>
  Boolean(
    search.value.trim() ||
    statusFilter.value ||
    planFilter.value ||
    paymentFilter.value,
  ),
);
const planOptions = computed(() =>
  [
    ...new Set(
      [
        ...gymStore.planCatalog.map((plan) => plan.name),
        ...clients.value.map((client) => client.plan),
      ].filter(Boolean),
    ),
  ].sort(),
);
const activeClients = computed(
  () =>
    clients.value.filter((client) => clientMembershipGroup(client) === 'active')
      .length,
);
const readyToActivateClients = computed(
  () =>
    clients.value.filter(
      (client) =>
        clientMembershipGroup(client) === 'pending' &&
        client.paymentStatus === 'PAGADO',
    ).length,
);
const unpaidClients = computed(
  () =>
    clients.value.filter((client) => client.paymentStatus === 'PENDIENTE')
      .length,
);
const statusFilters = computed(() => [
  { value: '', label: 'Todos', count: clients.value.length },
  { value: 'active', label: 'Activo', count: activeClients.value },
  {
    value: 'pending',
    label: 'En trámite',
    count: clients.value.filter(
      (client) => clientMembershipGroup(client) === 'pending',
    ).length,
  },
  {
    value: 'expired',
    label: 'Vencida',
    count: clients.value.filter(
      (client) => clientMembershipGroup(client) === 'expired',
    ).length,
  },
]);
const resetFilters = () => {
  search.value = '';
  statusFilter.value = '';
  planFilter.value = '';
  paymentFilter.value = '';
  currentPage.value = 1;
};
watch(
  [search, statusFilter, planFilter, paymentFilter, sortOrder],
  () => {
    currentPage.value = 1;
  },
  { flush: 'sync' },
);
watch(
  () => pagination.value.page,
  (page) => {
    currentPage.value = page;
  },
);
const membershipBadgeClass = (client) =>
  ({
    active: 'ws-success ws-tint-success',
    pending: 'ws-warning ws-tint-warning',
    expired: 'ws-danger ws-tint-danger',
  })[clientMembershipGroup(client)];
const initials = (name) =>
  String(name || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || '?';
const feedbackToneClass = computed(() =>
  feedbackTone.value === 'success'
    ? 'ws-tint-success ws-success'
    : feedbackTone.value === 'error'
      ? 'ws-tint-danger ws-danger'
      : 'ws-tint-info ws-info',
);
const refreshClients = async (force = false) => {
  isLoading.value = true;
  try {
    await gymStore.fetchFromBackend({ section: 'clients', force });
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value =
      error.message ||
      'No se pudo actualizar la lista de clientes. Inténtalo nuevamente.';
  } finally {
    isLoading.value = false;
  }
};

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
  form.pagar_con_stripe = false;
  submitError.value = '';
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
  if (savingClient.value) return;
  isEditorOpen.value = false;
  resetForm();
};

/**
 * Carga los datos de un cliente en el formulario de edición.
 */
const editClient = (client) => {
  submitError.value = '';
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
  paymentError.value = '';
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
  if (
    !client ||
    !window.confirm(
      `¿Confirmas que recibiste el pago en efectivo para la membresía de ${client.name}?`,
    )
  )
    return;
  const idCliente =
    client.id_cliente || Number(String(client.id || '').replace(/^SGCLI/i, ''));

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
    feedbackMessage.value =
      error instanceof Error ? error.message : 'No se pudo registrar el pago.';
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
  if (savingClient.value) return;
  savingClient.value = true;
  const isNewClient = !editingId.value;
  submitError.value = '';
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
      pagar_con_stripe: !editingId.value && form.pagar_con_stripe,
    });

    if (isNewClient) {
      resetFilters();
      sortOrder.value = 'recent';
    }
    savingClient.value = false;
    closeEditor();

    feedbackTone.value = 'success';

    feedbackMessage.value = `Cliente ${saved.id} guardado con estado ${saved.status || form.estado}.`;
    if (saved.payment?.checkout_url) {
      window.location.assign(saved.payment.checkout_url);
    } else if (saved.payment?.message) {
      feedbackTone.value = 'info';
      feedbackMessage.value = `Cliente ${saved.id} registrado. ${saved.payment.message}. Puedes retomar el pago desde sus detalles.`;
      openDetails(saved);
      paymentError.value = saved.payment.message;
    }
  } catch (error) {
    feedbackTone.value = 'error';

    feedbackMessage.value =
      error instanceof Error ? error.message : 'No se pudo guardar el cliente.';
    submitError.value = feedbackMessage.value;
  } finally {
    savingClient.value = false;
  }
};

const payWithStripe = async (client) => {
  if (payingClientId.value || !canPayClientWithStripe(client)) return;
  payingClientId.value = client.id;
  paymentError.value = '';
  try {
    const payment = await apiPost(
      `/clientes/${client.id_cliente}/pago-stripe`,
      {},
      authStore.token,
    );
    if (!payment.checkout_url)
      throw new Error(payment.message || 'No se pudo abrir Stripe.');
    window.location.assign(payment.checkout_url);
  } catch (error) {
    paymentError.value = error.message || 'No se pudo iniciar el pago.';
    feedbackTone.value = 'error';
    feedbackMessage.value = paymentError.value;
  } finally {
    payingClientId.value = '';
  }
};

onMounted(async () => {
  const stripeResult = route.query.stripe_result;
  if (stripeResult) {
    try {
      if (stripeResult === 'success') {
        if (!route.query.session_id)
          throw new Error('Falta la sesión de Stripe para verificar el pago.');
        const result = await apiPost(
          `/pagos/stripe/confirmar-retorno?session_id=${encodeURIComponent(route.query.session_id)}`,
          {},
          authStore.token,
        );
        feedbackTone.value = result.confirmed ? 'success' : 'info';
        feedbackMessage.value = result.confirmed
          ? `Pago de SGCLI${String(result.id_cliente).padStart(3, '0')} confirmado. Ya puedes activar su membresía.`
          : 'Stripe todavía no confirmó el pago. Actualiza la lista en unos momentos.';
      } else {
        feedbackTone.value = 'info';
        feedbackMessage.value =
          'Pago cancelado. El cliente sigue registrado y puedes retomar el pago desde sus detalles.';
      }
      const { stripe_result, session_id, ...query } = route.query;
      await router.replace({ path: route.path, query });
    } catch (error) {
      feedbackTone.value = 'error';
      feedbackMessage.value = `${error.message || 'No se pudo verificar el pago.'} Recarga esta página para volver a comprobarlo.`;
    }
  }
  await refreshClients(Boolean(stripeResult));
});
</script>

<style scoped>
.client-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}
.client-metrics .ws-metric {
  position: relative;
  padding: 1.1rem;
}
.clients-view > header {
  padding: 1.25rem 1.75rem;
}
.clients-view > header .ws-title {
  font-size: clamp(1.5rem, 2.5vw, 1.9rem);
}
.client-metrics .ws-metric > p:first-of-type {
  padding-right: 2rem;
}
.client-metric-icon {
  position: absolute;
  top: 0.9rem;
  right: 0.9rem;
  display: grid;
  place-items: center;
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 0.75rem;
  margin-bottom: 0.85rem;
}
.client-directory {
  display: grid;
  gap: 1rem;
}
.client-filter-bar {
  display: grid;
  grid-template-columns: minmax(230px, 2fr) repeat(3, minmax(140px, 1fr));
  gap: 0.85rem;
  align-items: end;
}
.client-search {
  min-width: 0;
}
.client-status-bar,
.client-page-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.client-filter-count {
  border-radius: 999px;
  background: var(--ws-inset);
  color: var(--ws-soft);
  padding: 0.1rem 0.45rem;
  font-size: 0.7rem;
  font-variant-numeric: tabular-nums;
}
.client-reset {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  font-weight: 650;
  color: var(--ws-muted);
  padding: 0.5rem;
  border-radius: 0.5rem;
}
.client-reset:hover {
  color: var(--ws-text);
  background: var(--ws-hover);
}
.client-page-bar {
  position: sticky;
  top: 0.75rem;
  z-index: 5;
  border: 1px solid var(--ws-border);
  background: var(--ws-inset);
  border-radius: 0.85rem;
  padding: 0.7rem 0.85rem;
}
.client-pagination {
  display: flex;
  gap: 0.3rem;
  align-items: center;
}
.client-page-number,
.client-page-arrow,
.client-page-gap {
  display: grid;
  place-items: center;
  min-width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.6rem;
  font-size: 0.8rem;
  font-weight: 750;
  color: var(--ws-muted);
}
.client-page-arrow {
  border: 1px solid var(--ws-border);
  background: var(--ws-panel);
}
.client-page-number:hover,
.client-page-arrow:not(:disabled):hover {
  background: var(--ws-hover);
  color: var(--ws-text);
}
.client-page-number[aria-current='page'] {
  background: var(--ws-info-bg);
  color: var(--ws-info);
  box-shadow: inset 0 0 0 1px var(--ws-info);
}
.client-table {
  min-width: 800px;
}
.client-table td {
  padding: 0.65rem 1rem;
  vertical-align: middle;
}
.client-table .client-identity-cell {
  width: 36%;
}
.client-identity {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}
.client-name {
  text-align: left;
  font-weight: 750;
  color: var(--ws-text);
  border-radius: 0.3rem;
}
.client-name:hover {
  color: var(--ws-info);
  text-decoration: underline;
  text-underline-offset: 3px;
}
.client-contact {
  font-size: 0.75rem;
  margin-top: 0.2rem;
  overflow-wrap: anywhere;
}
.client-id {
  font-size: 0.65rem;
  margin-top: 0.15rem;
}
.client-plan {
  font-size: 0.75rem;
  font-weight: 750;
  white-space: nowrap;
}
.client-status-dot {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 50%;
  background: currentColor;
}
.client-actions-heading {
  text-align: right;
}
.client-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.35rem;
}
.client-icon-button {
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border: 1px solid var(--ws-border);
  border-radius: 0.65rem;
  background: var(--ws-panel);
  color: var(--ws-soft);
  flex-shrink: 0;
}
.client-icon-button:hover {
  background: var(--ws-hover);
  color: var(--ws-info);
}
.client-delete:hover {
  color: var(--ws-danger);
  background: var(--ws-danger-bg);
  border-color: var(--ws-danger);
}
.client-action-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 2.25rem;
  padding: 0.45rem 0.7rem;
  border-radius: 0.65rem;
  font-size: 0.75rem;
  font-weight: 750;
  white-space: nowrap;
}
.client-action-primary:hover {
  box-shadow: inset 0 0 0 1px currentColor;
}
.client-directory-note {
  line-height: 1.5;
}
@media (max-width: 1100px) {
  .client-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .client-filter-bar {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .client-search {
    grid-column: 1 / -1;
  }
}
@media (max-width: 1023px) {
  .client-page-bar {
    top: 4.5rem;
  }
}
@media (max-width: 700px) {
  .client-metrics {
    gap: 0.65rem;
  }
  .client-metrics .ws-metric {
    padding: 0.85rem;
  }
  .client-metric-icon {
    display: none;
  }
  .clients-view > header {
    padding: 1rem;
  }
  .client-metrics .ws-metric > p:first-of-type {
    padding-right: 0;
  }
  .client-metrics .ws-metric-value {
    margin: 0.3rem 0;
  }
  .client-filter-bar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .client-filter-bar > label:last-child {
    grid-column: 1 / -1;
  }
  .client-page-bar {
    justify-content: center;
  }
  .client-page-bar > p {
    width: 100%;
    text-align: center;
  }
  .client-pagination {
    gap: 0.15rem;
  }
  .client-page-number,
  .client-page-arrow,
  .client-page-gap {
    min-width: 2rem;
  }
  .client-table-wrap {
    border: none;
    overflow: visible;
  }
  .client-table {
    min-width: 0;
    display: block;
  }
  .client-table thead {
    display: none;
  }
  .client-table tbody {
    display: grid;
    gap: 0.75rem;
  }
  .client-table tbody tr {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    border: 1px solid var(--ws-border);
    border-radius: 1rem;
    padding: 0.9rem;
    gap: 0.8rem;
  }
  .client-table td {
    display: block;
    border: none;
    padding: 0;
  }
  .client-table .client-identity-cell {
    grid-column: 1 / -1;
    width: auto;
    border-bottom: 1px solid var(--ws-border);
    padding-bottom: 0.8rem;
  }
  .client-table td[data-label]::before {
    content: attr(data-label);
    display: block;
    color: var(--ws-muted);
    font-size: 0.7rem;
    margin-bottom: 0.4rem;
  }
  .client-table .ws-badge {
    max-width: 100%;
    white-space: normal;
  }
  .client-actions-cell {
    grid-column: 1 / -1;
  }
  .client-actions {
    justify-content: flex-end;
    border-top: 1px solid var(--ws-border);
    padding-top: 0.8rem;
  }
  .client-actions .client-action-primary {
    margin-right: auto;
  }
}
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
</style>
