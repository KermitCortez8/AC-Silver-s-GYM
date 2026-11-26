<template>
  <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
    <div>
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Estado</p>
      <h2 class="mt-2 text-2xl font-black text-white">Listado de inventario</h2>
    </div>
    <div class="flex flex-col items-end gap-1">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-2xl border border-white/10 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="!items.length || isExporting"
        @click="download"
      >
        <FileDown :size="16" aria-hidden="true" />
        {{ isExporting ? 'Generando…' : 'Descargar Excel' }}
      </button>
      <p v-if="exportError" role="alert" class="text-xs text-rose-300">{{ exportError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { FileDown } from 'lucide-vue-next';
import { exportToExcel, INVENTORY_EXCEL_COLUMNS, inventoryExcelRows } from '../../utils/excelExport.js';

// items: las filas que se ven con los filtros y el orden actuales.
const props = defineProps({ items: { type: Array, default: () => [] } });
const isExporting = ref(false);
const exportError = ref('');

const download = async () => {
  if (isExporting.value || !props.items.length) return;
  isExporting.value = true;
  exportError.value = '';
  try {
    await exportToExcel({
      sheetName: 'Inventario',
      title: 'Listado de inventario',
      columns: INVENTORY_EXCEL_COLUMNS,
      rows: inventoryExcelRows(props.items),
    }, 'inventario');
  } catch {
    exportError.value = 'No se pudo generar el Excel. Vuelve a intentarlo.';
  } finally {
    isExporting.value = false;
  }
};
</script>
