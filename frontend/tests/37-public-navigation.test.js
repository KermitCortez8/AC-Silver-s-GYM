import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createMemoryHistory, createRouter } from 'vue-router';
import { createSessionGuard } from '../src/presentation/router/sessionGuard.js';

const navigation = (role, initializeAuth = async () => {}) => {
  const auth = {
    isInitialized: true,
    isAuthenticated: Boolean(role),
    userRole: role,
    isAdmin: ['admin', 'staff'].includes(role),
    isTrainer: role === 'trainer',
    dashboardPath: ['admin', 'staff'].includes(role) ? '/admin/dashboard'
      : role === 'trainer' ? '/trainer/dashboard' : '/user/dashboard',
    sessionErrorCode: '',
    initializeAuth,
  };
  const view = { render: () => null };
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: view },
      { path: '/nosotros', component: view },
      { path: '/login', name: 'Login', component: view },
      { path: '/admin/dashboard', component: view, meta: { requiresAuth: true, requiresAdmin: true } },
      { path: '/admin/attendance', component: view, meta: { requiresAuth: true, requiresAdministrator: true } },
      { path: '/trainer/dashboard', component: view, meta: { requiresAuth: true, requiresTrainer: true } },
      { path: '/user/dashboard', component: view, meta: { requiresAuth: true } },
    ],
  });
  router.beforeEach(createSessionGuard(() => auth));
  return { auth, router };
};

for (const role of ['admin', 'staff', 'trainer', 'user']) {
  test(`${role} puede regresar del panel a la landing y sus secciones sin cerrar sesión`, async () => {
    const { auth, router } = navigation(role);
    await router.push(auth.dashboardPath);
    await router.push('/');
    assert.equal(router.currentRoute.value.fullPath, '/');
    await router.push('/#membresias');
    assert.equal(router.currentRoute.value.fullPath, '/#membresias');
    await router.push('/nosotros');
    await router.push('/#servicios');
    assert.equal(router.currentRoute.value.fullPath, '/#servicios');
    assert.equal(auth.isAuthenticated, true);
    // El acceso explícito a la plataforma sigue recuperando el panel de la sesión.
    await router.push('/login');
    assert.equal(router.currentRoute.value.path, auth.dashboardPath);
  });
}

test('la landing también permite entrada directa con una sesión restaurada', async () => {
  let checks = 0;
  const { auth, router } = navigation('user', async () => { checks++; });
  auth.isInitialized = false;
  await router.push('/');
  assert.equal(checks, 1);
  assert.equal(router.currentRoute.value.path, '/');
  assert.equal(auth.isAuthenticated, true);
});

test('sin sesión se conserva el acceso público y se bloquean los paneles', async () => {
  const { router } = navigation(null);
  await router.push('/');
  assert.equal(router.currentRoute.value.path, '/');
  await router.push('/admin/dashboard');
  assert.equal(router.currentRoute.value.path, '/login');
});

test('una membresía vencida mantiene el motivo en login al intentar abrir el panel', async () => {
  const { auth, router } = navigation('user', async () => {
    auth.isAuthenticated = false;
    auth.sessionErrorCode = 'membership_expired';
  });
  await router.push('/user/dashboard');
  assert.equal(router.currentRoute.value.fullPath, '/login?reason=membership_expired');
  await router.push('/');
  assert.equal(router.currentRoute.value.path, '/');
});

test('visitar la landing no concede acceso a otros roles', async () => {
  const { router } = navigation('user');
  await router.push('/admin/dashboard');
  assert.equal(router.currentRoute.value.path, '/');
  await router.push('/trainer/dashboard');
  assert.equal(router.currentRoute.value.path, '/');

  const { router: staffRouter } = navigation('staff');
  await staffRouter.push('/admin/attendance');
  assert.equal(staffRouter.currentRoute.value.path, '/admin/dashboard');
});
