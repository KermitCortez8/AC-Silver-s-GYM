<template>
  <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Estado</p>
        <h2 class="mt-2 text-2xl font-black text-white">Listado de productos</h2>
      </div>
    </div>

    <!-- Pills de categorías con punto de color (estilo Inventario) -->
    <div class="mt-5 flex flex-wrap gap-2.5">
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold transition"
        :class="categoriaActiva === '' ? 'border-rose-500 bg-rose-600 text-white' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'"
        @click="categoriaActiva = ''; paginaActual = 1"
      >
        Todas las categorías <span :class="categoriaActiva === '' ? 'text-white/70' : 'text-slate-500'">{{ productos.length }}</span>
      </button>
      <button
        v-for="cat in categoriasUnicas"
        :key="cat"
        type="button"
        class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-bold transition"
        :class="categoriaActiva === cat ? 'border-rose-500 bg-rose-600 text-white' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'"
        @click="categoriaActiva = cat; paginaActual = 1"
      >
        <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ background: categoriaDotColor(cat) }"></span>
        {{ cat }} <span :class="categoriaActiva === cat ? 'text-white/70' : 'text-slate-500'">{{ productos.filter(p => (p.categoria || 'General') === cat).length }}</span>
      </button>
    </div>

    <!-- Buscador (N° de producto y nombre) + select de estado -->
    <div class="mt-4 grid gap-3 sm:grid-cols-[1.5fr_1fr]">
      <TableSearch
        v-model="busqueda"
        label="Buscar productos por N° o nombre"
        placeholder="Buscar por N° de producto o nombre"
        @update:model-value="paginaActual = 1"
      />
      <select v-model="filtroEstado" class="field-input" aria-label="Filtrar por estado" @change="paginaActual = 1">
        <option value="">Todos los estados</option>
        <option>Disponible</option>
        <option>Agotado</option>
        <option>Descatalogado</option>
      </select>
    </div>
    <button v-if="soloStockBajo" type="button" class="inv-btn-ghost mt-3 inline-flex items-center gap-1.5 whitespace-nowrap" @click="$emit('toggle-stock')">
      Mostrando solo stock bajo <X :size="14" aria-hidden="true" />
    </button>

    <!-- Feedback -->
    <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
      {{ feedbackMessage }}
    </p>

    <!-- Tabla con min-w fijo para no romperse en zoom -->
    <div v-if="productosFiltrados.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm store-admin-table">
          <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
            <tr>
              <SortableTh class="px-5 py-4 font-bold" label="N° producto" column="code" :sort-key="sortKey" :sort-dir="sortDir" @sort="$emit('sort', $event)" />
              <SortableTh class="px-4 py-4 font-bold" label="Nombre" column="nombre" :sort-key="sortKey" :sort-dir="sortDir" @sort="$emit('sort', $event)" />
              <th class="px-4 py-4 font-bold">Imagen</th>
              <th class="px-4 py-4 font-bold">Categoría</th>
              <SortableTh class="px-4 py-4 font-bold" label="Precio" column="precio" numeric :sort-key="sortKey" :sort-dir="sortDir" @sort="$emit('sort', $event)" />
              <SortableTh class="px-4 py-4 font-bold" label="Stock" column="cantidad" numeric :sort-key="sortKey" :sort-dir="sortDir" @sort="$emit('sort', $event)" />
              <th class="px-4 py-4 font-bold">Estado</th>
              <th class="px-4 py-4 font-bold">Almacén</th>
              <th class="px-5 py-4 text-right font-bold">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/10">
            <tr v-for="producto in productosPaginados" :key="producto.id_producto" class="transition hover:bg-white/[0.04]">
              <td data-label="N° producto" class="whitespace-nowrap px-5 py-4 align-top">
                <span class="rounded-lg bg-amber-400/10 px-2.5 py-1 text-xs font-bold text-amber-200">
                  {{ productCode(producto.id_producto) }}
                </span>
              </td>
              <td data-label="Nombre" class="max-w-xs px-4 py-4 align-top">
                <p class="font-bold text-white">{{ producto.nombre }}</p>
                <p class="mt-1 line-clamp-1 text-xs leading-5 text-slate-400">
                  {{ producto.descripcion || 'Sin descripción' }}
                </p>
              </td>
              <td data-label="Imagen" class="px-4 py-4 align-top">
                <img
                  v-if="producto.imagen_url"
                  :src="producto.imagen_url"
                  :alt="producto.nombre"
                  class="h-14 w-14 rounded-xl border border-white/10 bg-slate-950/60 object-contain p-1"
                />
                <span v-else class="text-xs text-slate-500">Sin imagen</span>
              </td>
              <td data-label="Categoría" class="px-4 py-4 align-top">
                <span class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-slate-200">
                  <span class="h-1.5 w-1.5 shrink-0 rounded-full" :style="{ background: categoriaDotColor(producto.categoria || 'General') }"></span>
                  {{ producto.categoria || 'General' }}
                </span>
              </td>

              <!-- Precio -->
              <td data-label="Precio" class="whitespace-nowrap px-4 py-4 align-top font-black text-emerald-300">
                S/. {{ Number(producto.precio || 0).toFixed(2) }}
              </td>

              <!-- Stock -->
              <td data-label="Stock" class="px-4 py-4 align-top">
                <p class="font-bold" :class="isProductLowStock(producto) ? 'text-rose-300' : 'text-white'">
                  {{ producto.cantidad }} {{ producto.unidad_venta || 'unidad' }}
                </p>
                <p class="mt-1 text-xs text-slate-400">Mínimo: {{ producto.minimo || 0 }}</p>
              </td>

              <!-- Estado -->
              <td data-label="Estado" class="px-4 py-4 align-top">
                <span class="inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold" :class="productStatusClass(producto.estado)">
                  {{ producto.estado }}
                </span>
              </td>

              <!-- Almacen -->
              <td data-label="Almacén" class="px-4 py-4 align-top">
                <span v-if="producto.id_item" class="font-semibold text-orange-200">Item #{{ producto.id_item }}</span>
                <span v-else class="text-slate-500">Sin vincular</span>
              </td>

              <!-- Acciones -->
              <td data-label="Acciones" class="px-5 py-4 align-top">
                <div class="flex justify-end gap-2">
                  <button
                    class="inline-flex items-center gap-1.5 rounded-xl border border-sky-400/30 bg-sky-400/10 px-3 py-2 text-sm font-bold text-sky-200 transition hover:bg-sky-400/20"
                    @click="$emit('detail', producto)"
                  >
                    <Eye :size="15" aria-hidden="true" /> Detalles
                  </button>
                  <button
                    class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:border-white/20 hover:bg-white/5"
                    @click="$emit('edit', producto)"
                  >
                    Editar
                  </button>
                  <button
                    class="rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-300 transition hover:bg-rose-400/10"
                    @click="$emit('delete', producto.id_producto)"
                  >
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
      :total="productosFiltrados.length"
      item-label="productos"
    />

    <!-- Empty state -->
    <div v-if="!productosFiltrados.length" class="mt-6 rounded-2xl border border-dashed border-white/10 px-6 py-14 text-center">
      <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-slate-900">
        <svg class="h-6 w-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 3H8l-2 4h12l-2-4z" />
        </svg>
      </div>
      <p class="text-sm font-semibold text-slate-300">{{ busqueda || categoriaActiva ? 'Sin resultados' : 'Sin productos registrados' }}</p>
      <p class="mt-1 text-xs text-slate-500">{{ busqueda || categoriaActiva ? 'Prueba con otro término o categoría.' : 'Usa "Ingresar Nuevo Artículo" para agregar el primero.' }}</p>
    </div>
  </section>
</template>
<script setup>
import SortableTh from '../common/SortableTh.vue';
import TablePager from '../common/TablePager.vue';
import TableSearch from '../common/TableSearch.vue';
import { Eye, X } from 'lucide-vue-next';
const busqueda = defineModel('busqueda', { type: String });
const categoriaActiva = defineModel('categoriaActiva', { type: String });
const filtroEstado = defineModel('filtroEstado', { type: String });
const paginaActual = defineModel('paginaActual', { type: Number });
const porPagina = defineModel('porPagina', { type: Number });
defineProps({
  productos: Array, categoriasUnicas: Array, categoriaDotColor: Function, soloStockBajo: Boolean,
  sortKey: String, sortDir: String, productosFiltrados: Array, productosPaginados: Array,
  feedbackMessage: String, feedbackToneClass: String, productCode: Function,
  isProductLowStock: Function, productStatusClass: Function,
});
defineEmits(['toggle-stock', 'sort', 'detail', 'edit', 'delete']);
</script>
<style scoped src="../../styles/store-view.css"></style>
