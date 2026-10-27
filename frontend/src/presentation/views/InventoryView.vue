<template>
  <div class="inv-store-theme space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-xs font-bold uppercase tracking-[0.3em] text-amber-300">Recursos &middot; Gestion de inventario</p>
          <h1 class="mt-2 text-3xl font-black text-white">Inventario</h1>
          <p class="mt-2 text-slate-300">Controla stock, ubicacion, estado operativo y observaciones de cada recurso del gimnasio.</p>
        </div>

        <button v-if="activeTab === 'articulos'" class="rounded-2xl bg-amber-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:scale-[1.02] hover:bg-amber-300" @click="openNewItem">
          + Ingresar Nuevo Articulo
        </button>
      </div>

      <nav class="mt-5 flex border-b border-white/10" aria-label="Secciones de inventario">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="relative px-5 py-3 text-sm font-bold transition-colors duration-200"
          :class="activeTab === tab.value ? 'text-amber-400' : 'text-slate-400 hover:text-slate-200'"
          :aria-current="activeTab === tab.value ? 'page' : undefined"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
          <span
            v-if="activeTab === tab.value"
            class="absolute bottom-0 left-0 h-0.5 w-full rounded-full bg-amber-400"
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

      <div class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-blue-400 bg-slate-900/80 px-4 py-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
            <Package :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Total registrados</p>
            <p class="text-2xl font-black text-white">{{ inventory.length }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-green-400 bg-slate-900/80 px-4 py-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-green-100 text-green-600">
            <CheckCircle2 :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Disponibilidad operativa</p>
            <p class="text-2xl font-black text-white">{{ operationalPercent }}%</p>
          </div>
        </div>
        <button
          type="button"
          class="flex items-center gap-3 rounded-2xl border-l-4 border-l-yellow-400 bg-slate-900/80 px-4 py-3 text-left transition hover:bg-slate-800/80"
          :class="isLowStockFilter ? 'ring-2 ring-yellow-400/70' : ''"
          :aria-pressed="isLowStockFilter"
          :title="isLowStockFilter ? 'Quitar filtro de stock minimo' : 'Ver solo articulos en su stock minimo o por debajo'"
          @click="toggleLowStockFilter"
        >
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-yellow-100 text-yellow-700">
            <TrendingDown :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Stock minimo</p>
            <p class="text-2xl font-black text-white">{{ lowStock.length }}</p>
          </div>
        </button>
        <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-violet-400 bg-slate-900/80 px-4 py-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-100 text-violet-600">
            <Wrench :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">En mantenimiento</p>
            <p class="text-2xl font-black text-white">{{ maintenanceItems }}</p>
          </div>
        </div>
      </div>

      <div class="mt-5 flex flex-wrap gap-2.5">
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold transition"
          :class="selectedCategory === 'all' ? 'border-amber-400 bg-amber-400 text-slate-950' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'"
          @click="selectedCategory = 'all'; paginaActual = 1"
        >
          Todas las categorias <span :class="selectedCategory === 'all' ? 'text-slate-900/70' : 'text-slate-500'">{{ inventory.length }}</span>
        </button>
        <button
          v-for="entry in categorySummary"
          :key="entry.name"
          type="button"
          class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold transition"
          :class="selectedCategory === entry.name ? 'border-amber-400 bg-amber-400 text-slate-950' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'"
          @click="selectedCategory = entry.name; paginaActual = 1"
        >
          <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ background: categoryDotColor(entry.name) }"></span>
          {{ entry.name }} <span :class="selectedCategory === entry.name ? 'text-slate-900/70' : 'text-slate-500'">{{ entry.count }}</span>
        </button>
      </div>

      <div class="mt-4 grid gap-3 sm:grid-cols-[1.5fr_1fr_1fr]">
        <TableSearch
          v-model="searchQuery"
          label="Buscar articulos por N° o nombre"
          placeholder="Buscar por N° de articulo o nombre"
          @update:model-value="paginaActual = 1"
        />
        <select v-model="selectedLocation" class="field-input" aria-label="Filtrar por ubicacion" @change="paginaActual = 1">
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
                <SortableTh class="px-5 py-4 font-bold" label="N° articulo" column="code" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="px-4 py-4 font-bold" label="Nombre" column="name" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <th class="px-4 py-4 font-bold">Categoria</th>
                <th class="px-4 py-4 font-bold">Ubicacion</th>
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
                <td class="px-4 py-4 align-top text-slate-300">{{ item.location || 'Sin ubicacion' }}</td>
                <td class="px-4 py-4 align-top">
                  <p class="font-bold" :class="isLowStock(item) ? 'text-rose-300' : 'text-white'">
                    {{ item.quantity }} {{ item.unidad_venta || 'unidad' }}
                  </p>
                  <div class="mt-1.5 h-1.5 w-24 overflow-hidden rounded-full bg-white/10">
                    <div class="h-full rounded-full transition-all" :class="isLowStock(item) ? 'bg-rose-500' : 'bg-green-500'" :style="{ width: stockBarPercent(item) + '%' }"></div>
                  </div>
                  <p class="mt-1 text-xs text-slate-400">Minimo: {{ item.minQuantity || 0 }}</p>
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
        {{ inventory.length ? 'Ningun articulo coincide con los filtros aplicados.' : 'No hay articulos en inventario. Usa "Ingresar Nuevo Articulo" para registrar el primero.' }}
      </p>
    </section>

    <ResourceModal
      :open="isEditorOpen"
      :icon="Package"
      eyebrow="Inventario · Articulo"
      :title="editingId ? 'Editar articulo' : 'Nuevo articulo'"
      :subtitle="editingId ? `N° de articulo ${currentInventoryCode}` : 'Los campos con * son obligatorios.'"
      size="xl"
      @close="closeEditor"
      @submit="handleSubmit"
    >
      <div v-if="formErrors.length" role="alert" class="inv-error">
        <AlertCircle :size="16" aria-hidden="true" />
        <p>{{ missingFieldsMessage(formErrors) }}</p>
      </div>

      <fieldset class="rm-section">
        <legend class="sr-only">Informacion general</legend>
        <p class="rm-section-title"><Info :size="14" aria-hidden="true" /> Informacion general</p>
        <div class="grid gap-4 sm:grid-cols-2">
          <div class="space-y-2 sm:col-span-2">
            <label for="inv-name" class="inv-label inv-required">Nombre</label>
            <input
              id="inv-name"
              v-model="form.name"
              class="field-input"
              :class="{ 'is-invalid': formErrors.includes('Nombre') || nameWarning }"
              :maxlength="NAME_MAX_LENGTH"
              placeholder="Nombre del articulo"
              @beforeinput="blockNameChars"
              @input="cleanNameField"
            />
            <p v-if="nameWarning" class="inv-field-error">{{ nameWarning }}</p>
          </div>
          <div class="space-y-2">
            <label for="inv-category" class="inv-label">Categoria (Tipo)</label>
            <ExtensibleSelect
              id="inv-category"
              v-model="form.category"
              :options="categoryOptions"
              placeholder="Selecciona una categoria"
              add-label="Agregar nueva categoria"
              add-placeholder="Nombre de la categoria"
            />
          </div>
          <div class="space-y-2">
            <label for="inv-location" class="inv-label">Ubicacion</label>
            <ExtensibleSelect
              id="inv-location"
              v-model="form.location"
              :options="locationChoices"
              placeholder="Selecciona una ubicacion"
              add-label="Agregar nueva ubicacion"
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
              <button type="button" class="field-input flex shrink-0 items-center justify-center text-lg font-bold" style="width: 2.75rem; padding: 0" aria-label="Restar una unidad" @click="form.quantity = Math.max(0, Number(form.quantity || 0) - 1)">−</button>
              <input
                id="inv-quantity"
                v-model.number="form.quantity"
                type="text"
                inputmode="numeric"
                class="field-input flex-1 text-center"
                :class="{ 'is-invalid': formErrors.includes('Stock inicial') }"
                placeholder="0"
                @beforeinput="blockQuantityChars"
                @input="cleanIntegerField($event, 'quantity')"
              />
              <button type="button" class="field-input flex shrink-0 items-center justify-center text-lg font-bold" style="width: 2.75rem; padding: 0" aria-label="Sumar una unidad" @click="form.quantity = Number(form.quantity || 0) + 1">+</button>
            </div>
            <input v-else id="inv-quantity" :value="form.quantity" type="text" class="field-input cursor-not-allowed text-center opacity-70" readonly />
            <p v-if="numberWarning.quantity" class="inv-field-error">{{ numberWarning.quantity }}</p>
          </div>
          <div class="space-y-2">
            <label for="inv-min" class="flex items-center justify-between gap-2">
              <span class="inv-label">Stock minimo</span>
              <span v-if="Number(form.quantity || 0) <= Number(form.minQuantity || 0)" class="rounded-full border border-yellow-400/40 bg-yellow-100 px-2.5 py-0.5 text-[10px] font-black uppercase tracking-wide text-yellow-800">Alerta activa</span>
            </label>
            <input
              id="inv-min"
              v-model.number="form.minQuantity"
              type="text"
              inputmode="numeric"
              class="field-input"
              @beforeinput="blockMinChars"
              @input="cleanIntegerField($event, 'minQuantity')"
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
              <p>Alerta de stock minimo: el articulo entra en alerta cuando su stock es igual o menor a este valor (10 por defecto).{{ isTiendaForm ? ' El minimo de Tienda se edita en su producto.' : '' }}</p>
              <p v-if="editingId">
                El stock no se edita aqui: registra una entrada, salida o ajuste en la pestaña Movimientos.
                <span v-if="isTiendaForm" class="font-bold">Este articulo es la reserva de Tienda: para pasar unidades a la Tienda registra una salida con destino Tienda.</span>
              </p>
              <p v-else>
                El N° de articulo se genera automaticamente y el stock inicial queda registrado como una entrada en Movimientos.
                <span v-if="isTiendaForm" class="font-bold">Al ser Tipo "Tienda" se creara su producto en la tienda, sin stock y oculto hasta que le asignes precio.</span>
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
                Los articulos de Tienda cambian solos a Disponible, Stock bajo o Agotado segun su stock y su stock minimo en Inventario.
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

      <template #footer>
        <button type="button" class="rm-btn-secondary" @click="closeEditor">Cancelar</button>
        <button type="submit" class="rounded-2xl bg-amber-400 px-5 py-3 text-base font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300">
          {{ editingId ? 'Guardar cambios' : 'Agregar articulo' }}
        </button>
      </template>
    </ResourceModal>

    <ResourceModal
      :open="Boolean(detailItem)"
      :icon="Eye"
      eyebrow="Inventario · Detalles"
      :title="detailItem?.name || 'Articulo'"
      :subtitle="detailItem ? `N° de articulo ${detailItem.inventoryCode}` : ''"
      size="lg"
      @close="detailItem = null"
    >
      <template v-if="detailItem">
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="rm-section">
            <p class="rm-section-title" style="margin-bottom: 0.35rem">Stock</p>
            <p class="text-2xl font-black" :class="isLowStock(detailItem) ? 'text-rose-300' : 'text-white'">{{ detailItem.quantity }}</p>
            <p class="text-xs text-slate-400">{{ detailItem.unidad_venta || 'unidad' }} · minimo {{ detailItem.minQuantity || 0 }}</p>
          </div>
          <div class="rm-section">
            <p class="rm-section-title" style="margin-bottom: 0.35rem">Estado</p>
            <span class="inline-flex rounded-full border px-2.5 py-1 text-xs font-bold" :class="inventoryStatusClass(detailItem.status)">{{ detailItem.status }}</span>
          </div>
          <div class="rm-section">
            <p class="rm-section-title" style="margin-bottom: 0.35rem">Categoria</p>
            <p class="font-bold text-white">{{ detailItem.category || 'General' }}</p>
          </div>
        </div>

        <dl class="rm-section grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
          <div>
            <dt class="inv-label">Ubicacion</dt>
            <dd class="mt-1 text-slate-300">{{ detailItem.location || 'Sin ubicacion' }}</dd>
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
          <p class="rm-section-title"><History :size="14" aria-hidden="true" /> Ultimos movimientos</p>
          <ul v-if="detailMovements.length" class="divide-y divide-white/10 text-sm">
            <li v-for="movement in detailMovements" :key="movement.id_mov" class="flex items-center justify-between gap-3 py-2">
              <span class="text-slate-300">{{ movement.fecha_movimiento || 'Sin fecha' }}</span>
              <span class="rounded-full px-2.5 py-0.5 text-xs font-black capitalize" :class="movementClass(movement.tipo_movimiento)">{{ movement.tipo_movimiento }}</span>
              <span class="w-12 text-right font-bold text-white">{{ signedQuantity(movement) }}</span>
              <span class="hidden min-w-0 flex-1 truncate text-xs text-slate-400 sm:block">{{ movement.descripcion || 'Sin descripcion' }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-slate-400">Este articulo aun no tiene movimientos.</p>
        </div>
      </template>

      <template #footer>
        <button type="button" class="rm-btn-secondary" @click="detailItem = null">Cerrar</button>
        <button type="button" class="rounded-2xl bg-amber-400 px-5 py-3 font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300" @click="editFromDetails">
          Editar articulo
        </button>
      </template>
    </ResourceModal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { AlertCircle, Boxes, CheckCircle2, ClipboardCheck, Eye, History, Info, Package, TrendingDown, Wrench } from 'lucide-vue-next';
import InventoryMovementsPanel from '../components/inventory/InventoryMovementsPanel.vue';
import ResourceModal from '../components/ResourceModal.vue';
import ExtensibleSelect from '../components/common/ExtensibleSelect.vue';
import SortableTh from '../components/common/SortableTh.vue';
import TablePager from '../components/common/TablePager.vue';
import TableSearch from '../components/common/TableSearch.vue';
import { blockNonInteger, blockSpecialChars } from '../utils/inputGuards.js';
import {
  cleanInteger,
  cleanText,
  DEFAULT_PAGE_SIZE,
  matchesSearch,
  missingFields,
  missingFieldsMessage,
  NAME_MAX_LENGTH,
  sortRows,
  uniqueOptions,
} from '../../domain/utils/inputRules.js';
import { useGymStore } from '../../application/stores/gymStore';

const route = useRoute();
const router = useRouter();
const gymStore = useGymStore();
const tabs = [
  { value: 'articulos', label: 'Articulos' },
  { value: 'movimientos', label: 'Movimientos' },
];
const activeTab = computed({
  get: () => (tabs.some((tab) => tab.value === route.query.tab) ? route.query.tab : 'articulos'),
  set: (tab) => router.replace({ query: { ...route.query, tab } }),
});
const inventory = computed(() => gymStore.inventory);
// Articulos de Inventario (equipos y productos) con stock en su minimo o por debajo, agotados incluidos.
// Los descontinuados y dados de baja no se reponen, por eso no cuentan.
const lowStock = computed(() => inventory.value.filter(isLowStockAlert));
const maintenanceItems = computed(() => inventory.value.filter((item) => item.status === 'En mantenimiento').length);

// Unidades sugeridas por el TP2; se suman las que ya existen en la base.
const BASE_UNITS = ['Unidad', 'Paquete', 'Docena', 'Caja', 'Combo'];
const DEFAULT_MIN_QUANTITY = 10;

// Filtros de la tabla (solo lectura, no afectan el store).
const searchQuery = ref('');
const selectedCategory = ref('all');
const selectedLocation = ref('all');
const selectedStatus = ref('all');
const isLowStockFilter = ref(false);

/**
 * Activa o quita el filtro de articulos en stock minimo desde la tarjeta.
 */
const toggleLowStockFilter = () => {
  isLowStockFilter.value = !isLowStockFilter.value;
  if (isLowStockFilter.value) {
    selectedStatus.value = 'all';
    selectedCategory.value = 'all';
  }
  paginaActual.value = 1;
};

const locationOptions = computed(() => {
  const set = new Set(inventory.value.map((item) => item.location).filter(Boolean));
  return Array.from(set);
});
const categoryOptions = computed(() => uniqueOptions('Tienda', inventory.value.map((item) => item.category)));
const locationChoices = computed(() => uniqueOptions('Recepcion', locationOptions.value));
const unitOptions = computed(() => uniqueOptions(BASE_UNITS, inventory.value.map((item) => item.unidad_venta)));

// El buscador solo mira el N° de articulo y el nombre.
const filteredInventory = computed(() => inventory.value.filter((item) => {
  const matchesQuery = matchesSearch(searchQuery.value, [item.inventoryCode, item.name]);
  const matchesCategory = selectedCategory.value === 'all' || (item.category || 'General') === selectedCategory.value;
  const matchesLocation = selectedLocation.value === 'all' || item.location === selectedLocation.value;
  const matchesStatus = selectedStatus.value === 'all' || item.status === selectedStatus.value;
  const matchesLowStock = !isLowStockFilter.value || isLowStockAlert(item);
  return matchesQuery && matchesCategory && matchesLocation && matchesStatus && matchesLowStock;
}));

// Orden por columna: clic alterna ascendente y descendente.
const sortKey = ref('');
const sortDir = ref('asc');
const SORT_COLUMNS = {
  code: { accessor: (item) => item.inventoryCode, type: 'text' },
  name: { accessor: (item) => item.name, type: 'text' },
  quantity: { accessor: (item) => item.quantity, type: 'number' },
};
const toggleSort = (column) => {
  sortDir.value = sortKey.value === column && sortDir.value === 'asc' ? 'desc' : 'asc';
  sortKey.value = column;
  paginaActual.value = 1;
};
const sortedInventory = computed(() => {
  const column = SORT_COLUMNS[sortKey.value];
  return column ? sortRows(filteredInventory.value, column.accessor, sortDir.value, column.type) : filteredInventory.value;
});

// Paginacion (sobre la lista filtrada y ordenada).
const paginaActual = ref(1);
const porPagina = ref(DEFAULT_PAGE_SIZE);
const paginaInicio = computed(() => (paginaActual.value - 1) * porPagina.value);
const inventoryPaginado = computed(() => sortedInventory.value.slice(paginaInicio.value, paginaInicio.value + porPagina.value));

// Derivados de inventory, solo lectura.
const operationalPercent = computed(() => {
  if (!inventory.value.length) return 0;
  const operational = inventory.value.filter((item) => item.status === 'Operativo' || item.status === 'Disponible').length;
  return Math.round((operational / inventory.value.length) * 100);
});
const categorySummary = computed(() => {
  const counts = new Map();
  inventory.value.forEach((item) => {
    const key = item.category || 'General';
    counts.set(key, (counts.get(key) || 0) + 1);
  });
  return Array.from(counts.entries()).map(([name, count]) => ({ name, count }));
});
const editingId = ref('');
const isEditorOpen = ref(false);
const feedbackMessage = ref('');
const feedbackTone = ref('info');
const formErrors = ref([]);
const nameWarning = ref('');
const numberWarning = reactive({ quantity: '', minQuantity: '' });

const form = reactive({
  name: '',
  category: 'General',
  quantity: 0,
  minQuantity: DEFAULT_MIN_QUANTITY,
  unidad_venta: 'unidad',
  precio_venta: 0,
  location: 'Recepcion',
  status: 'Operativo',
  observations: '',
});

const isTiendaForm = computed(() => String(form.category || '').trim().toLowerCase() === 'tienda');
// En articulos de Tienda el estado lo calcula el backend; solo se marca o desmarca Descontinuado.
const isDiscontinuedForm = computed({
  get: () => form.status === 'Descontinuado',
  set: (value) => { form.status = value ? 'Descontinuado' : 'Disponible'; },
});
const statusPreview = computed(() => {
  if (!isTiendaForm.value || form.status === 'Descontinuado') return form.status;
  const current = inventory.value.find((item) => item.id === editingId.value)?.status;
  return editingId.value && current && current !== 'Descontinuado' ? current : 'Automatico';
});

const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success') return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50';
  if (feedbackTone.value === 'error') return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

/**
 * Valida los datos recibidos.
 */
const isLowStock = (item) => Number(item.quantity || 0) <= Number(item.minQuantity || 0);
const isLowStockAlert = (item) => isLowStock(item) && !['Descontinuado', 'Dado de baja'].includes(item.status);

/**
 * Ancho de la barra de stock respecto al minimo (3x el minimo = 100%).
 */
const stockBarPercent = (item) => {
  const min = Number(item.minQuantity ?? 1);
  const qty = Number(item.quantity || 0);
  const reference = Math.max(min * 3, 1);
  return Math.min(100, Math.round((qty / reference) * 100));
};

// Color del punto por categoria (categoria es texto libre, color estable segun el nombre).
const categoryDotPalette = ['#0d9488', '#7c3aed', '#2563eb', '#db2777', '#4f46e5'];
const categoryDotColor = (category) => {
  const key = category || 'General';
  let hash = 0;
  for (let i = 0; i < key.length; i += 1) hash = (hash + key.charCodeAt(i)) % categoryDotPalette.length;
  return categoryDotPalette[hash];
};

/**
 * Gestiona esta acción de la vista.
 */
const inventoryStatusClass = (status) => {
  if (status === 'Operativo') return 'bg-green-100 text-green-700 border-green-300';
  if (status === 'Disponible') return 'bg-blue-100 text-blue-700 border-blue-300';
  if (status === 'En mantenimiento') return 'bg-violet-100 text-violet-700 border-violet-300';
  if (status === 'Stock bajo') return 'bg-yellow-100 text-yellow-800 border-yellow-300';
  if (status === 'Agotado') return 'bg-rose-100 text-rose-700 border-rose-300';
  if (status === 'Descontinuado') return 'bg-slate-300 text-slate-600 border-slate-400 line-through';
  return 'bg-slate-200 text-slate-700 border-slate-300';
};

const currentInventoryCode = computed(() => {
  if (editingId.value) {
    return inventory.value.find((item) => item.id === editingId.value)?.inventoryCode || 'Se generara automaticamente';
  }

  return 'Se generara automaticamente';
});

// Bloqueo al escribir: nombre sin caracteres especiales y stock solo con enteros.
const blockNameChars = blockSpecialChars((message) => { nameWarning.value = message; });
const blockQuantityChars = blockNonInteger((message) => { numberWarning.quantity = message; });
const blockMinChars = blockNonInteger((message) => { numberWarning.minQuantity = message; });

const cleanNameField = (event) => {
  const { value, rejected } = cleanText(event.target.value, NAME_MAX_LENGTH);
  if (value !== event.target.value) {
    event.target.value = value;
    form.name = value;
  }
  nameWarning.value = rejected ? 'Sin caracteres especiales: solo letras, numeros y espacios.' : '';
  formErrors.value = formErrors.value.filter((label) => label !== 'Nombre');
};

const cleanIntegerField = (event, key) => {
  const value = cleanInteger(event.target.value);
  if (value !== event.target.value) event.target.value = value;
  form[key] = value === '' ? '' : Number(value);
  numberWarning[key] = '';
  if (key === 'quantity') formErrors.value = formErrors.value.filter((label) => label !== 'Stock inicial');
};

const clearFormWarnings = () => {
  formErrors.value = [];
  nameWarning.value = '';
  numberWarning.quantity = '';
  numberWarning.minQuantity = '';
};

/**
 * Gestiona esta acción de la vista.
 */
const resetForm = () => {
  editingId.value = '';
  form.name = '';
  form.category = 'General';
  form.quantity = 0;
  form.minQuantity = DEFAULT_MIN_QUANTITY;
  form.unidad_venta = 'unidad';
  form.precio_venta = 0;
  form.location = 'Recepcion';
  form.status = 'Operativo';
  form.observations = '';
  clearFormWarnings();
};

/**
 * Gestiona esta acción de la vista.
 */
const openNewItem = () => {
  resetForm();
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

/**
 * Gestiona esta acción de la vista.
 */
const closeEditor = () => {
  isEditorOpen.value = false;
  resetForm();
};

/**
 * Gestiona esta acción de la vista.
 */
const editItem = (item) => {
  editingId.value = item.id;
  form.name = item.name;
  form.category = item.category || 'General';
  form.quantity = Number(item.quantity || 0);
  form.minQuantity = Number(item.minQuantity ?? 1);
  form.unidad_venta = item.unidad_venta || 'unidad';
  form.precio_venta = Number(item.precio_venta || 0);
  form.location = item.location || 'Recepcion';
  form.status = item.status || 'Operativo';
  form.observations = item.observations || '';
  clearFormWarnings();
  feedbackMessage.value = '';
  isEditorOpen.value = true;
};

// Obligatorios: nombre siempre y stock inicial al crear.
const requiredFields = () => [
  { key: 'name', label: 'Nombre' },
  ...(editingId.value ? [] : [{ key: 'quantity', label: 'Stock inicial', isEmpty: (value) => value === '' || value === null || !Number.isInteger(Number(value)) }]),
];

/**
 * Gestiona esta acción de la vista.
 */
const handleSubmit = async () => {
  formErrors.value = missingFields(form, requiredFields());
  if (formErrors.value.length) return;
  try {
    await gymStore.upsertInventoryItem({
      id: editingId.value || undefined,
      ...form,
      name: form.name.trim(),
      minQuantity: Number(form.minQuantity || 0),
    });
    const savedLabel = editingId.value ? 'Articulo actualizado.' : 'Articulo registrado.';
    closeEditor();
    feedbackTone.value = 'success';
    feedbackMessage.value = savedLabel;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo guardar el articulo.';
  }
};

/**
 * Elimina el registro indicado.
 */
const deleteItem = async (id) => {
  if (!window.confirm('Eliminar este articulo?\n\nSi ya tiene movimientos o se vende en Tienda no se borrara: quedara como "Descontinuado" para conservar su historial.')) return;
  try {
    const result = await gymStore.deleteInventoryItem(id);
    feedbackTone.value = 'success';
    feedbackMessage.value = result?.accion === 'descontinuado'
      ? 'El articulo tiene historial o se vende en Tienda: se marco como Descontinuado.'
      : 'Articulo eliminado.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo eliminar el articulo.';
  }
};

// Detalles: datos del articulo y sus ultimos movimientos, solo lectura.
const detailItem = ref(null);
const itemNumber = (item) => Number(String(item?.id ?? '').replace('item-', ''));
const detailMovements = computed(() => {
  if (!detailItem.value) return [];
  const id = itemNumber(detailItem.value);
  return (gymStore.inventoryMovements || [])
    .filter((movement) => Number(movement.id_item) === id)
    .sort((a, b) => String(b.fecha_movimiento || '').localeCompare(String(a.fecha_movimiento || '')) || Number(b.id_mov || 0) - Number(a.id_mov || 0))
    .slice(0, 6);
});
const movementClass = (type) => {
  if (type === 'entrada') return 'bg-emerald-400/15 text-emerald-200';
  if (type === 'salida') return 'bg-rose-400/15 text-rose-200';
  return 'bg-cyan-400/15 text-cyan-200';
};
const signedQuantity = (movement) => {
  if (movement.tipo_movimiento === 'entrada') return `+${movement.cantidad}`;
  if (movement.tipo_movimiento === 'salida') return `-${movement.cantidad}`;
  return `= ${movement.cantidad}`;
};
const openDetails = (item) => {
  detailItem.value = item;
};
const editFromDetails = () => {
  const item = detailItem.value;
  detailItem.value = null;
  if (item) editItem(item);
};

onMounted(() => {
  gymStore.fetchFromBackend?.({ section: 'inventory' }).catch((error) => console.warn('No se pudo refrescar inventario:', error));
});
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
