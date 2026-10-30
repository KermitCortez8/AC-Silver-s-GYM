import { prepareNavigationSession } from '../../application/services/moduleNavigation.js';

// Mantiene la sesión y los permisos de navegación en una sola política.
export const createSessionGuard = (getAuth) => async (to, from) => {
  const authStore = getAuth();

  await prepareNavigationSession(authStore, to, from);

  // Verificar si la ruta requiere autenticación
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    if (authStore.sessionErrorCode === 'membership_expired') {
      return { name: 'Login', query: { reason: 'membership_expired' } };
    }
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
};
