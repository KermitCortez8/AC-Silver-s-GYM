/** Ensambla módulos con estado acotado y capacidades explícitas. */
import { createClientsModule } from '../modules/clients.js';
import { createSchedulesModule } from '../modules/schedules.js';
import { createMembershipsModule } from '../modules/memberships.js';
import { createDashboardModule } from '../modules/dashboard.js';
import { createSynchronizationModule } from '../modules/synchronization.js';
import { createStoreModule } from '../modules/store.js';
import { createAttendanceModule } from '../modules/attendance.js';
import { createUsersModule } from '../modules/users.js';
import { createInventoryModule } from '../modules/inventory.js';
import { getApplicationServices } from '../ports/services.js';
import { createBackendGateway } from './backendGateway.js';

export const createGymModules = (state, repositories, services = getApplicationServices()) => {
  const apiBase = services.config.app.authApiBaseUrl || '/api';
  const dashboard = createDashboardModule(Object.freeze({
    pinia: services.pinia,
    apiBase,
    attendance: state.attendance,
    authStore: state.authStore,
    gymSettings: state.gymSettings,
    inventory: state.inventory,
    members: state.members
  }), repositories.gymSettings);
  const clients = createClientsModule(Object.freeze({
    pinia: services.pinia,
    apiBase,
    attendance: state.attendance,
    attendancePasses: state.attendancePasses,
    authStore: state.authStore,
    fetchFromBackend: (...args) => synchronization.fetchFromBackend(...args),
    get generation() { return state.generation; },
    getPlanById: (...args) => memberships.getPlanById(...args),
    members: state.members,
    normalizeLookupEmail: dashboard.normalizeLookupEmail,
    resourceErrors: state.resourceErrors,
    syncError: state.syncError
  }), repositories.clients);
  const memberships = createMembershipsModule(Object.freeze({
    pinia: services.pinia,
    apiBase,
    authStore: state.authStore,
    fetchFromBackend: (...args) => synchronization.fetchFromBackend(...args),
    get generation() { return state.generation; },
    logMemberEvent: clients.logMemberEvent,
    memberById: clients.memberById,
    members: state.members,
    mergeClient: clients.mergeClient,
    planCatalog: state.planCatalog,
    promotions: state.promotions,
    resourceErrors: state.resourceErrors,
    syncError: state.syncError
  }), repositories.memberships);
  const attendance = createAttendanceModule(Object.freeze({
    pinia: services.pinia,
    apiBase,
    attendance: state.attendance,
    attendancePasses: state.attendancePasses,
    authStore: state.authStore,
    isMembershipActive: memberships.isMembershipActive,
    memberById: clients.memberById,
    memberByInternalCode: clients.memberByInternalCode,
    members: state.members,
    normalizeLookupEmail: dashboard.normalizeLookupEmail
  }), repositories.attendance);
  const inventory = createInventoryModule(Object.freeze({
    pinia: services.pinia,
    apiBase,
    authStore: state.authStore,
    fetchFromBackend: (...args) => synchronization.fetchFromBackend(...args),
    get generation() { return state.generation; },
    inventory: state.inventory,
    inventoryMovements: state.inventoryMovements,
    resourceErrors: state.resourceErrors,
    syncError: state.syncError
  }), repositories.inventory);
  const store = createStoreModule(Object.freeze({
    pinia: services.pinia,
    apiBase,
    authStore: state.authStore,
    cart: state.cart,
    fetchFromBackend: (...args) => synchronization.fetchFromBackend(...args),
    get generation() { return state.generation; },
    productos_tienda: state.productos_tienda,
    resourceErrors: state.resourceErrors,
    storeOrders: state.storeOrders,
    syncError: state.syncError
  }), repositories.store);
  const users = createUsersModule(Object.freeze({
    pinia: services.pinia,
    apiBase,
    authStore: state.authStore,
    users: state.users
  }), repositories.users);
  const schedules = createSchedulesModule(Object.freeze({
    pinia: services.pinia,
    get activeSyncs() { return state.activeSyncs; },
    set activeSyncs(value) { state.activeSyncs = value; },
    apiBase,
    authStore: state.authStore,
    enrollments: state.enrollments,
    get generation() { return state.generation; },
    isSyncing: state.isSyncing,
    logMemberEvent: clients.logMemberEvent,
    memberById: clients.memberById,
    members: state.members,
    resourceErrors: state.resourceErrors,
    routines: state.routines,
    schedule: state.schedule,
    serviceSchedules: state.serviceSchedules,
    syncError: state.syncError,
    trainerOverview: state.trainerOverview,
    trainerOverviewCache: state.trainerOverviewCache
  }), repositories.schedules);
  const synchronization = createSynchronizationModule(Object.freeze({
    pinia: services.pinia,
    apiBase,
    get activeSyncs() { return state.activeSyncs; },
    set activeSyncs(value) { state.activeSyncs = value; },
    authStore: state.authStore,
    get errorScope() { return state.errorScope; },
    set errorScope(value) { state.errorScope = value; },
    fetchTrainerOverview: schedules.fetchTrainerOverview,
    get generation() { return state.generation; },
    inventory: state.inventory,
    isSyncing: state.isSyncing,
    members: state.members,
    membershipPayments: state.membershipPayments,
    pendingSyncs: state.pendingSyncs,
    planCatalog: state.planCatalog,
    refreshAttendanceFromBackend: attendance.refreshAttendanceFromBackend,
    refreshEnrollmentsFromBackend: schedules.refreshEnrollmentsFromBackend,
    refreshGymSettingsFromBackend: dashboard.refreshGymSettingsFromBackend,
    refreshInventoryMovementsFromBackend: inventory.refreshInventoryMovementsFromBackend,
    refreshPromotionsFromBackend: memberships.refreshPromotionsFromBackend,
    refreshRoutinesFromBackend: schedules.refreshRoutinesFromBackend,
    refreshServiceSchedulesFromBackend: schedules.refreshServiceSchedulesFromBackend,
    refreshStoreOrdersFromBackend: store.refreshStoreOrdersFromBackend,
    refreshStoreProductsFromBackend: store.refreshStoreProductsFromBackend,
    resourceCache: state.resourceCache,
    resourceErrors: state.resourceErrors,
    schedule: state.schedule,
    sectionSyncs: state.sectionSyncs,
    syncError: state.syncError,
    get syncScope() { return state.syncScope; },
    set syncScope(value) { state.syncScope = value; },
    users: state.users
  }), createBackendGateway(services));
  return Object.freeze({ dashboard, clients, memberships, attendance, inventory, store, users, schedules, synchronization });
};
