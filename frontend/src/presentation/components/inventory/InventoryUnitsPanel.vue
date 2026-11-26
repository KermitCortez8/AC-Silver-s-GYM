<template>
  <div class="unit-panel" aria-label="Unidades del artículo">
    <div v-if="units.length || (!isLoadingUnits && !loadError)" class="flex items-center justify-between gap-2">
      <span class="unit-muted text-xs">{{ activeCount }} activas</span>
      <label v-if="retiredCount" class="unit-muted flex items-center gap-1.5 text-xs">
        <input v-model="showRetired" type="checkbox" class="h-3.5 w-3.5 accent-amber-400" />
        Ver bajas ({{ retiredCount }})
      </label>
    </div>

    <p v-if="feedback" class="unit-feedback" :class="{ 'is-error': feedbackTone === 'error' }" role="status">{{ feedback }}</p>

    <ul v-if="visibleUnits.length" class="unit-list">
      <li v-for="unit in visibleUnits" :key="unit.id_unidad" class="unit-row">
        <div class="flex items-center gap-2">
          <span class="unit-code">{{ unit.codigo }}</span>
          <span class="unit-badge" :class="statusClass(unit.estado)">{{ unit.estado }}</span>
          <div class="ml-auto flex shrink-0 gap-1">
            <button
              type="button"
              class="unit-icon"
              :class="{ 'is-active': mode(unit) === 'detalle' }"
              :aria-label="`Ver detalle de ${unit.codigo}`"
              :title="`Detalle de ${unit.codigo}`"
              :aria-expanded="mode(unit) === 'detalle'"
              @click="toggle(unit, 'detalle')"
            >
              <Eye :size="15" aria-hidden="true" />
            </button>
            <template v-if="isActiveUnit(unit)">
              <button
                type="button"
                class="unit-icon"
                :class="{ 'is-active': mode(unit) === 'editar' }"
                :aria-label="`Editar ${unit.codigo}`"
                :title="`Editar ${unit.codigo}`"
                :aria-expanded="mode(unit) === 'editar'"
                @click="toggle(unit, 'editar')"
              >
                <Pencil :size="15" aria-hidden="true" />
              </button>
              <button
                type="button"
                class="unit-icon unit-icon--danger"
                :class="{ 'is-active': mode(unit) === 'borrar' }"
                :aria-label="`Dar de baja ${unit.codigo}`"
                :title="`Dar de baja ${unit.codigo}`"
                :aria-expanded="mode(unit) === 'borrar'"
                @click="toggle(unit, 'borrar')"
              >
                <Archive :size="15" aria-hidden="true" />
              </button>
            </template>
            <button
              v-else
              type="button"
              class="unit-icon unit-icon--ok"
              :class="{ 'is-active': mode(unit) === 'restablecer' }"
              :aria-label="`Restablecer ${unit.codigo}`"
              :title="`Restablecer ${unit.codigo}`"
              :aria-expanded="mode(unit) === 'restablecer'"
              @click="toggle(unit, 'restablecer')"
            >
              <RotateCcw :size="15" aria-hidden="true" />
            </button>
          </div>
        </div>

        <dl v-if="mode(unit) === 'detalle'" class="unit-box grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
          <div class="col-span-2"><dt class="inv-label">Ubicación</dt><dd class="unit-text">{{ unit.ubicacion }}</dd></div>
          <div><dt class="inv-label">Alta</dt><dd class="unit-text">{{ unit.fecha_alta || 'Sin fecha' }}</dd></div>
          <div><dt class="inv-label">Baja</dt><dd class="unit-text">{{ unit.fecha_baja || '—' }}</dd></div>
          <div class="col-span-2"><dt class="inv-label">Observaciones</dt><dd class="unit-text">{{ unit.observaciones || 'Sin observaciones' }}</dd></div>
        </dl>

        <form v-else-if="mode(unit) === 'editar'" class="unit-box grid gap-2" @submit.prevent="saveUnit(unit)">
          <label class="grid gap-1">
            <span class="inv-label">Estado</span>
            <select :id="`unit-status-${unit.id_unidad}`" v-model="draft.estado" class="inv-input unit-input">
              <option v-for="status in UNIT_STATUSES" :key="status">{{ status }}</option>
            </select>
          </label>
          <div class="grid gap-1">
            <label :for="`unit-location-${unit.id_unidad}`" class="inv-label">Ubicación</label>
            <ExtensibleSelect
              :id="`unit-location-${unit.id_unidad}`"
              v-model="draft.ubicacion"
              class="unit-select"
              :options="locationOptions"
              placeholder="Selecciona una ubicación"
              add-label="Agregar nueva ubicación"
              add-placeholder="Ej. Sala 3"
            />
          </div>
          <label class="grid gap-1">
            <span class="inv-label">Observaciones</span>
            <input :id="`unit-notes-${unit.id_unidad}`" v-model="draft.observaciones" class="inv-input unit-input" maxlength="100" placeholder="Reparación, incidencia..." />
          </label>
          <div class="flex justify-end gap-1.5">
            <button type="button" class="unit-icon" aria-label="Cancelar edición" title="Cancelar" @click="close">
              <X :size="15" aria-hidden="true" />
            </button>
            <button type="submit" class="unit-icon unit-icon--primary" :disabled="isSaving" :aria-label="`Guardar ${unit.codigo}`" title="Guardar">
              <Check :size="15" aria-hidden="true" />
            </button>
          </div>
        </form>

        <form v-else-if="mode(unit) === 'borrar'" class="unit-box unit-box--danger grid gap-2" @submit.prevent="retireUnit(unit)">
          <p class="unit-danger-text text-xs">Se da de baja con una salida en Movimientos; su historial se conserva.</p>
          <input :id="`unit-reason-${unit.id_unidad}`" v-model="draft.motivo" class="inv-input unit-input" maxlength="100" placeholder="Motivo (opcional)" />
          <div class="flex justify-end gap-1.5">
            <button type="button" class="unit-icon" aria-label="Cancelar baja" title="Cancelar" @click="close">
              <X :size="15" aria-hidden="true" />
            </button>
            <button type="submit" class="unit-icon unit-icon--danger is-active" :disabled="isSaving" :aria-label="`Confirmar baja de ${unit.codigo}`" title="Confirmar baja">
              <Archive :size="15" aria-hidden="true" />
            </button>
          </div>
        </form>

        <form v-else-if="mode(unit) === 'restablecer'" class="unit-box unit-box--ok grid gap-2" @submit.prevent="restoreUnit(unit)">
          <p class="unit-ok-text text-xs">Vuelve a estar Operativa con el mismo código y suma 1 al stock; queda como entrada en Movimientos.</p>
          <input :id="`unit-restore-${unit.id_unidad}`" v-model="draft.motivo" class="inv-input unit-input" maxlength="100" placeholder="Motivo (opcional)" />
          <div class="flex justify-end gap-1.5">
            <button type="button" class="unit-icon" aria-label="Cancelar restablecimiento" title="Cancelar" @click="close">
              <X :size="15" aria-hidden="true" />
            </button>
            <button type="submit" class="unit-icon unit-icon--ok is-active" :disabled="isSaving" :aria-label="`Confirmar restablecimiento de ${unit.codigo}`" title="Confirmar restablecimiento">
              <Check :size="15" aria-hidden="true" />
            </button>
          </div>
        </form>
      </li>
    </ul>
    <p v-else class="unit-muted mt-2 text-xs" role="status">
      {{ isLoadingUnits ? 'Cargando unidades…' : loadError || 'Sin unidades activas. Registra una entrada en Movimientos para agregarlas.' }}
    </p>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { Archive, Check, Eye, Pencil, RotateCcw, X } from 'lucide-vue-next';
