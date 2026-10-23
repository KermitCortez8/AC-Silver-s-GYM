/** Estado y operaciones del módulo state. */
import { loadState } from '../../domain/utils/gymRules.js';
import { useAuthStore } from '../stores/authStore.js';
import { ref } from 'vue';
import { createResourceCache } from '../services/resourceCache.js';

export const createGymState = () => {
  const initialState = loadState();

  const authStore = useAuthStore();

  const planCatalog = ref(initialState.planCatalog);

  const promotions = ref(initialState.promotions);

  const members = ref(initialState.members);

  const users = ref(initialState.users);

  const attendance = ref(initialState.attendance);

  const attendancePasses = ref(initialState.attendancePasses || []);

  const inventory = ref(initialState.inventory);

  const inventoryMovements = ref(initialState.inventoryMovements || []);

  const productos_tienda = ref(initialState.productos_tienda);

  const storeOrders = ref(initialState.storeOrders);

  const cart = ref(initialState.cart);

  const routines = ref(initialState.routines);

  const schedule = ref(initialState.schedule);

  const serviceSchedules = ref(initialState.serviceSchedules);

  const enrollments = ref(initialState.enrollments);

  const trainerOverview = ref(initialState.trainerOverview);

  const gymSettings = ref(initialState.gymSettings);

  const membershipPayments = ref([]);

  const syncError = ref('');

  const isSyncing = ref(false);

  const sectionSyncs = ref({});

  const isSectionSyncing = (section) => Boolean(sectionSyncs.value[section] || sectionSyncs.value.all);

  const resourceCache = createResourceCache();

  const trainerOverviewCache = createResourceCache();

  const pendingSyncs = new Set();

  let syncScope = '';

  let activeSyncs = 0;

  let errorScope = '';

  const resourceErrors = new Map();

  const persist = () => {
    // Business data is persisted only through the backend, which writes to Supabase.
  };

  return { initialState, authStore, planCatalog, promotions, members, users, attendance, attendancePasses, inventory, inventoryMovements, productos_tienda, storeOrders, cart, routines, schedule, serviceSchedules, enrollments, trainerOverview, gymSettings, membershipPayments, syncError, isSyncing, sectionSyncs, isSectionSyncing, resourceCache, trainerOverviewCache, pendingSyncs, syncScope, activeSyncs, errorScope, resourceErrors, persist };
};
