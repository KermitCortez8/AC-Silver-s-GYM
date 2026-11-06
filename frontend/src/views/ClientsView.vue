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
          <SearchInput
            v-model="search"
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

    <ClientEditorDialog v-bind="clientEditorProps" />

    <ClientDetailsDialog
      :can-pay-client-with-stripe="canPayClientWithStripe"
      :client-membership-group="clientMembershipGroup"
      :client-membership-label="clientMembershipLabel"
      :close-details="closeDetails"
      :get-plan-price="getPlanPrice"
      :is-active-status="isActiveStatus"
      :is-details-open="isDetailsOpen"
      :mark-as-paid-manual="markAsPaidManual"
      :membership-badge-class="membershipBadgeClass"
      :notifying-client-id="notifyingClientId"
      :confirming-payment-client-id="confirmingPaymentClientId"
      :pay-with-stripe="payWithStripe"
      :paying-client-id="payingClientId"
      :payment-error="paymentError"
      :request-activation="requestActivation"
      :retry-activation-email="retryActivationEmail"
      :viewing-client="viewingClient"
    />
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
import SearchInput from '../components/SearchInput.vue';
import ClientDetailsDialog from '../components/clients/ClientDetailsDialog.vue';
import ClientEditorDialog from '../components/clients/ClientEditorDialog.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';
import { canPayClientWithStripe } from '../../domain/utils/adminClientPayment.js';
import { clientMembershipGroup, clientMembershipLabel } from '../../domain/utils/clientDirectory.js';
import {
  BadgeCheck,
  ChevronLeft,
  ChevronRight,
  CircleCheck,
  Clock3,
  CreditCard,
  Info,
  LoaderCircle,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  SearchX,
  Trash2,
  Users,
  X,
} from 'lucide-vue-next';
import { useClientDirectory } from '../composables/clients/useClientDirectory.js';

const {
  gymStore, authStore, route, router, clients,
  search, statusFilter, planFilter, paymentFilter, sortOrder,
  currentPage, isLoading, isDetailsOpen, viewingClient, feedbackMessage,
  feedbackTone, normalizeStatus, displayMembershipStatus, isActiveStatus, isPendingMembership,
  getPlanPrice, filteredClients, pagination, hasFilters, planOptions,
  activeClients, readyToActivateClients, unpaidClients, statusFilters, resetFilters,
  membershipBadgeClass, initials, feedbackToneClass, refreshClients, openDetails,
  closeDetails, confirmDelete, activatingClientId, pendingActivation, activationError,
  notifyingClientId, payingClientId, confirmingPaymentClientId, paymentError, requestActivation,
  cancelActivation, notificationMessage, retryActivationEmail, markAsPaidManual, activateMembership,
  payWithStripe, initializeDirectory, fieldErrors, validateField, revalidateField,
  editingId, isEditorOpen, savingClient, submitError, editingClient,
  editingMembershipLabel, editingNeedsActivation, editingExpired, form, availablePromotions,
  estimatedCharge, resetForm, openNewClient, closeEditor, editClient,
  handleSubmit, clientEditorProps,
} = useClientDirectory();
</script>

<style scoped src="../styles/clients-view.css"></style>