import ExtensibleSelect from '../common/ExtensibleSelect.vue';
import { useGymStore } from '../../../application/stores/gymStore';
import { isActiveUnit, UNIT_STATUSES } from '../../../domain/utils/inventoryUnits.js';
import { INVENTORY_LOCATIONS, inventoryOptions } from '../../utils/inventoryOptions.js';

const props = defineProps({ item: { type: Object, required: true } });

const gymStore = useGymStore();
const isLoadingUnits = computed(() => gymStore.isSectionSyncing('inventoryUnits'));
const loadError = ref('');
onMounted(() => {
  gymStore.fetchFromBackend({ section: 'inventoryUnits' }).catch(() => {
    loadError.value = 'No se pudieron cargar las unidades.';
  });
});
const showRetired = ref(false);
const openUnit = ref({ id: null, mode: '' });
const draft = reactive({ estado: 'Operativo', ubicacion: '', observaciones: '', motivo: '' });
const isSaving = ref(false);
const feedback = ref('');
const feedbackTone = ref('success');

const itemNumber = computed(() => Number(String(props.item.id).replace('item-', '')));
const units = computed(() => (gymStore.inventoryUnits || [])
  .filter((unit) => Number(unit.id_item) === itemNumber.value)
  .sort((a, b) => Number(a.correlativo) - Number(b.correlativo)));
