<template>
  <div class="inv-store-theme space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-xs font-bold uppercase tracking-[0.3em] text-orange-300">Recursos &middot; Gestión de inventario</p>
          <h1 class="mt-2 text-3xl font-black text-white">Inventario</h1>
          <p class="mt-2 text-slate-300">Controla stock, ubicación, estado operativo y observaciones de cada recurso del gimnasio.</p>
        </div>

        <button v-if="activeTab === 'articulos'" class="rounded-2xl bg-orange-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg shadow-orange-500/20 transition hover:scale-[1.02] hover:bg-orange-300" @click="openNewItem">
          + Ingresar Nuevo Artículo
        </button>
      </div>

      <nav class="mt-5 flex border-b border-white/10" aria-label="Secciones de inventario">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="relative px-5 py-3 text-sm font-bold transition-colors duration-200"
          :class="activeTab === tab.value ? 'text-orange-400' : 'text-slate-400 hover:text-slate-200'"
          :aria-current="activeTab === tab.value ? 'page' : undefined"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
          <span
            v-if="activeTab === tab.value"
            class="absolute bottom-0 left-0 h-0.5 w-full rounded-full bg-orange-400"
          ></span>
        </button>
      </nav>
    </section>

    <InventoryMovementsPanel v-if="activeTab === 'movimientos'" />

    <section v-else class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Estado</p>
          <h2 class="mt-2 text-2xl font-black text-white">Listado de inventario</h2>
        </div>
      </div>

      <div class="mt-5 flex flex-wrap gap-2.5">
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold transition"
          :class="selectedCategory === 'all' ? 'border-orange-400 bg-orange-400 text-slate-950' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'"
          @click="selectedCategory = 'all'; paginaActual = 1"
        >
          Todas las categorías <span :class="selectedCategory === 'all' ? 'text-slate-900/70' : 'text-slate-500'">{{ inventory.length }}</span>
        </button>
        <button
          v-for="entry in categorySummary"
          :key="entry.name"
          type="button"
          class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold transition"
          :class="selectedCategory === entry.name ? 'border-orange-400 bg-orange-400 text-slate-950' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'"
          @click="selectedCategory = entry.name; paginaActual = 1"
        >
          <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ background: categoryDotColor(entry.name) }"></span>
          {{ entry.name }} <span :class="selectedCategory === entry.name ? 'text-slate-900/70' : 'text-slate-500'">{{ entry.count }}</span>
        </button>
      </div>

      <div class="mt-4 grid gap-3 sm:grid-cols-[1.5fr_1fr_1fr]">
        <TableSearch
          v-model="searchQuery"
          label="Buscar artículos por N°, nombre o categoría"
          placeholder="Buscar por N°, nombre o categoría"
          @update:model-value="paginaActual = 1"
        />
        <select v-model="selectedLocation" class="field-input" aria-label="Filtrar por ubicación" @change="paginaActual = 1">
          <option value="all">Todas las ubicaciones</option>
          <option v-for="loc in locationOptions" :key="loc" :value="loc">{{ loc }}</option>
        </select>
        <select v-model="selectedStatus" class="field-input" aria-label="Filtrar por estado" @change="paginaActual = 1">
          <option value="all">Todos los estados</option>
          <option>Operativo</option>
          <option>Disponible</option>
          <option>En mantenimiento</option>
          <option>Fuera de servicio</option>
          <option>Dado de baja</option>
          <option>Stock bajo</option>
          <option>Agotado</option>
          <option>Descontinuado</option>
        </select>
      </div>

      <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
        {{ feedbackMessage }}
      </p>

      <div v-if="filteredInventory.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[1080px] text-left text-sm">
            <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
              <tr>
                <SortableTh class="px-5 py-4 font-bold" label="N° artículo" column="code" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="px-4 py-4 font-bold" label="Nombre" column="name" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <th class="px-4 py-4 font-bold">Categoría</th>
                <th class="px-4 py-4 font-bold">Ubicación</th>
                <SortableTh class="px-4 py-4 font-bold" label="Stock" column="quantity" numeric :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <th class="px-4 py-4 font-bold">Estado</th>
                <th class="px-5 py-4 text-right font-bold">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr v-for="item in inventoryPaginado" :key="item.id" class="transition hover:bg-white/[0.04]">
                <td class="whitespace-nowrap px-5 py-4 align-top">
                  <span class="rounded-lg bg-amber-400/10 px-2.5 py-1 text-xs font-bold text-amber-200">
                    {{ item.inventoryCode }}
                  </span>
                </td>
                <td class="max-w-xs px-4 py-4 align-top">
                  <p class="font-bold text-white">{{ item.name }}</p>
                  <p class="mt-1 line-clamp-1 text-xs leading-5 text-slate-400">{{ item.observations || 'Sin observaciones' }}</p>
                </td>
                <td class="px-4 py-4 align-top">
                  <span class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-slate-200">
                    <span class="h-1.5 w-1.5 shrink-0 rounded-full" :style="{ background: categoryDotColor(item.category) }"></span>
                    {{ item.category || 'General' }}
                  </span>
                </td>
                <td class="px-4 py-4 align-top text-slate-300">{{ item.location || 'Sin ubicación' }}</td>
                <td class="px-4 py-4 align-top">
                  <p class="font-bold" :class="isLowStock(item) ? 'text-rose-300' : 'text-white'">
                    {{ item.quantity }} {{ item.unidad_venta || 'unidad' }}
                  </p>
                  <p class="mt-1 text-xs text-slate-400">Mínimo: {{ item.minQuantity || 0 }}</p>
                </td>
                <td class="px-4 py-4 align-top">
                  <span class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold" :class="inventoryStatusClass(item.status)">
                    {{ item.status }}
                  </span>
                </td>
                <td class="px-5 py-4 align-top">
                  <div class="flex justify-end gap-2">
                    <button class="inline-flex items-center gap-1.5 rounded-xl border border-sky-400/30 bg-sky-400/10 px-3 py-2 text-sm font-bold text-sky-200 transition hover:bg-sky-400/20" @click="openDetails(item)">
                      <Eye :size="15" aria-hidden="true" /> Detalles
                    </button>
                    <button class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/5" @click="editItem(item)">
                      Editar
                    </button>
                    <button class="rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-100 transition hover:bg-rose-400/10" @click="deleteItem(item.id)">
                      Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <TablePager
        v-model:page="paginaActual"
        v-model:pageSize="porPagina"
        :total="filteredInventory.length"
        item-label="articulos"
      />

      <p v-if="!filteredInventory.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">
        {{ inventory.length ? 'Ningún artículo coincide con los filtros aplicados.' : 'No hay artículos en inventario. Usa "Ingresar Nuevo Artículo" para registrar el primero.' }}
      </p>
    </section>

    <ResourceModal
      :open="isEditorOpen"
      :icon="Package"
      eyebrow="Inventario · Artículo"
      :title="editingId ? 'Editar artículo' : 'Nuevo artículo'"
      :subtitle="editingId ? `N° de artículo ${currentInventoryCode}` : 'Los campos con * son obligatorios.'"
      size="xl"
      :busy="isSaving"
      @close="closeEditor"
      @submit="handleSubmit"
    >
      <div v-if="formErrors.length" role="alert" class="inv-error">
        <AlertCircle :size="16" aria-hidden="true" />
        <p>{{ missingFieldsMessage(formErrors) }}</p>
      </div>

      <fieldset class="rm-section">
        <legend class="sr-only">Información general</legend>
        <p class="rm-section-title"><Info :size="14" aria-hidden="true" /> Información general</p>
        <div class="grid gap-4 sm:grid-cols-2">
          <div class="space-y-2 sm:col-span-2">
            <label for="inv-name" class="inv-label inv-required">Nombre</label>
            <input
              id="inv-name"
              v-model="form.name"
              class="field-input"
              :class="{ 'is-invalid': formErrors.includes('Nombre') || nameWarning }"
              :maxlength="NAME_MAX_LENGTH"
              placeholder="Nombre del artículo"
              @beforeinput="blockNameChars"
              @input="cleanNameField"
            />
            <p v-if="nameWarning" class="inv-field-error">{{ nameWarning }}</p>
          </div>
          <div class="space-y-2">
            <label for="inv-category" class="inv-label">Categoría (Tipo)</label>
            <ExtensibleSelect
              id="inv-category"
              v-model="form.category"
              :options="categoryOptions"
              placeholder="Selecciona una categoría"
              add-label="Agregar nueva categoría"
              add-placeholder="Nombre de la categoría"
            />
          </div>
          <div class="space-y-2">
            <label for="inv-location" class="inv-label">Ubicación</label>
            <ExtensibleSelect
              id="inv-location"
              v-model="form.location"
              :options="editorLocationOptions"
              placeholder="Selecciona una ubicación"
              add-label="Agregar nueva ubicación"
              add-placeholder="Ej. Sala 3"
            />
          </div>
        </div>
      </fieldset>

      <fieldset class="rm-section">
        <legend class="sr-only">Stock</legend>
        <p class="rm-section-title"><Boxes :size="14" aria-hidden="true" /> Stock</p>
        <div class="grid gap-4 sm:grid-cols-3">
          <div class="space-y-2">
            <label for="inv-quantity" class="inv-label" :class="{ 'inv-required': !editingId }">{{ editingId ? 'Stock actual' : 'Stock inicial' }}</label>
            <div v-if="!editingId" class="flex items-center gap-2">
              <button type="button" class="field-input flex shrink-0 items-center justify-center text-lg font-bold" style="width: 2.75rem; padding: 0" aria-label="Restar una unidad" @click="stepQuantity(-1)" :disabled="isSaving">−</button>
              <QuantityInput
                id="inv-quantity"
                v-model="form.quantity"
                class="field-input flex-1 text-center"
                :class="{ 'is-invalid': formErrors.includes('Stock inicial') }"
                placeholder="0"
              />
              <button type="button" class="field-input flex shrink-0 items-center justify-center text-lg font-bold" style="width: 2.75rem; padding: 0" aria-label="Sumar una unidad" @click="stepQuantity(1)" :disabled="isSaving">+</button>
            </div>
            <input v-else id="inv-quantity" :value="form.quantity" type="text" class="field-input cursor-not-allowed text-center opacity-70" readonly />
            <p v-if="numberWarning.quantity" class="inv-field-error">{{ numberWarning.quantity }}</p>
          </div>
          <div class="space-y-2">
            <label for="inv-min" class="flex items-center justify-between gap-2">
              <span class="inv-label inv-required">Stock mínimo</span>
              <span v-if="form.minQuantity !== '' && Number(form.quantity || 0) <= Number(form.minQuantity)" class="rounded-full border border-yellow-400/40 bg-yellow-100 px-2.5 py-0.5 text-[10px] font-black uppercase tracking-wide text-yellow-800">Alerta activa</span>
            </label>
            <QuantityInput
              id="inv-min"
              v-model="form.minQuantity"
              class="field-input"
              placeholder="Ej. 5"
              :class="{ 'is-invalid': formErrors.includes('Stock mínimo') }"
              @update:model-value="formErrors = formErrors.filter((label) => label !== 'Stock mínimo')"
            />
            <p v-if="numberWarning.minQuantity" class="inv-field-error">{{ numberWarning.minQuantity }}</p>
          </div>
          <div class="space-y-2">
            <label for="inv-unit" class="inv-label">Unidad</label>
            <ExtensibleSelect
              id="inv-unit"
              v-model="form.unidad_venta"
              :options="unitOptions"
              placeholder="Selecciona una unidad"
              add-label="Agregar nueva unidad"
              add-placeholder="Ej. Bolsa"
            />
          </div>
          <div class="inv-info sm:col-span-3">
            <Info :size="16" aria-hidden="true" />
            <div class="space-y-1">
              <p>Alerta de stock mínimo: el artículo entra en alerta cuando su stock es igual o menor a este valor.{{ isTiendaForm ? ' El mínimo de Tienda se edita en su producto.' : '' }}</p>
              <p v-if="editingId">
                El stock no se edita aquí: registra una entrada, salida o ajuste en la pestaña Movimientos.
                <span v-if="isTiendaForm" class="font-bold">Este artículo es la reserva de Tienda: para pasar unidades a la Tienda registra una salida con destino Tienda.</span>
              </p>
              <p v-else>
                El N° de artículo se genera automáticamente y el stock inicial queda registrado como una entrada en Movimientos.
                <span v-if="isTiendaForm" class="font-bold">Al ser Tipo "Tienda" se creará su producto en la tienda, sin stock y oculto hasta que le asignes precio.</span>
              </p>
            </div>
          </div>
        </div>
      </fieldset>

      <fieldset class="rm-section">
        <legend class="sr-only">Estado y observaciones</legend>
        <p class="rm-section-title"><ClipboardCheck :size="14" aria-hidden="true" /> Estado y observaciones</p>
        <div class="grid gap-4">
          <div class="space-y-2">
            <span class="flex items-center justify-between gap-2">
              <label for="inv-status" class="inv-label">Estado</label>
              <span class="inline-flex w-fit rounded-full border px-3 py-0.5 text-[11px] font-black uppercase tracking-wide" :class="inventoryStatusClass(statusPreview)">
                {{ statusPreview }}
              </span>
            </span>
            <template v-if="isTiendaForm">
              <label class="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-200">
                <input id="inv-status" v-model="isDiscontinuedForm" type="checkbox" class="h-4 w-4 accent-amber-400" />
                Marcar como Descontinuado
              </label>
              <p class="inv-info">
                <Info :size="16" aria-hidden="true" />
                Los artículos de Tienda cambian solos a Disponible, Stock bajo o Agotado según su stock y su stock mínimo en Inventario.
              </p>
            </template>
            <select v-else id="inv-status" v-model="form.status" class="field-input">
              <option>Operativo</option>
              <option>En mantenimiento</option>
              <option>Fuera de servicio</option>
              <option>Dado de baja</option>
              <option>Disponible</option>
              <option>Stock bajo</option>
              <option>Agotado</option>
              <option>Descontinuado</option>
            </select>
          </div>
          <div class="space-y-2">
            <label for="inv-observations" class="inv-label">Observaciones</label>
            <textarea id="inv-observations" v-model="form.observations" rows="3" class="field-input" placeholder="Estado del equipo, mantenimiento pendiente, incidencias..."></textarea>
          </div>
        </div>
      </fieldset>

      <p v-if="editorError" role="alert" class="app-notice app-notice--error rounded-2xl border px-4 py-3 text-sm">{{ editorError }}</p>

      <template #footer>
        <button type="button" class="rm-btn-secondary" :disabled="isSaving" @click="closeEditor">Cancelar</button>
        <button type="submit" :disabled="isSaving" class="rounded-2xl bg-amber-400 px-5 py-3 text-base font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300">
          {{ isSaving ? 'Guardando...' : editingId ? 'Guardar cambios' : 'Agregar artículo' }}
        </button>
      </template>
    </ResourceModal>

    <ResourceModal
      :open="Boolean(detailItem)"
      :icon="Eye"
      eyebrow="Inventario · Detalles"
      :title="detailItem?.name || 'Artículo'"
      :subtitle="detailItem ? `N° de artículo ${detailItem.inventoryCode}` : ''"
      size="lg"
      @close="detailItem = null"
    >
      <template v-if="detailItem">
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="rm-section">
            <p class="rm-section-title" style="margin-bottom: 0.35rem">Stock</p>
            <p class="text-2xl font-black" :class="isLowStock(detailItem) ? 'text-rose-300' : 'text-white'">{{ detailItem.quantity }}</p>
            <p class="text-xs text-slate-400">{{ detailItem.unidad_venta || 'unidad' }} · mínimo {{ detailItem.minQuantity || 0 }}</p>
          </div>
          <div class="rm-section">
            <p class="rm-section-title" style="margin-bottom: 0.35rem">Estado</p>
            <span class="inline-flex rounded-full border px-2.5 py-1 text-xs font-bold" :class="inventoryStatusClass(detailItem.status)">{{ detailItem.status }}</span>
          </div>
          <div class="rm-section">
            <p class="rm-section-title" style="margin-bottom: 0.35rem">Categoría</p>
            <p class="font-bold text-white">{{ detailItem.category || 'General' }}</p>
          </div>
        </div>

        <dl class="rm-section grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
          <div>
            <dt class="inv-label">Ubicación</dt>
            <dd class="mt-1 text-slate-300">{{ detailItem.location || 'Sin ubicación' }}</dd>
          </div>
          <div>
            <dt class="inv-label">N° activo</dt>
            <dd class="mt-1 text-slate-300">{{ detailItem.n_activo || 'Auto' }}</dd>
          </div>
          <div class="sm:col-span-2">
            <dt class="inv-label">Observaciones</dt>
            <dd class="mt-1 text-slate-300">{{ detailItem.observations || 'Sin observaciones' }}</dd>
          </div>
        </dl>

        <div class="rm-section">
          <p class="rm-section-title"><History :size="14" aria-hidden="true" /> Últimos movimientos</p>
          <ul v-if="detailMovements.length" class="divide-y divide-white/10 text-sm">
            <li v-for="movement in detailMovements" :key="movement.id_mov" class="flex items-center justify-between gap-3 py-2">
              <span class="text-slate-300">{{ movement.fecha_movimiento || 'Sin fecha' }}</span>
              <span class="rounded-full px-2.5 py-0.5 text-xs font-black capitalize" :class="movementClass(movement.tipo_movimiento)">{{ movement.tipo_movimiento }}</span>
              <span class="w-12 text-right font-bold text-white">{{ signedQuantity(movement) }}</span>
              <span class="hidden min-w-0 flex-1 truncate text-xs text-slate-400 sm:block">{{ movement.descripcion || 'Sin descripción' }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-slate-400">Este artículo aún no tiene movimientos.</p>
        </div>
      </template>

      <template #footer>
        <button type="button" class="rm-btn-secondary" @click="detailItem = null">Cerrar</button>
        <button type="button" class="rounded-2xl bg-amber-400 px-5 py-3 font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300" @click="editFromDetails">
          Editar artículo
        </button>
      </template>
    </ResourceModal>
  </div>
</template>

<script setup>
import QuantityInput from '../components/QuantityInput.vue';
import { AlertCircle, Boxes, ClipboardCheck, Eye, History, Info, Package } from 'lucide-vue-next';
import InventoryMovementsPanel from '../components/inventory/InventoryMovementsPanel.vue';
import ResourceModal from '../components/ResourceModal.vue';
import ExtensibleSelect from '../components/common/ExtensibleSelect.vue';
import SortableTh from '../components/common/SortableTh.vue';
import TablePager from '../components/common/TablePager.vue';
import TableSearch from '../components/common/TableSearch.vue';
import { missingFieldsMessage, NAME_MAX_LENGTH } from '../../domain/utils/inputRules.js';
import { useInventoryWorkspace } from '../composables/inventory/useInventoryWorkspace.js';

const {
  route, router, gymStore, tabs, activeTab,
  inventory, searchQuery, selectedCategory, selectedLocation, selectedStatus,
  locationOptions, locationChoices, filteredInventory, sortKey, sortDir,
  SORT_COLUMNS, toggleSort, sortedInventory, paginaActual, porPagina,
  paginaInicio, totalPages, inventoryPaginado, categorySummary, editingId,
  isEditorOpen, isSaving, editorError, feedbackMessage, feedbackTone,
  formErrors, nameWarning, numberWarning, form, categoryOptions,
  editorLocationOptions, unitOptions, stepQuantity, isTiendaForm, isDiscontinuedForm,
  statusPreview, feedbackToneClass, isLowStock, categoryDotPalette, categoryDotColor,
  inventoryStatusClass, currentInventoryCode, blockNameChars, cleanNameField, clearFormWarnings,
  resetForm, openNewItem, closeEditor, editItem, requiredFields,
  handleSubmit, deleteItem, detailItem, itemNumber, detailMovements,
  movementClass, signedQuantity, openDetails, editFromDetails,
} = useInventoryWorkspace();
</script>

<style scoped>
.field-input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  background: rgba(2, 6, 23, 0.72);
  padding: 0.75rem 1rem;
  color: white;
  outline: none;
}

.field-input::placeholder {
  color: #64748b;
}
</style>
