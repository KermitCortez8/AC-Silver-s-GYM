/** Estado y operaciones del módulo synchronization. */
import { normalizeBackendClientToMember, normalizeUser, normalizePlanFromBackend } from '../../domain/utils/gymRules.js';
import { APP_CONFIG } from '../services/appResources.js';
import { authHeaders, parseError, apiGet } from '../services/backendGateway.js';
import { syncResources } from '../services/syncResources.js';

export const createSynchronizationModule = (ctx) => {
  const apiBase = APP_CONFIG.authApiBaseUrl || '/api';

  const _authHeaders = () => authHeaders(ctx.authStore.token);

  const readBackendError = async (response, fallbackMessage) => {
    const error = await parseError(response);
    return error.message || fallbackMessage;
  };

  const fetchFromBackend = ({ force = false, section = 'all' } = {}) => {
    if (!ctx.authStore.token) return Promise.resolve();
    const scope = `${ctx.authStore.token}|${ctx.authStore.userRole}`;
    const generation = ctx.generation;
    const assertCurrent = () => {
      if (generation !== ctx.generation) throw new Error('La sesión ha cambiado.');
    };
    ctx.syncScope = scope;
    if (scope !== ctx.errorScope) {
      ctx.errorScope = scope;
      ctx.resourceErrors.clear();
      ctx.syncError.value = '';
    }
    ctx.activeSyncs += 1;
    ctx.sectionSyncs.value[section] = (ctx.sectionSyncs.value[section] || 0) + 1;
    ctx.isSyncing.value = true;

    const sync = (async () => {
      const role = ctx.authStore.userRole || ctx.authStore.user?.role;
      const internal = ['admin', 'staff'].includes(role);
      const getList = async (path) => {
        assertCurrent();
        const data = await apiGet(path, ctx.authStore.token);
        if (!Array.isArray(data)) throw new Error('El servidor devolvió una lista de datos inválida.');
        return data;
      };
      const tasks = [];
      let clientsReady = Promise.resolve();
      if (internal) {
        tasks.push(['Clientes', () => clientsReady = (async () => {
          ctx.members.value = (await getList('/clientes')).map(normalizeBackendClientToMember);
        })()], ['Usuarios', async () => {
          ctx.users.value = (await getList('/usuarios')).map(normalizeUser);
        }]);
      } else if (role === 'user') {
        tasks.push(['Mi perfil', () => clientsReady = (async () => {
          ctx.members.value = [normalizeBackendClientToMember(await apiGet('/clientes/me', ctx.authStore.token))];
        })()]);
      }

      if (internal) tasks.push(['Inventario', async () => {
        ctx.inventory.value = (await getList('/inventario')).map((i) => ({
          id: `item-${i.id_item}`,
          inventoryCode: `ACT-${String(i.n_activo || i.id_item).padStart(4, '0')}`,
          n_activo: i.n_activo || i.id_item,
          name: i.nombre_item,
          category: i.tipo,
          quantity: i.cantidad_stock,
          minQuantity: Number(i.stock_minimo ?? 1),
          unidad_venta: i.unidad_venta || 'unidad',
          precio_venta: Number(i.precio_venta ?? 0),
          location: i.ubicacion || 'Almacén',
          status: i.estado || '',
          observations: i.observaciones || '',
        }));
      }],
        ['Movimientos', ctx.refreshInventoryMovementsFromBackend]);
      tasks.push(['Productos', ctx.refreshStoreProductsFromBackend],
        ['Pedidos', ctx.refreshStoreOrdersFromBackend],
        ['Planes', async () => {
          ctx.planCatalog.value = (await getList('/planes-membresia')).map(normalizePlanFromBackend);
        }],
        ['Promociones', ctx.refreshPromotionsFromBackend]);

      if (internal) {
        tasks.push(['Pagos de membresías', async () => {
          ctx.membershipPayments.value = await getList('/pagos/membresias');
        }], ['Configuración', ctx.refreshGymSettingsFromBackend], ['Horarios', async () => {
          ctx.schedule.value = (await getList('/gym/horarios')).map((h) => ({
            ...h,
            capacidad_maxima: Number(h.capacidad_maxima ?? 1),
            cupos_usados: Number(h.cupos_usados ?? 1),
          }));
        }]);
      }
      if (internal || role === 'user') {
        tasks.push(['Horarios por servicio', ctx.refreshServiceSchedulesFromBackend],
          ['Matrículas', ctx.refreshEnrollmentsFromBackend]);
      }
      if (internal || role === 'trainer') tasks.push(['Rutinas', ctx.refreshRoutinesFromBackend]);
      if (role === 'trainer') tasks.push(['Supervisión', () => ctx.fetchTrainerOverview({ force })]);
      if (role === 'admin' || role === 'user') tasks.push(['Asistencias', async () => {
        // La normalización de asistencias necesita los nombres de clientes.
        await clientsReady.catch(() => { });
        assertCurrent();
        await ctx.refreshAttendanceFromBackend();
      }]);

      const sectionResources = {
        clients: ['Clientes', 'Mi perfil', 'Planes', 'Promociones'],
        users: ['Usuarios'],
        plans: ['Planes'],
        schedules: ['Horarios por servicio', 'Rutinas'],
        inventory: ['Inventario', 'Movimientos'],
        store: ['Productos', 'Inventario', 'Pedidos', 'Clientes'],
        orders: ['Pedidos', 'Clientes'],
        promotions: ['Promociones', 'Planes', 'Clientes'],
        payments: ['Pagos de membresías'],
        enrollment: ['Clientes', 'Mi perfil', 'Horarios por servicio', 'Matrículas'],
        attendance: ['Clientes', 'Matrículas', 'Asistencias'],
        trainer: ['Supervisión'],
        dashboard: ['Clientes', 'Mi perfil', 'Inventario', 'Horarios por servicio', 'Matrículas', 'Asistencias'],
      };
      const labels = sectionResources[section];
      if (section !== 'all' && !labels) throw new Error('Sección de datos desconocida.');
      const selectedTasks = labels ? tasks.filter(([label]) => labels.includes(label) &&
        !(['dashboard', 'store'].includes(section) && label === 'Inventario' && !internal)) : tasks;
      await syncResources(selectedTasks.map(([label, load]) => [label, async () => {
        try {
          assertCurrent();
          await ctx.resourceCache.load(scope, label, () => { assertCurrent(); return load(); }, { force });
          if (scope === ctx.errorScope && generation === ctx.generation) ctx.resourceErrors.delete(label);
        } catch (error) {
          if (scope === ctx.errorScope && generation === ctx.generation) ctx.resourceErrors.set(label, `${label}: ${error.message || 'No se pudieron cargar los datos.'}`);
          throw error;
        } finally {
          if (scope === ctx.errorScope && generation === ctx.generation) ctx.syncError.value = [...ctx.resourceErrors.values()].join(' ');
        }
      }]));
    })().finally(() => {
      if (generation !== ctx.generation) return;
      ctx.activeSyncs -= 1;
      ctx.sectionSyncs.value[section] -= 1;
      ctx.isSyncing.value = ctx.activeSyncs > 0;
      ctx.pendingSyncs.delete(sync);
    });
    ctx.pendingSyncs.add(sync);
    return sync;
  };

  return { apiBase, _authHeaders, readBackendError, fetchFromBackend };
};