const activeCount = computed(() => units.value.filter(isActiveUnit).length);
const retiredCount = computed(() => units.value.length - activeCount.value);
const visibleUnits = computed(() => units.value.filter((unit) => showRetired.value || isActiveUnit(unit)));
// Las mismas ubicaciones que el formulario del artículo, más las ya usadas por artículos y unidades.
const locationOptions = computed(() => inventoryOptions(
  INVENTORY_LOCATIONS,
  [...(gymStore.inventory || []).map((item) => item.location), ...(gymStore.inventoryUnits || []).map((unit) => unit.ubicacion)],
  draft.ubicacion,
));

const mode = (unit) => (openUnit.value.id === unit.id_unidad ? openUnit.value.mode : '');
const close = () => { openUnit.value = { id: null, mode: '' }; };
const toggle = (unit, nextMode) => {
  feedback.value = '';
  if (mode(unit) === nextMode) return close();
  Object.assign(draft, { estado: unit.estado, ubicacion: unit.ubicacion, observaciones: unit.observaciones || '', motivo: '' });
  openUnit.value = { id: unit.id_unidad, mode: nextMode };
};

const statusClass = (status) => ({
  Operativo: 'is-ok',
  'En mantenimiento': 'is-warn',
  'Fuera de servicio': 'is-bad',
}[status] || 'is-off');

const run = async (action, success) => {
  if (isSaving.value) return;
  isSaving.value = true;
  try {
    await action();
    feedback.value = success;
    feedbackTone.value = 'success';
    close();
  } catch (error) {
    feedback.value = error instanceof Error ? error.message : 'No se pudo guardar la unidad.';
    feedbackTone.value = 'error';
  } finally {
    isSaving.value = false;
  }
};

const saveUnit = (unit) => {
  if (!String(draft.ubicacion || '').trim()) {
    feedback.value = 'Elige una ubicación.';
    feedbackTone.value = 'error';
    return;
  }
  return run(() => gymStore.updateInventoryUnit(unit.id_unidad, {
    estado: draft.estado,
    ubicacion: draft.ubicacion.trim(),
    observaciones: draft.observaciones.trim(),
  }), `${unit.codigo} actualizada.`);
};

const retireUnit = (unit) => run(
  () => gymStore.retireInventoryUnit(unit.id_unidad, draft.motivo.trim()),
  `${unit.codigo} dada de baja; quedó registrada en Movimientos.`,
);

const restoreUnit = (unit) => run(
  () => gymStore.restoreInventoryUnit(unit.id_unidad, draft.motivo.trim()),
  `${unit.codigo} restablecida; quedó registrada en Movimientos.`,
);
</script>

