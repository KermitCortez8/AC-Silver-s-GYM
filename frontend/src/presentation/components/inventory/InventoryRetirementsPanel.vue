<template>
  <section class="rounded-2xl border border-white/10 bg-white/5 p-6">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Historial</p>
        <h2 class="mt-2 text-2xl font-black text-white">Bajas de inventario</h2>
        <p class="mt-1 text-sm text-slate-400">Unidades con N° de activo dadas de baja y artículos retirados del inventario.</p>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-2xl border border-white/10 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="!filteredRows.length || isExporting"
        @click="download"
      >
        <FileDown :size="16" aria-hidden="true" />
        {{ isExporting ? 'Generando…' : 'Descargar Excel' }}
      </button>
    </div>

    <div class="mt-5 grid gap-3 sm:grid-cols-[1.5fr_1fr]">
      <div>
        <TableSearch
          v-model="nameFilter"
          label="Buscar bajas por nombre o código"
          placeholder="Buscar por nombre o código"
          @update:model-value="page = 1"
        />
        <div class="mt-1 flex justify-end">
          <CharCounter :value="nameFilter" :max="RETIREMENT_NAME_MAX_LENGTH" />
        </div>
      </div>
      <select v-model="monthFilter" class="field-input" aria-label="Filtrar bajas por mes" @change="page = 1">
        <option value="all">Todos los meses</option>
        <option v-for="month in months" :key="month" :value="month">{{ monthLabel(month) }}</option>
      </select>
    </div>

    <p v-if="exportError" role="alert" class="mt-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-50">{{ exportError }}</p>

    <div v-if="filteredRows.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[980px] text-left text-sm">
          <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
            <tr>
              <th class="px-5 py-4 font-bold">Fecha de baja</th>
              <th class="px-4 py-4 font-bold">Código</th>
              <th class="px-4 py-4 font-bold">Artículo</th>
              <th class="px-4 py-4 font-bold">Categoría</th>
              <th class="px-4 py-4 font-bold">Tipo</th>
              <th class="px-4 py-4 font-bold">Motivo</th>
              <th class="px-5 py-4 font-bold">Ubicación</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/10">
            <tr v-for="row in pagedRows" :key="row.key" class="transition hover:bg-white/[0.04]">
              <td class="whitespace-nowrap px-5 py-3" :class="row.fecha ? 'text-slate-300' : 'text-slate-500'">{{ formatRetirementDate(row.fecha) }}</td>
              <td class="whitespace-nowrap px-4 py-3 font-mono font-bold text-white">{{ row.codigo }}</td>
              <td class="px-4 py-3 font-bold text-white">{{ row.articulo }}</td>
              <td class="px-4 py-3 text-slate-300">{{ row.categoria || '-' }}</td>
              <td class="px-4 py-3">
                <span class="rounded-full px-3 py-1 text-xs font-black" :class="row.tipo === 'Unidad' ? 'bg-rose-400/15 text-rose-200' : 'bg-slate-400/15 text-slate-200'">{{ row.tipo }}</span>
              </td>
              <td class="max-w-xs px-4 py-3 text-slate-400">{{ row.motivo }}</td>
              <td class="px-5 py-3 text-slate-300">{{ row.ubicacion || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <TablePager v-if="filteredRows.length" v-model:page="page" v-model:pageSize="pageSize" :total="filteredRows.length" item-label="bajas" />
    <p v-else class="mt-5 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">
      {{ rows.length ? 'Ninguna baja coincide con los filtros.' : 'Todavía no hay bajas registradas.' }}
    </p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import { FileDown } from 'lucide-vue-next';
import TableSearch from '../common/TableSearch.vue';
import TablePager from '../common/TablePager.vue';
import CharCounter from '../common/CharCounter.vue';
import { useGymStore } from '../../../application/stores/gymStore';
import { DEFAULT_PAGE_SIZE } from '../../../domain/utils/inputRules.js';
import {
  buildRetirements, filterRetirements, formatRetirementDate, monthLabel, RETIREMENT_NAME_MAX_LENGTH, retirementMonths,
} from '../../../domain/utils/inventoryRetirements.js';
import { exportToExcel, retirementExcelRows, RETIREMENTS_EXCEL_COLUMNS } from '../../utils/excelExport.js';

const gymStore = useGymStore();
const nameFilter = ref('');
const monthFilter = ref('all');
const page = ref(1);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const isExporting = ref(false);
const exportError = ref('');

const rows = computed(() => buildRetirements({
  inventory: gymStore.inventory || [],
  units: gymStore.inventoryUnits || [],
  movements: gymStore.inventoryMovements || [],
}));
const months = computed(() => retirementMonths(rows.value));
const filteredRows = computed(() => filterRetirements(rows.value, { name: nameFilter.value, month: monthFilter.value }));
const pagedRows = computed(() => filteredRows.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value));

const download = async () => {
  if (isExporting.value) return;
  isExporting.value = true;
  exportError.value = '';
  try {
    const period = monthFilter.value === 'all' ? 'todos los meses' : monthLabel(monthFilter.value);
    await exportToExcel({
      sheetName: 'Bajas',
      title: `Bajas de inventario · ${period}`,
      columns: RETIREMENTS_EXCEL_COLUMNS,
      rows: retirementExcelRows(filteredRows.value),
    }, 'bajas_inventario');
  } catch {
    exportError.value = 'No se pudo generar el Excel. Vuelve a intentarlo.';
  } finally {
    isExporting.value = false;
  }
};
</script>

<style scoped>
.field-input { width: 100%; border: 1px solid rgba(255,255,255,.1); border-radius: 1rem; background: rgba(2,6,23,.72); padding: .75rem 1rem; color: white; outline: none; }
</style>
