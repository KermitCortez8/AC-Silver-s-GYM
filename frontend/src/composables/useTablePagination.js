import { computed, ref, watch } from 'vue';

// Los filtros y totales usan toda la lista; solo se montan las filas de la página.
export const useTablePagination = (items, pageSize = 25) => {
  const page = ref(1);
  const pageCount = computed(() => Math.max(1, Math.ceil(items.value.length / pageSize)));
  watch(items, () => { page.value = 1; }, { flush: 'sync' });
  const pageItems = computed(() => {
    const start = (page.value - 1) * pageSize;
    return items.value.slice(start, start + pageSize);
  });
  return { page, pageCount, pageItems };
};
