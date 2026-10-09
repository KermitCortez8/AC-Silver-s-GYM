export const MAX_MODULE_WAIT_MS = 3_000;
const MODULE_FADE_OUT_MS = 220;

// La navegación termina al montar la vista. Sus datos tienen indicadores propios;
// una consulta pendiente en otra sección no debe bloquear la pantalla actual.
export const createModuleLoader = ({
  onChange,
  schedule = setTimeout,
  cancel = clearTimeout,
} = {}) => {
  let timer = null;
  let active = false;
  let revision = 0;

  const stop = () => {
    if (timer !== null) cancel(timer);
    timer = null;
    if (active) onChange(false);
    active = false;
  };
  return {
    start() {
      if (timer !== null) cancel(timer);
      const current = ++revision;
      active = true;
      onChange(true);
      // Reserva la animación de salida para que la espera completa no exceda 3s.
      timer = schedule(() => {
        if (current === revision) stop();
      }, MAX_MODULE_WAIT_MS - MODULE_FADE_OUT_MS);
      return current;
    },
    complete(current) {
      if (current !== revision) return;
      stop();
    },
    stop,
    dispose() {
      revision += 1;
      stop();
    },
  };
};

// Una sesión interna ya validada no retiene cada cambio de sección en /auth/me.
// La comprobación sigue en segundo plano; la entrada inicial sí espera al servidor.
export const prepareNavigationSession = async (auth, to, from) => {
  const needsCheck = !auth.isInitialized || (auth.isAuthenticated &&
    (to.meta.requiresAuth || to.path === '/' || to.path === '/login'));
  if (!needsCheck) return;

  const withinPanel = auth.isInitialized && auth.isAuthenticated && (
    (auth.isAdmin && from.meta.requiresAdmin && to.meta.requiresAdmin) ||
    (auth.isTrainer && from.meta.requiresTrainer && to.meta.requiresTrainer)
  );
  const check = auth.initializeAuth();
  if (withinPanel) {
    void check.catch(() => {});
  } else {
    await check;
  }
};

export const sectionForPath = (path) => {
  const [, panel, section] = path.split('/');
  if (panel === 'trainer') return 'trainer';
  if (panel === 'admin') return ({
    dashboard: 'dashboard', clients: 'clients', users: 'users',
    plans: 'plans', promotions: 'promotions', inventory: 'inventory',
    store: 'store', orders: 'orders', settings: 'settings',
    'service-schedules': 'schedules', enrollment: 'enrollment',
    attendance: 'attendance',
  })[section] || 'dashboard';
  return 'all';
};
