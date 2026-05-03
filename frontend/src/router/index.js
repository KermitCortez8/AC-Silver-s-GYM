import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/authStore';

// Vistas
import LoginView from '../views/LoginView.vue';
import AdminDashboard from '../views/AdminDashboard.vue';
import UserDashboard from '../views/UserDashboard.vue';
import HomeView from '../views/HomeView.vue';
import UsersView from '../views/UsersView.vue';
import AttendanceView from '../views/AttendanceView.vue';
import InventoryView from '../views/InventoryView.vue';
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
    component: HomeView,
    meta: { requiresAuth: true },
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
        path: 'attendance',
        name: 'Attendance',
        component: AttendanceView,
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: InventoryView,
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
        path: 'schedule',
        name: 'Schedule',
        component: ScheduleView,
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
