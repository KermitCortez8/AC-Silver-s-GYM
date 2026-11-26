<template>
  <ResourceModal
    :open="Boolean(movement)"
    :icon="History"
    eyebrow="Movimientos · Detalles"
    :title="item?.name || 'Movimiento'"
    :subtitle="movement ? `Movimiento #${movement.id_mov}${item ? ` · ${item.inventoryCode}` : ''}` : ''"
    size="xl"
    @close="$emit('close')"
  >
    <template v-if="movement">
      <dl class="grid gap-3 sm:grid-cols-3">
        <div class="rm-section">
          <dt class="rm-section-title">Tipo</dt>
          <dd class="flex items-center gap-2">
            <span class="rounded-full px-2.5 py-0.5 text-xs font-black" :class="movementClass(movement.tipo_movimiento)">{{ movementTypeLabel(movement.tipo_movimiento) }}</span>
            <span class="font-black text-white">{{ signedQuantity(movement) }}</span>
          </dd>
        </div>
        <div class="rm-section">
          <dt class="rm-section-title">Fecha y hora</dt>
          <dd class="text-white">{{ movement.fecha_movimiento || 'Sin fecha' }} <span class="text-slate-400">{{ movementTime(movement) }}</span></dd>
        </div>
        <div class="rm-section">
          <dt class="rm-section-title">Registrado por</dt>
          <dd class="text-white">{{ author }}</dd>
        </div>
        <div class="rm-section sm:col-span-3">
          <dt class="rm-section-title">Descripción{{ destination ? ` · Destino ${destination}` : '' }}</dt>
          <dd class="text-slate-200">{{ movement.descripcion || 'Sin descripción' }}</dd>
        </div>
      </dl>

      <div class="rm-section mt-4">
        <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
          <p class="rm-section-title" style="margin-bottom: 0"><History :size="14" aria-hidden="true" /> Historial</p>
          <div v-if="unit" class="flex rounded-xl border border-white/10 p-0.5 text-xs font-bold" role="group" aria-label="Alcance del historial">
            <button type="button" class="rounded-lg px-3 py-1" :class="!unitOnly ? 'bg-white/10 text-white' : 'text-slate-400'" :aria-pressed="!unitOnly" @click="unitOnly = false">Todo el artículo</button>
            <button type="button" class="rounded-lg px-3 py-1 font-mono" :class="unitOnly ? 'bg-white/10 text-white' : 'text-slate-400'" :aria-pressed="unitOnly" @click="unitOnly = true">Solo {{ unit.codigo }}</button>
          </div>
        </div>
        <ul v-if="history.length" class="max-h-72 divide-y divide-white/10 overflow-y-auto pr-1 text-sm">
          <li v-for="row in history" :key="row.id_mov" class="flex items-center gap-3 py-2" :class="{ 'bg-white/[0.04]': row.id_mov === movement.id_mov }">
            <span class="w-24 shrink-0 text-slate-300">{{ row.fecha_movimiento || 'Sin fecha' }}</span>
            <span class="w-11 shrink-0 text-xs text-slate-400">{{ movementTime(row) }}</span>
            <span class="w-20 shrink-0 rounded-full px-2.5 py-0.5 text-center text-xs font-black" :class="movementClass(row.tipo_movimiento)">{{ movementTypeLabel(row.tipo_movimiento) }}</span>
            <span class="w-10 shrink-0 text-right font-bold text-white">{{ signedQuantity(row) }}</span>
            <span class="min-w-0 flex-1 truncate text-xs text-slate-400" :title="row.descripcion">{{ row.descripcion || 'Sin descripción' }}</span>
          </li>
        </ul>
        <p v-else class="text-sm text-slate-400">Sin movimientos para mostrar.</p>
      </div>
    </template>

    <template #footer>
      <button type="button" class="rm-btn-secondary" @click="$emit('close')">Cerrar</button>
    </template>
  </ResourceModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { History } from 'lucide-vue-next';
import ResourceModal from '../ResourceModal.vue';
import { useGymStore } from '../../../application/stores/gymStore';
import { movementAuthor, movementHistory, movementTime, movementTypeLabel, signedQuantity } from '../../../domain/utils/inventoryMovements.js';

const props = defineProps({
  movement: { type: Object, default: null },
  item: { type: Object, default: null },
  destination: { type: String, default: '' },
});
defineEmits(['close']);

const gymStore = useGymStore();
const unitOnly = ref(false);
// Al abrir otro movimiento se vuelve a mostrar todo el artículo.
watch(() => props.movement?.id_mov, () => { unitOnly.value = false; });

const unit = computed(() => (props.movement?.id_unidad
  ? (gymStore.inventoryUnits || []).find((entry) => Number(entry.id_unidad) === Number(props.movement.id_unidad)) || null
  : null));
const history = computed(() => movementHistory(gymStore.inventoryMovements, props.movement, unitOnly.value ? unit.value : null));
const author = computed(() => movementAuthor(props.movement, gymStore.users || []));

const movementClass = (type) => ({
  entrada: 'bg-emerald-400/15 text-emerald-200',
  salida: 'bg-rose-400/15 text-rose-200',
  traslado: 'bg-violet-400/15 text-violet-200',
}[type] || 'bg-cyan-400/15 text-cyan-200');
</script>