<style scoped>
/* Colores por tema: oscuro por defecto y claro con texto de alto contraste. */
.unit-panel {
  --unit-text: #f1f5f9;
  --unit-muted: #94a3b8;
  --unit-line: rgba(255, 255, 255, 0.1);
  --unit-box: rgba(255, 255, 255, 0.04);
  --unit-btn-border: rgba(255, 255, 255, 0.16);
  --unit-btn-text: #e2e8f0;
  --unit-btn-hover: rgba(255, 255, 255, 0.08);
  --unit-danger: #fda4af;
  --unit-danger-bg: rgba(251, 113, 133, 0.12);
  --unit-primary-bg: #fbbf24;
  --unit-primary-text: #0f172a;
  --unit-ok: #a7f3d0;
  --unit-ok-bg: rgba(52, 211, 153, 0.12);
  margin-top: 0.6rem;
}
/* `:root[...]` y no `:global(...)`: Vue descarta el resto del selector tras `:global()`. */
:root[data-theme="light"] .unit-panel {
  --unit-text: #0f172a;
  --unit-muted: #334155;
  --unit-line: #e2e8f0;
  --unit-box: #ffffff;
  --unit-btn-border: #cbd5e1;
  --unit-btn-text: #0f172a;
  --unit-btn-hover: #f1f5f9;
  --unit-danger: #be123c;
  --unit-danger-bg: #fff1f2;
  --unit-primary-bg: #2563eb;
  --unit-primary-text: #ffffff;
  --unit-ok: #047857;
  --unit-ok-bg: #ecfdf5;
}
.unit-muted { color: var(--unit-muted); }
.unit-text { color: var(--unit-text); }
.unit-list {
  margin-top: 0.4rem;
  max-height: 15rem;
  overflow-y: auto;
  overscroll-behavior: contain;
  border: 1px solid var(--unit-line);
  border-radius: 0.9rem;
}
.unit-row { padding: 0.45rem 0.6rem; border-bottom: 1px solid var(--unit-line); }
.unit-row:last-child { border-bottom: 0; }
.unit-code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.82rem; font-weight: 800; color: var(--unit-text); white-space: nowrap; }
.unit-badge { border: 1px solid; border-radius: 999px; padding: 0.05rem 0.45rem; font-size: 0.68rem; font-weight: 700; white-space: nowrap; }
.unit-badge.is-ok { border-color: rgba(52, 211, 153, 0.35); background: rgba(52, 211, 153, 0.12); color: #6ee7b7; }
.unit-badge.is-warn { border-color: rgba(251, 191, 36, 0.35); background: rgba(251, 191, 36, 0.12); color: #fcd34d; }
.unit-badge.is-bad { border-color: rgba(251, 113, 133, 0.35); background: rgba(251, 113, 133, 0.12); color: #fda4af; }
.unit-badge.is-off { border-color: var(--unit-line); color: var(--unit-muted); }
:root[data-theme="light"] .unit-badge.is-ok { border-color: #6ee7b7; background: #ecfdf5; color: #065f46; }
:root[data-theme="light"] .unit-badge.is-warn { border-color: #fcd34d; background: #fffbeb; color: #92400e; }
:root[data-theme="light"] .unit-badge.is-bad { border-color: #fda4af; background: #fff1f2; color: #9f1239; }
.unit-icon {
  display: inline-flex;
  height: 1.85rem;
  width: 1.85rem;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--unit-btn-border);
  border-radius: 0.6rem;
  color: var(--unit-btn-text);
  transition: background 0.15s, color 0.15s;
}
.unit-icon:hover, .unit-icon.is-active { background: var(--unit-btn-hover); }
.unit-icon:focus-visible { outline: 2px solid var(--unit-primary-bg); outline-offset: 2px; }
.unit-icon:disabled { opacity: 0.6; cursor: not-allowed; }
.unit-icon--danger { color: var(--unit-danger); }
.unit-icon--danger:hover, .unit-icon--danger.is-active { background: var(--unit-danger-bg); }
.unit-icon--primary { border-color: transparent; background: var(--unit-primary-bg); color: var(--unit-primary-text); }
.unit-icon--primary:hover { background: var(--unit-primary-bg); filter: brightness(1.08); }
.unit-box { margin-top: 0.45rem; border: 1px solid var(--unit-line); border-radius: 0.75rem; background: var(--unit-box); padding: 0.55rem 0.65rem; }
.unit-box--danger { border-color: var(--unit-danger); background: var(--unit-danger-bg); }
.unit-danger-text { color: var(--unit-danger); }
.unit-icon--ok { color: var(--unit-ok); }
.unit-icon--ok:hover, .unit-icon--ok.is-active { background: var(--unit-ok-bg); }
.unit-box--ok { border-color: var(--unit-ok); background: var(--unit-ok-bg); }
.unit-ok-text { color: var(--unit-ok); }
.unit-feedback { margin-top: 0.4rem; border-radius: 0.6rem; padding: 0.35rem 0.6rem; font-size: 0.75rem; background: rgba(52, 211, 153, 0.12); color: var(--unit-ok); }
.unit-feedback.is-error { background: var(--unit-danger-bg); color: var(--unit-danger); }
.unit-input, .unit-select :deep(.inv-input) { padding: 0.45rem 0.7rem; font-size: 0.82rem; border-radius: 0.65rem; }
</style>
