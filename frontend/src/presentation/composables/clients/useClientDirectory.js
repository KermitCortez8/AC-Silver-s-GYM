import { feedbackClass as noticeClassFor } from '../../utils/feedback.js';
import { useClientMembershipActions } from './useClientMembershipActions.js';
import { useClientEditor } from './useClientEditor.js';
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useGymStore } from '../../../application/stores/gymStore';
import { useAuthStore } from '../../../application/stores/authStore';
import { clientMembershipGroup, filterClientDirectory, paginateClients } from '../../../domain/utils/clientDirectory.js';

/** Coordina los filtros del directorio y sus acciones de edición y membresía. */
export const useClientDirectory = () => {
  const gymStore = useGymStore();
  const authStore = useAuthStore();
  const route = useRoute();
  const router = useRouter();

  const clients = computed(() => gymStore.members);

  const search = ref(typeof route.query.search === 'string' ? route.query.search.slice(0, 30) : '');
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

  const isDetailsOpen = ref(false);
  const viewingClient = ref(null);
  const feedbackMessage = ref('');
  const feedbackTone = ref('info');

  const normalizeStatus = (value) =>
    String(value || '')
      .trim()
      .toUpperCase();

  const displayMembershipStatus = (client) =>
    normalizeStatus(client.membershipStatus || client.status || 'EN_TRAMITE');

  const isActiveStatus = (value) =>
    ['ACTIVO', 'ACTIVA'].includes(normalizeStatus(value));

  const isPendingMembership = (client) =>
    clientMembershipGroup(client) === 'pending';

  const getPlanPrice = (planName) => {
    const plan = gymStore.planCatalog.find((p) => p.name === planName);
    return plan ? Number(plan.price || 0) : 0;
  };

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
  const feedbackToneClass = computed(() => noticeClassFor(feedbackTone.value));
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

  const openDetails = (client) => {
    paymentError.value = '';
    viewingClient.value = client;
    isDetailsOpen.value = true;
  };

  const closeDetails = () => {
    isDetailsOpen.value = false;
    viewingClient.value = null;
  };

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

  const { activatingClientId, pendingActivation, activationError, notifyingClientId, payingClientId, confirmingPaymentClientId, paymentError, requestActivation, cancelActivation, notificationMessage, retryActivationEmail, markAsPaidManual, activateMembership, payWithStripe, initializeDirectory } = useClientMembershipActions({ gymStore, authStore, feedbackMessage, feedbackTone, viewingClient, route, router, refreshClients });
  const { clientEditorProps, fieldErrors, validateField, revalidateField, editingId, isEditorOpen, savingClient, submitError, editingClient, editingMembershipLabel, editingNeedsActivation, editingExpired, form, availablePromotions, estimatedCharge, resetForm, openNewClient, closeEditor, editClient, handleSubmit } = useClientEditor({ gymStore, clients, feedbackMessage, feedbackTone, resetFilters, sortOrder, openDetails, paymentError, normalizeStatus });
  onMounted(initializeDirectory);

  return {
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
  };
};
