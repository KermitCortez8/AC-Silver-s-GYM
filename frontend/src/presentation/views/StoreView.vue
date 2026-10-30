<template>
  <div class="workspace-view inv-store-theme space-y-6">

    <!-- ═══════════════════════════════════════════════
         HEADER
    ════════════════════════════════════════════════ -->
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p class="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.35em] text-slate-500">
            <span class="text-rose-400">Catálogo</span>
            <span class="text-slate-600">»</span>
            <span>{{ isAdmin ? 'Control de Productos de Tienda' : 'Tienda Online' }}</span>
          </p>
          <h1 class="mt-2 text-4xl font-black text-white">{{ isAdmin ? 'Tienda' : 'Tienda' }}</h1>
          <p class="mt-1.5 text-sm text-slate-400">
            {{ isAdmin ? 'Gestiona el catálogo de productos, precios, stock y estado de venta.' : 'Explora artículos, agrega al carrito y prepara tu compra.' }}
          </p>
        </div>

        <button
          v-if="isAdmin && activeTab === 'productos'"
          class="group flex items-center gap-2.5 self-start rounded-2xl bg-rose-600 px-5 py-3.5 text-sm font-black text-white shadow-lg shadow-rose-600/30 transition-all hover:bg-rose-500 hover:shadow-rose-500/40 xl:self-auto"
          @click="openNewProducto"
        >
          <svg class="h-4 w-4 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Ingresar Nuevo Artículo
        </button>
      </div>

      <nav v-if="isAdmin" class="mt-5 flex border-b border-white/10" aria-label="Secciones de tienda">
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

    <div v-if="!isAdmin" class="ws-panel store-toolbar">
      <div class="store-toolbar-search">
        <span class="ws-field-label">Buscar</span>
        <TableSearch
          v-model="productSearch"
          label="Buscar productos por nombre o categoría"
          placeholder="Buscar por nombre o categoría"
        />
      </div>
      <label>
        <span class="ws-field-label">Categoría</span>
        <select v-model="categoryFilter" class="inv-input">
          <option value="">Todas las categorías</option>
          <option v-for="category in categories" :key="category">{{ category }}</option>
        </select>
      </label>
      <label>
        <span class="ws-field-label">Ordenar por</span>
        <select v-model="clientSort" class="inv-input">
          <option value="recomendados">Recomendados</option>
          <option value="nombre">Nombre (A-Z)</option>
          <option value="precio-asc">Precio: menor a mayor</option>
          <option value="precio-desc">Precio: mayor a menor</option>
        </select>
      </label>
      <button
        type="button"
        class="store-fav-filter"
        :class="{ 'is-active': onlyFavorites }"
        :aria-pressed="onlyFavorites"
        @click="onlyFavorites = !onlyFavorites"
      >
        <Heart :size="16" :fill="onlyFavorites ? 'currentColor' : 'none'" aria-hidden="true" />
        Favoritos ({{ favoriteIds.length }})
      </button>
      <button v-if="hasClientFilters" type="button" class="inv-btn-ghost" @click="clearClientFilters">
        Limpiar filtros
      </button>
    </div>
    <p
      v-if="!isAdmin && feedbackMessage && !isProductEditorOpen"
      role="status"
      class="ws-notice"
      :class="feedbackToneClass"
    >
      {{ feedbackMessage }}
    </p>
    <StoreMovementsPanel v-if="isAdmin && activeTab === 'ventas'" />

    <StoreProductTable v-else-if="isAdmin" v-model:busqueda="busqueda" v-model:categoria-activa="categoriaActiva"
      v-model:filtro-estado="filtroEstado" v-model:pagina-actual="paginaActual" v-model:por-pagina="porPagina"
      :productos="productos" :categorias-unicas="categoriasUnicas" :categoria-dot-color="categoriaDotColor"
      :solo-stock-bajo="soloStockBajo" :sort-key="sortKey" :sort-dir="sortDir" :productos-filtrados="productosFiltrados"
      :productos-paginados="productosPaginados" :feedback-message="feedbackMessage" :feedback-tone-class="feedbackToneClass"
      :product-code="productCode" :is-product-low-stock="isProductLowStock" :product-status-class="productStatusClass"
      @toggle-stock="toggleStockBajo" @sort="toggleSort" @detail="detailProduct = $event" @edit="editProducto" @delete="deleteProducto" />

    <!-- ═══════════════════════════════════════════════
         CLIENTE — VISTA DE TIENDA (CARRITO)
    ════════════════════════════════════════════════ -->
    <StoreClientCatalog v-else :favorite-ids="favoriteIds" :is-favorite="isFavorite" :only-favorites="onlyFavorites"
      :can-buy="canBuy" :visible-products="visibleProducts" :has-client-filters="hasClientFilters"
      :available-for="availableFor" :stock-warning="stockWarning" :cart="cart" :cart-item-stock="cartItemStock"
      :cart-total="cartTotal" :cantidad-input="cantidadInput" @favorite="toggleFavorite" @detail="openClientDetail"
      @quantity-guard="blockQuantityChars" @quantity-change="setQuantity" @add="agregarAlCarrito"
      @remove="gymStore.removeFromCart" @clear="gymStore.clearCart" @update-cart="updateCart" @checkout="goToCheckout" />

    <!-- ═══════════════════════════════════════════════
         MODAL — INGRESAR / EDITAR PRODUCTO
    ════════════════════════════════════════════════ -->
    <!-- MODAL — DETALLE DEL PRODUCTO (cliente) -->
    <ResourceModal
      v-if="!isAdmin"
      :open="Boolean(clientDetail)"
      :icon="ShoppingBag"
      :eyebrow="clientDetail?.categoria || 'Tienda'"
      :title="clientDetail?.nombre || 'Producto'"
      size="lg"
      @close="clientDetail = null"
    >
      <template v-if="clientDetail">
        <div class="grid gap-5 sm:grid-cols-[minmax(0,240px)_1fr]">
          <div class="store-detail-image">
            <img v-if="clientDetail.imagen_url" :src="clientDetail.imagen_url" :alt="clientDetail.nombre" class="h-full w-full object-contain p-3" />
            <Package v-else :size="64" class="text-slate-500" aria-hidden="true" />
          </div>
          <div class="space-y-4">
            <p class="text-3xl font-black text-emerald-300">S/. {{ Number(clientDetail.precio || 0).toFixed(2) }}</p>
            <p class="text-sm leading-6 text-slate-300">{{ clientDetail.descripcion || 'Producto disponible en tienda.' }}</p>
            <dl class="grid grid-cols-2 gap-3 text-sm">
              <div class="rm-section">
                <dt class="inv-label">Disponibles</dt>
                <dd class="mt-1 text-lg font-black text-white">{{ clientDetail.cantidad }}</dd>
              </div>
              <div class="rm-section">
                <dt class="inv-label">Unidad</dt>
                <dd class="mt-1 text-lg font-black text-white">{{ clientDetail.unidad_venta || 'unidad' }}</dd>
              </div>
            </dl>
            <div v-if="canBuy(clientDetail)" class="space-y-2">
              <span class="inv-label">Cantidad</span>
              <div class="flex items-center gap-2">
                <button type="button" class="inv-btn-ghost h-11 w-11 text-lg" aria-label="Restar uno" @click="stepDetailQuantity(-1)">−</button>
                <input
                  :value="detailQuantity"
                  type="text"
                  inputmode="numeric"
                  aria-label="Cantidad"
                  class="inv-input w-20 text-center"
                  @beforeinput="blockQuantityChars"
                  @input="setDetailQuantity($event)"
                />
                <button
                  type="button"
                  class="inv-btn-ghost h-11 w-11 text-lg disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label="Sumar uno"
                  :disabled="detailQuantity >= availableFor(clientDetail)"
                  @click="stepDetailQuantity(1)"
                >+</button>
              </div>
              <p class="text-xs ws-muted">Máximo {{ availableFor(clientDetail) }}{{ inCart(clientDetail) ? ` (ya tienes ${inCart(clientDetail)} en tu carrito)` : '' }}</p>
              <p v-if="stockWarning[clientDetail.id_producto]" class="text-xs ws-warning">{{ stockWarning[clientDetail.id_producto] }}</p>
            </div>
            <p v-else class="inv-error">Este producto no está disponible por ahora.</p>
          </div>
        </div>
      </template>
      <template #footer>
        <button
          v-if="clientDetail"
          type="button"
          class="rm-btn-secondary inline-flex items-center justify-center gap-2"
          :aria-pressed="isFavorite(clientDetail.id_producto)"
          @click="toggleFavorite(clientDetail.id_producto)"
        >
          <Heart :size="16" :fill="isFavorite(clientDetail.id_producto) ? 'currentColor' : 'none'" aria-hidden="true" />
          {{ isFavorite(clientDetail.id_producto) ? 'En favoritos' : 'Agregar a favoritos' }}
        </button>
        <button
          v-if="clientDetail && canBuy(clientDetail)"
          type="button"
          class="rounded-2xl bg-amber-400 px-5 py-3 font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300"
          @click="addDetailToCart"
        >
          Agregar al carrito · S/. {{ (Number(clientDetail.precio || 0) * detailQuantity).toFixed(2) }}
        </button>
      </template>
    </ResourceModal>

    <!-- MODAL — DETALLES DEL PRODUCTO (solo lectura) -->
    <ResourceModal
      v-if="isAdmin"
      :open="Boolean(detailProduct)"
      :icon="Eye"
      eyebrow="Tienda · Detalles"
      :title="detailProduct?.nombre || 'Producto'"
      :subtitle="detailProduct ? `N° de producto ${productCode(detailProduct.id_producto)}` : ''"
      size="lg"
      @close="detailProduct = null"
    >
      <template v-if="detailProduct">
        <div class="grid gap-4 sm:grid-cols-[160px_1fr]">
          <div class="mx-auto flex aspect-square w-40 items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] p-2 sm:mx-0">
            <img v-if="detailProduct.imagen_url" :src="detailProduct.imagen_url" :alt="detailProduct.nombre" class="h-full w-full object-contain" />
            <Package v-else :size="40" class="text-slate-500" aria-hidden="true" />
          </div>
          <div class="grid content-start gap-3 sm:grid-cols-2">
            <div class="rm-section">
              <p class="rm-section-title" style="margin-bottom: 0.35rem">Precio</p>
              <p class="text-2xl font-black text-emerald-300">S/. {{ Number(detailProduct.precio || 0).toFixed(2) }}</p>
            </div>
            <div class="rm-section">
              <p class="rm-section-title" style="margin-bottom: 0.35rem">Stock en Tienda</p>
              <p class="text-2xl font-black" :class="isProductLowStock(detailProduct) ? 'text-rose-300' : 'text-white'">{{ detailProduct.cantidad }}</p>
              <p class="text-xs text-slate-400">{{ detailProduct.unidad_venta || 'unidad' }} · mínimo {{ detailProduct.minimo || 0 }}</p>
            </div>
            <div class="rm-section sm:col-span-2">
              <p class="rm-section-title" style="margin-bottom: 0.35rem">Estado</p>
              <span class="inline-flex rounded-full border px-2.5 py-1 text-xs font-bold" :class="productStatusClass(detailProduct.estado)">{{ detailProduct.estado }}</span>
            </div>
          </div>
        </div>
        <dl class="rm-section grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
          <div>
            <dt class="inv-label">Categoría</dt>
            <dd class="mt-1 text-slate-300">{{ detailProduct.categoria || 'General' }}</dd>
          </div>
          <div>
            <dt class="inv-label">Almacén</dt>
            <dd class="mt-1 text-slate-300">{{ detailProduct.id_item ? linkedItemName(detailProduct.id_item) : 'Sin vincular' }}</dd>
          </div>
          <div class="sm:col-span-2">
            <dt class="inv-label">Descripción</dt>
            <dd class="mt-1 text-slate-300">{{ detailProduct.descripcion || 'Sin descripción' }}</dd>
          </div>
        </dl>
      </template>
      <template #footer>
        <button type="button" class="rm-btn-secondary" @click="detailProduct = null">Cerrar</button>
        <button type="button" class="rounded-2xl bg-amber-400 px-5 py-3 font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300" @click="editFromDetails">
          Editar producto
        </button>
      </template>
    </ResourceModal>

    <ProductEditorDialog
      :category-options="productCategoryOptions"
      :unit-options="productUnitOptions"
      :form-errors="productFormErrors"
      :available-tienda-items="availableTiendaItems"
      :bucket-images="bucketImages"
      :clear-selected-image="clearSelectedImage"
      :close-bucket-picker="closeBucketPicker"
      :close-product-editor="closeProductEditor"
      :current-product-code="currentProductCode"
      :editing-id="editingId"
      :editing-linked="editingLinked"
      :feedback-message="feedbackMessage"
      :feedback-tone="feedbackTone"
      :form="form"
      :handle-local-image-upload="handleLocalImageUpload"
      :handle-submit="handleSubmit"
      :image-feedback="imageFeedback"
      :image-feedback-tone="imageFeedbackTone"
      :is-admin="isAdmin"
      :is-bucket-picker-open="isBucketPickerOpen"
      :is-loading-bucket-images="isLoadingBucketImages"
      :is-product-editor-open="isProductEditorOpen"
      :is-saving="isSaving"
      :is-uploading-image="isUploadingImage"
      :item-number="itemNumber"
      :linked-item-label="linkedItemLabel"
      :open-bucket-picker="openBucketPicker"
      :select-bucket-image="selectBucketImage"
      :stock-editable="stockEditable"
      :stock-mostrado="stockMostrado"
    />
  </div>
