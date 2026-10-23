/** Fachada estable del gimnasio; las operaciones se mantienen por módulo. */
import { defineStore } from 'pinia';
import { createGymState } from '../modules/state.js';
import { createAttendanceModule } from '../modules/attendance.js';
import { createDashboardModule } from '../modules/dashboard.js';
import { createMembershipsModule } from '../modules/memberships.js';
import { createInventoryModule } from '../modules/inventory.js';
import { createClientsModule } from '../modules/clients.js';
import { createSchedulesModule } from '../modules/schedules.js';
import { createUsersModule } from '../modules/users.js';
import { createStoreModule } from '../modules/store.js';
import { createSynchronizationModule } from '../modules/synchronization.js';

export const useGymStore = defineStore('gym', () => {
  const context = createGymState();
  Object.assign(context, createAttendanceModule(context));
  Object.assign(context, createDashboardModule(context));
  Object.assign(context, createMembershipsModule(context));
  Object.assign(context, createInventoryModule(context));
  Object.assign(context, createClientsModule(context));
  Object.assign(context, createSchedulesModule(context));
  Object.assign(context, createUsersModule(context));
  Object.assign(context, createStoreModule(context));
  Object.assign(context, createSynchronizationModule(context));
  context.pruneExpiredAttendancePasses();
  return {
    syncError: context.syncError,
    isSyncing: context.isSyncing,
    isSectionSyncing: context.isSectionSyncing,
    members: context.members,
    users: context.users,
    attendance: context.attendance,
    attendancePasses: context.attendancePasses,
    planCatalog: context.planCatalog,
    promotions: context.promotions,
    routines: context.routines,
    inventory: context.inventory,
    inventoryMovements: context.inventoryMovements,
    productos_tienda: context.productos_tienda,
    storeOrders: context.storeOrders,
    cart: context.cart,
    schedule: context.schedule,
    serviceSchedules: context.serviceSchedules,
    enrollments: context.enrollments,
    trainerOverview: context.trainerOverview,
    gymSettings: context.gymSettings,
    membershipPayments: context.membershipPayments,
    stats: context.stats,
    recentAttendance: context.recentAttendance,
    attendanceAnalytics: context.attendanceAnalytics,
    activePlans: context.activePlans,
    activePromotions: context.activePromotions,
    membershipAlerts: context.membershipAlerts,
    lowStockInventory: context.lowStockInventory,
    cartTotal: context.cartTotal,
    searchMembers: context.searchMembers,
    getPlanById: context.getPlanById,
    getPromotionById: context.getPromotionById,
    isMembershipActive: context.isMembershipActive,
    isMembershipExpiringSoon: context.isMembershipExpiringSoon,
    calculatePlanCharge: context.calculatePlanCharge,
    upsertPlan: context.upsertPlan,
    deletePlan: context.deletePlan,
    upsertPromotion: context.upsertPromotion,
    deletePromotion: context.deletePromotion,
    upsertRutina: context.upsertRutina,
    assignPlanToMember: context.assignPlanToMember,
    renewMembership: context.renewMembership,
    attendanceByMemberRange: context.attendanceByMemberRange,
    memberByInternalCode: context.memberByInternalCode,
    recordAttendanceByCode: context.recordAttendanceByCode,
    recordAttendanceByDni: context.recordAttendanceByDni,
    memberSchedules: context.memberSchedules,
    assignMemberSchedule: context.assignMemberSchedule,
    userAttendance: context.userAttendance,
    memberByEmail: context.memberByEmail,
    memberById: context.memberById,
    activeAttendancePass: context.activeAttendancePass,
    createAttendancePass: context.createAttendancePass,
    redeemAttendancePass: context.redeemAttendancePass,
    upsertMember: context.upsertMember,
    deleteMember: context.deleteMember,
    upsertClient: context.upsertClient,
    deleteClient: context.deleteClient,
    recordAttendance: context.recordAttendance,
    upsertInventoryItem: context.upsertInventoryItem,
    deleteInventoryItem: context.deleteInventoryItem,
    upsertProductoTienda: context.upsertProductoTienda,
    deleteProductoTienda: context.deleteProductoTienda,
    addToCart: context.addToCart,
    removeFromCart: context.removeFromCart,
    updateCartQuantity: context.updateCartQuantity,
    clearCart: context.clearCart,
    createStoreOrder: context.createStoreOrder,
    upsertUser: context.upsertUser,
    deleteUser: context.deleteUser,
    fetchFromBackend: context.fetchFromBackend,
    refreshStoreProductsFromBackend: context.refreshStoreProductsFromBackend,
    refreshStoreOrdersFromBackend: context.refreshStoreOrdersFromBackend,
    updateStoreOrderStatus: context.updateStoreOrderStatus,
    refreshAttendanceFromBackend: context.refreshAttendanceFromBackend,
    refreshServiceSchedulesFromBackend: context.refreshServiceSchedulesFromBackend,
    refreshRoutinesFromBackend: context.refreshRoutinesFromBackend,
    refreshPromotionsFromBackend: context.refreshPromotionsFromBackend,
    refreshGymSettingsFromBackend: context.refreshGymSettingsFromBackend,
    updateGymSettings: context.updateGymSettings,
    refreshInventoryMovementsFromBackend: context.refreshInventoryMovementsFromBackend,
    upsertServiceSchedule: context.upsertServiceSchedule,
    deleteServiceSchedule: context.deleteServiceSchedule,
    refreshEnrollmentsFromBackend: context.refreshEnrollmentsFromBackend,
    refreshScheduleClientsFromBackend: context.refreshScheduleClientsFromBackend,
    fetchTrainerOverview: context.fetchTrainerOverview,
    upsertTrainerRoutine: context.upsertTrainerRoutine,
    assignTrainerRoutine: context.assignTrainerRoutine,
    fetchTrainerClientRoutines: context.fetchTrainerClientRoutines,
    markTrainerRoutineProgress: context.markTrainerRoutineProgress,
    enrollSchedule: context.enrollSchedule,
    deleteEnrollment: context.deleteEnrollment,
    upsertClienteToServer: context.upsertClienteToServer,
    registerClienteMembresiaToServer: context.registerClienteMembresiaToServer,
    registerPublicClient: context.registerPublicClient,
    activateClientMembership: context.activateClientMembership,
    checkinByDniServer: context.checkinByDniServer,
    checkinByIdServer: context.checkinByIdServer,
    registerAttendanceEntry: context.registerAttendanceEntry,
    registerAttendanceExit: context.registerAttendanceExit,
    updateAttendanceRecord: context.updateAttendanceRecord,
    deleteAttendanceRecord: context.deleteAttendanceRecord,
    upsertInventoryToServer: context.upsertInventoryToServer,
    upsertUserToServer: context.upsertUserToServer,
    deleteUserFromServer: context.deleteUserFromServer,
    registrarMovimientoToServer: context.registrarMovimientoToServer,
    confirmarPagoEfectivo: context.confirmarPagoEfectivo,
    updateInventoryMovement: context.updateInventoryMovement,
    createStoreCheckout: context.createStoreCheckout,
    confirmStoreCheckoutReturn: context.confirmStoreCheckoutReturn,
    cancelStoreCheckout: context.cancelStoreCheckout,
  };
});
