import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/authStore';

// Vistas
import LoginView from '../views/LoginView.vue';
import AdminDashboard from '../views/AdminDashboard.vue';
import UserDashboard from '../views/UserDashboard.vue';
import LandingView from '../views/LandingView.vue';
import RegisterView from '../views/RegisterView.vue';
import PaymentView from '../views/PaymentView.vue';
import HomeView from '../views/HomeView.vue';
import ClientsView from '../views/ClientsView.vue';
import UsersView from '../views/UsersView.vue';
import AttendanceView from '../views/AttendanceView.vue';
import ServiceSchedulesView from '../views/ServiceSchedulesView.vue';
import EnrollmentView from '../views/EnrollmentView.vue';
import InventoryView from '../views/InventoryView.vue';
import StoreView from '../views/StoreView.vue';
import ScheduleView from '../views/ScheduleView.vue';
import UserAttendanceView from '../views/UserAttendanceView.vue';
import AuthCallbackView from '../views/AuthCallbackView.vue';

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
        path: 'store',
        name: 'Store',
        component: StoreView,
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
        path: 'schedule',
        name: 'Schedule',
        component: ScheduleView,
      },
      {
        path: 'enrollment',
        name: 'UserEnrollment',
        component: EnrollmentView,
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
});

// Guard de rutas
router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  // Inicializar autenticación si no está hecho
  if (!authStore.isInitialized) {
    await authStore.initializeAuth();
  }

  if (to.path === '/' && authStore.isAuthenticated) {
    return authStore.isAdmin ? '/admin/dashboard' : '/user/dashboard';
  }

  // Verificar si la ruta requiere autenticación
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return '/login';
  }

  // Verificar roles
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return '/';
  }

  // Si está autenticado y va a login, redirigir al dashboard
  if (authStore.isAuthenticated && to.path === '/login') {
    return authStore.isAdmin ? '/admin' : '/user';
  }

  return true;
});

export default router;
