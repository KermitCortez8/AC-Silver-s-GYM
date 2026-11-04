import { computed, ref } from 'vue';
import { matchesSearch, sortRows } from '../../../domain/utils/inputRules.js';

/** Coordina el catálogo visible sin modificar el estado comercial de sus planes. */
export const usePlanDirectory = gymStore => {
  const plans = computed(() => gymStore.planCatalog);
  const search = ref('');
  const status = ref('all');
  const sort = ref('name');
  const loading = ref(false);
  const loadError = ref('');
  const activeCount = computed(() => plans.value.filter(plan => plan.active).length);
  const hasFilters = computed(() => Boolean(search.value || status.value !== 'all'));
  const filteredPlans = computed(() => {
    const rows = plans.value.filter(plan =>
      (status.value === 'all' || (status.value === 'active' ? plan.active : !plan.active))
      && matchesSearch(search.value, [plan.name, plan.description, plan.benefits, plan.duration]),
    );
    return sort.value === 'name'
      ? sortRows(rows, plan => plan.name)
      : sortRows(rows, plan => plan.price, sort.value === 'price-desc' ? 'desc' : 'asc', 'number');
  });
  const clearFilters = () => { search.value = ''; status.value = 'all'; };
  const loadPlans = async () => {
    if (loading.value) return;
    loading.value = true;
    loadError.value = '';
    try {
      await gymStore.fetchFromBackend({ section: 'plans' });
    } catch (error) {
      loadError.value = error instanceof Error ? error.message : 'No se pudieron cargar los planes.';
    } finally {
      loading.value = false;
    }
  };
  return { plans, search, status, sort, loading, loadError, activeCount, hasFilters, filteredPlans, clearFilters, loadPlans };
};