</template>

<script setup>
import StoreProductTable from '../components/store/StoreProductTable.vue';
import StoreClientCatalog from '../components/store/StoreClientCatalog.vue';

import ProductEditorDialog from '../components/store/ProductEditorDialog.vue';
import {
  Eye,
  Heart,
  Package,
  ShoppingBag,
} from 'lucide-vue-next';
import ResourceModal from '../components/ResourceModal.vue';

import TableSearch from '../components/common/TableSearch.vue';
import StoreMovementsPanel from '../components/store/StoreMovementsPanel.vue';
import { useStoreCatalog } from '../composables/store/useStoreCatalog.js';

const {
  route, router, gymStore, isAdmin, tabs,
  activeTab, productos, productSearch, categoryFilter, catalogProducts,
  categories, filteredProducts, authStore, favoriteOwner, favoriteIds,
  isFavorite, toggleFavorite, onlyFavorites, clientSort, canBuy,
  CLIENT_SORTS, visibleProducts, hasClientFilters, clearClientFilters, blockQuantityChars,
  inCart, availableFor, clampQuantity, stockWarning, warnStock,
  setQuantity, clientDetail, detailQuantity, openClientDetail, stepDetailQuantity,
  setDetailQuantity, addDetailToCart, inventario, cart, cartItemStock,
  cartTotal, busqueda, categoriaActiva, filtroEstado, categoriasUnicas,
  CATEGORY_COLORS, categoriaDotColor, soloStockBajo, sortKey, sortDir,
  SORT_COLUMNS, toggleSort, toggleStockBajo, productosFiltrados, paginaActual,
  porPagina, productosPaginados, detailProduct, linkedItemName, productCategoryOptions,
  productUnitOptions, editFromDetails, cantidadInput, feedbackMessage, feedbackTone,
  feedbackToneClass, productCode, isProductLowStock, productStatusClass, productStatusDot,
  stockBarColor, deleteProducto, cartError, updateCart, agregarAlCarrito,
  goToCheckout, isSaving, editingId, isProductEditorOpen, form,
  productFormErrors, currentProductCode, itemNumber, findItem, availableTiendaItems,
  editingLinked, linkedItemLabel, stockEditable, stockMostrado, resetForm,
  openNewProducto, closeProductEditor, editProducto, handleSubmit, imageFeedback,
  imageFeedbackTone, isUploadingImage, isBucketPickerOpen, isLoadingBucketImages, bucketImages,
  loadBucketImages, openBucketPicker, closeBucketPicker, selectBucketImage, clearSelectedImage,
  handleLocalImageUpload,
} = useStoreCatalog();
</script>

<style scoped src="../styles/store-view.css"></style>