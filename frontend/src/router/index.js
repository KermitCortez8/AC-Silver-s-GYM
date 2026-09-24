import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/authStore';

// Cada vista se descarga una vez, cuando se necesita.
const LoginView = () => import('../views/LoginView.vue');
const AdminDashboard = () => import('../views/AdminDashboard.vue');
const TrainerDashboard = () => import('../views/TrainerDashboard.vue');
const UserDashboard = () => import('../views/UserDashboard.vue');
const LandingView = () => import('../views/LandingView.vue');
const NosotrosView = () => import('../views/NosotrosView.vue');
const RegisterView = () => import('../views/RegisterView.vue');
const PaymentView = () => import('../views/PaymentView.vue');
const HomeView = () => import('../views/HomeView.vue');
const ClientsView = () => import('../views/ClientsView.vue');
const UsersView = () => import('../views/UsersView.vue');
const AttendanceView = () => import('../views/AttendanceView.vue');
const ServiceSchedulesView = () => import('../views/ServiceSchedulesView.vue');
const EnrollmentView = () => import('../views/EnrollmentView.vue');
const InventoryView = () => import('../views/InventoryView.vue');
const InventoryMovementsView = () => import('../views/InventoryMovementsView.vue');
const GymSettingsView = () => import('../views/GymSettingsView.vue');
const MembershipPlansView = () => import('../views/MembershipPlansView.vue');
const PromotionsView = () => import('../views/PromotionsView.vue');
const StoreView = () => import('../views/StoreView.vue');
const StorePaymentView = () => import('../views/StorePaymentView.vue');
const OrdersView = () => import('../views/OrdersView.vue');
const UserAttendanceView = () => import('../views/UserAttendanceView.vue');
const TrainerOverviewView = () => import('../views/TrainerOverviewView.vue');
const TrainerRoutinesView = () => import('../views/TrainerRoutinesView.vue');
const TrainerRoutineMonitorView = () => import('../views/TrainerRoutineMonitorView.vue');
const AuthCallbackView = () => import('../views/AuthCallbackView.vue');

const routes = [
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: AuthCallbackView,
    meta: { requiresAuth: false },
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Home',
    component: LandingView,
    meta: { requiresAuth: false },
  },
  {
    path: '/tp-remix',
    name: 'TpRemix',
    component: () => import('../views/TpRemixView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/nosotros',
    name: 'Nosotros',
    component: NosotrosView,
    meta: { requiresAuth: false },
  },
  {
    path: '/registro',
    name: 'Register',
    component: RegisterView,
    meta: { requiresAuth: false },
  },
  {
    path: '/registro/pago/:idCliente',
    name: 'Payment',
    component: PaymentView,
    meta: { requiresAuth: false },
  },
  {
    path: '/admin',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard',
      },
      {
        path: 'dashboard',
        name: 'AdminHome',
        component: HomeView,
      },
      {
        path: 'users',
        name: 'Users',
        component: UsersView,
      },
      {
        path: 'clients',
        name: 'Clients',
        component: ClientsView,
      },
      {
        path: 'attendance',
        name: 'Attendance',
        component: AttendanceView,
        meta: { requiresAdministrator: true },
      },
      {
        path: 'service-schedules',
        name: 'ServiceSchedules',
        component: ServiceSchedulesView,
      },
      {
        path: 'enrollment',
        name: 'AdminEnrollment',
        component: EnrollmentView,
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: InventoryView,
      },
      {
        path: 'inventory/movements',
        name: 'InventoryMovements',
        component: InventoryMovementsView,
      },
      {
        path: 'plans',
        name: 'MembershipPlans',
        component: MembershipPlansView,
      },
      {
        path: 'promotions',
        name: 'Promotions',
        component: PromotionsView,
      },
      {
        path: 'settings',
        name: 'GymSettings',
        component: GymSettingsView,
      },
      {
        path: 'store',
        name: 'Store',
        component: StoreView,
      },
      {
        path: 'orders',
        name: 'Orders',
        component: OrdersView,
      },
    ],
  },
  {
    path: '/trainer',
    component: TrainerDashboard,
    meta: { requiresAuth: true, requiresTrainer: true },
    children: [
      {
        path: '',
        redirect: '/trainer/dashboard',
      },
      {
        path: 'dashboard',
        name: 'TrainerHome',
        component: TrainerOverviewView,
      },
      {
        path: 'routines',
        name: 'TrainerRoutines',
        component: TrainerRoutinesView,
      },
      {
        path: 'routine-monitor',
        name: 'TrainerRoutineMonitor',
        component: TrainerRoutineMonitorView,
      },
    ],
  },
  {
    path: '/user',
    component: UserDashboard,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/user/dashboard',
      },
      {
        path: 'dashboard',
        name: 'UserHome',
        component: HomeView,
      },
      {
        path: 'store',
        name: 'UserStore',
        component: StoreView,
      },
      {
        path: 'store/payment',
        name: 'UserStorePayment',
        component: StorePaymentView,
      },
      {
        path: 'schedule',
        name: 'Schedule',
        component: EnrollmentView,
      },
      {
        path: 'enrollment',
        name: 'UserEnrollment',
        redirect: '/user/schedule',
      },
      {
        path: 'attendance',
        name: 'UserAttendance',
        component: UserAttendanceView,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' };
    }
    return { top: 0 };
  },
});

// Guard de rutas
router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  // Valida al entrar y reutiliza la comprobación durante 30 segundos.
  // El backend sigue comprobando la sesión y los permisos en cada operación.
  const needsSessionCheck = authStore.isAuthenticated &&
    (to.meta.requiresAuth || to.path === '/' || to.path === '/login');
  if (!authStore.isInitialized || needsSessionCheck) {
    await authStore.initializeAuth();
  }

  if (to.path === '/' && authStore.isAuthenticated) {
    return authStore.dashboardPath;
  }

  // Verificar si la ruta requiere autenticación
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return '/login';
  }

  // Verificar roles
  if (to.meta.requiresAdministrator && authStore.userRole !== 'admin') {
    return authStore.dashboardPath;
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return '/';
  }

  if (to.meta.requiresTrainer && !authStore.isTrainer) {
    return '/';
  }

  // Si está autenticado y va a login, redirigir al dashboard
  if (authStore.isAuthenticated && to.path === '/login') {
    return authStore.dashboardPath;
  }

  return true;
});

export default router;
