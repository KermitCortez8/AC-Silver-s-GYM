import { onScopeDispose, ref } from 'vue';
import { usePublicCatalog } from '../../../application/services/publicCatalog.js';

/** Catálogo remoto compartido por altas públicas y formularios administrativos. */
export const useClientMembershipCatalog = ({ includeHistorical = false } = {}) => {
  const { loadClientMembershipCatalog } = usePublicCatalog();
  const plans = ref([]), promotions = ref([]);
  const catalogLoading = ref(false), catalogReady = ref(false), catalogError = ref('');
  let pending = null, disposed = false;
  onScopeDispose(() => { disposed = true; });

  const loadCatalog = () => {
    if (pending) return pending;
    catalogLoading.value = true;
    catalogReady.value = false;
    catalogError.value = '';
    pending = (async () => {
      try {
        const catalog = await loadClientMembershipCatalog({ includeHistorical });
        if (disposed) return false;
        plans.value = catalog.plans;
        promotions.value = catalog.promotions;
        catalogReady.value = true;
        return true;
      } catch (error) {
        if (!disposed) catalogError.value = error?.message || 'No se pudieron cargar los planes y promociones.';
        return false;
      } finally {
        if (!disposed) catalogLoading.value = false;
        pending = null;
      }
    })();
    return pending;
  };
  return { plans, promotions, catalogLoading, catalogReady, catalogError, loadCatalog };
};
