<template>
  <div class="workspace-view space-y-6">
    <section class="ws-panel ws-hero">
      <div
        class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between"
      >
        <div>
          <p class="ws-eyebrow">Catálogo</p>
          <h1 class="ws-title">
            {{ isAdmin ? 'Tienda del gimnasio' : 'Tienda' }}
          </h1>
          <p class="mt-2 ws-soft">
            {{
              isAdmin
                ? 'Administra el catalogo de productos disponibles.'
                : 'Explora artículos, agrega al carrito y prepara tu compra.'
            }}
          </p>
        </div>

        <button
          v-if="isAdmin"
          class="rounded-2xl ws-primary px-5 py-3 text-sm font-black ws-onaccent shadow-lg transition ws-primary-hover"
          @click="openNewProducto"
        >
          Nuevo producto
        </button>
      </div>
    </section>

    <div class="ws-panel flex flex-col gap-4 sm:flex-row sm:items-end">
      <label class="ws-search"
        ><span class="sr-only">Buscar productos</span
        ><Search :size="18" /><input
          v-model="productSearch"
          type="search"
          class="ws-input"
          placeholder="Busca por nombre o categoría"
      /></label>
      <label class="sm:w-52"
        ><span class="ws-field-label">Categoría</span
        ><select v-model="categoryFilter" class="ws-input">
          <option value="">Todas las categorías</option>
          <option v-for="category in categories" :key="category">
            {{ category }}
          </option>
        </select></label
      >
      <button
        v-if="productSearch || categoryFilter"
        class="ws-btn"
        @click="
          productSearch = '';
          categoryFilter = '';
        "
      >
        Limpiar filtros
      </button>
    </div>
    <p
      v-if="feedbackMessage && !isProductEditorOpen"
      role="status"
      class="ws-notice"
      :class="feedbackToneClass"
    >
      {{ feedbackMessage }}
    </p>
    <section v-if="isAdmin" class="ws-panel">
      <div
        class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"
      >
        <div>
          <p class="ws-eyebrow">Catálogo</p>
          <h2 class="mt-2 text-2xl font-black ws-text">Listado de productos</h2>
        </div>
        <div class="rounded-2xl ws-inset px-4 py-3 text-right">
          <p class="text-xs ws-muted">Total productos</p>
          <p class="text-xl font-black ws-text">{{ productos.length }}</p>
        </div>
      </div>

      <div
        v-if="filteredProducts.length"
        class="mt-5 overflow-hidden rounded-2xl border ws-border ws-inset"
      >
        <div class="overflow-x-auto">
          <table class="ws-table store-admin-table">
            <thead
              class="border-b ws-border ws-inset text-xs uppercase tracking-[0.16em] ws-muted"
            >
              <tr>
                <th class="px-5 py-4 font-bold">Producto</th>
                <th class="px-4 py-4 font-bold">Imagen</th>
                <th class="px-4 py-4 font-bold">Categoría</th>
                <th class="px-4 py-4 font-bold">Precio</th>
                <th class="px-4 py-4 font-bold">Stock</th>
                <th class="px-4 py-4 font-bold">Estado</th>
                <th class="px-4 py-4 font-bold">Almacén</th>
                <th class="px-5 py-4 text-right font-bold">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y ws-divide">
              <tr
                v-for="producto in filteredProducts"
                :key="producto.id_producto"
                class="transition ws-hover"
              >
                <td data-label="Producto" class="max-w-sm px-5 py-4 align-top">
                  <div class="flex items-start gap-3">
                    <span
                      class="mt-0.5 rounded-lg ws-tint-warning px-2.5 py-1 text-xs font-black ws-warning"
                    >
                      {{ productCode(producto.id_producto) }}
                    </span>
                    <div class="min-w-0">
                      <p class="font-bold ws-text">{{ producto.nombre }}</p>
                      <p class="mt-1 line-clamp-2 text-xs leading-5 ws-muted">
                        {{ producto.descripcion || 'Sin descripción' }}
                      </p>
                    </div>
                  </div>
                </td>
                <td data-label="Imagen" class="px-4 py-4 align-top">
                  <img
                    v-if="producto.imagen_url"
                    :src="producto.imagen_url"
                    :alt="producto.nombre"
                    class="h-14 w-14 rounded-xl border ws-border ws-surface object-contain p-1"
                  />
                  <span v-else class="text-xs ws-muted">Sin imagen</span>
                </td>
                <td data-label="Categoría" class="px-4 py-4 align-top ws-soft">
                  {{ producto.categoria || 'General' }}
                </td>
                <td
                  data-label="Precio"
                  class="whitespace-nowrap px-4 py-4 align-top font-black ws-success"
                >
                  S/. {{ Number(producto.precio || 0).toFixed(2) }}
                </td>
                <td data-label="Stock" class="px-4 py-4 align-top">
                  <p
                    class="font-bold"
                    :class="
                      isProductLowStock(producto) ? 'ws-danger' : 'ws-text'
                    "
                  >
                    {{ producto.cantidad }}
                    {{ producto.unidad_venta || 'unidad' }}
                  </p>
                  <p class="mt-1 text-xs ws-muted">
                    Mínimo: {{ producto.minimo || 0 }}
                  </p>
                </td>
                <td data-label="Estado" class="px-4 py-4 align-top">
                  <span
                    class="inline-flex rounded-full border px-2.5 py-1 text-xs font-bold"
                    :class="productStatusClass(producto.estado)"
                  >
                    {{ producto.estado }}
                  </span>
                </td>
                <td data-label="Almacén" class="px-4 py-4 align-top">
                  <span v-if="producto.id_item" class="font-semibold ws-warning"
                    >Item #{{ producto.id_item }}</span
                  >
                  <span v-else class="ws-muted">Sin vincular</span>
                </td>
                <td data-label="Acciones" class="px-5 py-4 align-top">
                  <div class="flex justify-end gap-2">
                    <button
                      class="rounded-xl border ws-border px-3 py-2 text-sm font-bold ws-text transition ws-hover"
                      @click="editProducto(producto)"
                    >
                      Editar
                    </button>
                    <button
                      class="rounded-xl border ws-border-danger px-3 py-2 text-sm font-bold ws-danger transition ws-hover-danger"
                      @click="deleteProducto(producto.id_producto)"
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

      <p
        v-if="!filteredProducts.length"
        class="mt-6 rounded-2xl border border-dashed ws-border p-8 text-center text-sm ws-muted"
      >
        {{
          productos.length
            ? 'No encontramos productos con esos filtros. Prueba otra búsqueda.'
            : 'Aún no hay productos. Usa «Nuevo producto» para crear el primero.'
        }}
      </p>
    </section>

    <section v-else class="space-y-6">
      <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div class="space-y-4">
          <div
            class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"
          >
            <div>
              <p class="ws-eyebrow">Para tu entrenamiento</p>
              <h2 class="mt-2 text-2xl font-black ws-text">
                Encuentra tu complemento ideal
              </h2>
            </div>
            <div class="rounded-2xl ws-inset px-4 py-3 text-right">
              <p class="text-xs ws-muted">Productos</p>
              <p class="text-xl font-black ws-text">
                {{ visibleProducts.length }}
              </p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <article
              v-for="producto in visibleProducts"
              :key="producto.id_producto"
              class="ws-panel store-product-card"
            >
              <div
                class="store-product-image mb-3 flex aspect-square items-center justify-center overflow-hidden rounded-xl border ws-border-warning ws-tint-warning"
              >
                <img
                  v-if="producto.imagen_url"
                  :src="producto.imagen_url"
                  :alt="producto.nombre"
                  class="h-full w-full object-contain p-2"
                />
                <div v-else class="text-center">
                  <p class="text-xs uppercase tracking-[0.25em] ws-warning">
                    {{ producto.categoria }}
                  </p>
                  <Package
                    :size="48"
                    class="mx-auto mt-3 ws-muted"
                    aria-hidden="true"
                  />
                </div>
              </div>
              <p class="font-semibold ws-text">{{ producto.nombre }}</p>
              <p class="mt-1 line-clamp-2 text-sm ws-muted">
                {{ producto.descripcion || 'Producto disponible en tienda.' }}
              </p>
              <p class="mt-3 text-lg font-black ws-success">
                S/. {{ Number(producto.precio || 0).toFixed(2) }}
              </p>
              <p class="mt-1 text-xs ws-muted">
                Stock: {{ producto.cantidad }}
              </p>

              <div
                v-if="
                  producto.estado === 'Disponible' &&
                  Number(producto.cantidad || 0) > 0
                "
                class="mt-4 flex gap-2"
              >
                <input
                  :value="cantidadInput[producto.id_producto] ?? 1"
                  @input="
                    cantidadInput[producto.id_producto] = Number(
                      $event.target.value,
                    )
                  "
                  :aria-label="`Cantidad de ${producto.nombre}`"
                  type="number"
                  min="1"
                  :max="producto.cantidad"
                  class="ws-input flex-1 px-3 py-2 text-sm"
                />
                <button
                  class="flex-1 rounded-xl ws-primary px-3 py-2 text-sm font-bold ws-onaccent transition ws-primary-hover"
                  @click="agregarAlCarrito(producto)"
                >
                  Agregar
                </button>
              </div>
              <div
                v-else
                class="mt-4 rounded-xl ws-inset px-3 py-2 text-center text-sm ws-muted"
              >
                {{
                  producto.estado !== 'Disponible' ? producto.estado : 'Agotado'
                }}
              </div>
            </article>
          </div>

          <p
            v-if="!visibleProducts.length"
            class="rounded-2xl border border-dashed ws-border p-10 text-center text-sm ws-muted"
          >
            {{
              productSearch || categoryFilter
                ? 'No encontramos productos con esos filtros. Prueba otra búsqueda.'
                : 'Pronto encontrarás nuevos productos aquí.'
            }}
          </p>
        </div>

        <aside class="h-fit ws-panel xl:sticky xl:top-4">
          <p class="ws-eyebrow">Carrito</p>
          <h2 class="mt-2 text-2xl font-black ws-text">Mi compra</h2>

          <div class="mt-5 max-h-96 space-y-3 overflow-y-auto">
            <article
              v-for="item in cart"
              :key="item.id_producto"
              class="rounded-2xl border ws-border ws-inset p-3"
            >
              <div class="flex items-start justify-between gap-2">
                <img
                  v-if="item.imagen_url"
                  :src="item.imagen_url"
                  :alt="item.nombre"
                  class="h-12 w-12 rounded-xl border ws-border ws-surface object-contain p-1"
                />
                <div class="min-w-0 flex-1">
                  <p class="truncate font-semibold ws-text">
                    {{ item.nombre }}
                  </p>
                  <p class="mt-1 text-sm ws-success">
                    S/. {{ Number(item.precio || 0).toFixed(2) }}
                  </p>
                </div>
                <button
                  class="rounded-full ws-tint-danger px-2 py-1 text-sm font-bold ws-danger hover:bg-rose-500 ws-hover-text"
                  :aria-label="`Quitar ${item.nombre} del carrito`"
                  @click="() => gymStore.removeFromCart(item.id_producto)"
                >
                  x
                </button>
              </div>

              <div class="mt-3 flex items-center gap-2">
                <button
                  class="rounded ws-inset px-2 py-1 text-sm ws-text ws-hover"
                  :aria-label="`Reducir cantidad de ${item.nombre}`"
                  @click="
                    () =>
                      gymStore.updateCartQuantity(
                        item.id_producto,
                        Math.max(1, item.cantidad - 1),
                      )
                  "
                >
                  -
                </button>
                <input
                  :value="item.cantidad"
                  :aria-label="`Cantidad de ${item.nombre} en el carrito`"
                  type="number"
                  min="1"
                  class="w-full rounded ws-inset px-2 py-1 text-center text-sm ws-text outline-none"
                  @change="
                    (event) =>
                      gymStore.updateCartQuantity(
                        item.id_producto,
                        Math.max(1, Number(event.target.value)),
                      )
                  "
                />
                <button
                  class="rounded ws-inset px-2 py-1 text-sm ws-text ws-hover"
                  :aria-label="`Aumentar cantidad de ${item.nombre}`"
                  @click="
                    () =>
                      gymStore.updateCartQuantity(
                        item.id_producto,
                        item.cantidad + 1,
                      )
                  "
                >
                  +
                </button>
              </div>

              <p class="mt-2 text-right text-sm ws-soft">
                Subtotal: S/.
                {{
                  (
                    Number(item.precio || 0) * Number(item.cantidad || 0)
                  ).toFixed(2)
                }}
              </p>
            </article>

            <p
              v-if="!cart.length"
              class="rounded-2xl border border-dashed ws-border p-6 text-center text-sm ws-muted"
            >
              Tu carrito esta vacio.
            </p>
          </div>

          <div
            v-if="cart.length"
            class="mt-6 space-y-3 border-t ws-border pt-4"
          >
            <div class="flex justify-between text-sm">
              <p class="ws-soft">Subtotal:</p>
              <p class="font-semibold ws-text">
                S/. {{ cartTotal.subtotal.toFixed(2) }}
              </p>
            </div>
            <div class="flex justify-between text-sm">
              <p class="ws-soft">IGV (18%):</p>
              <p class="font-semibold ws-success">
                S/. {{ cartTotal.igv.toFixed(2) }}
              </p>
            </div>
            <div class="flex justify-between border-t ws-border pt-3">
              <p class="font-black ws-text">Total:</p>
              <p class="text-xl font-black ws-warning">
                S/. {{ cartTotal.total.toFixed(2) }}
              </p>
            </div>

            <button
              class="mt-4 w-full rounded-2xl ws-primary px-4 py-3 font-bold ws-onaccent transition ws-primary-hover"
              @click="goToCheckout"
            >
              Procesar compra
            </button>
            <button
              class="w-full rounded-2xl border ws-border ws-surface px-4 py-3 font-bold ws-text transition ws-hover"
              @click="() => gymStore.clearCart()"
            >
              Limpiar carrito
            </button>
          </div>
        </aside>
      </div>
    </section>

    <WorkspaceDialog
      :open="isAdmin && isProductEditorOpen"
      :title="editingId ? 'Editar producto' : 'Nuevo producto'"
      :busy="isSaving || isUploadingImage"
      @close="closeProductEditor"
    >
      <form @submit.prevent="handleSubmit">
        <fieldset :disabled="isSaving">
          <div
            class="mt-4 rounded-2xl border ws-border-warning ws-tint-warning px-4 py-3 text-sm ws-warning"
          >
            <p class="text-xs uppercase tracking-[0.35em] ws-warning">
              Identificador unico
            </p>
            <p class="mt-1 font-semibold ws-text">{{ currentProductCode }}</p>
          </div>

          <div class="mt-5 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm ws-soft">Nombre del producto</span>
              <input
                required
                v-model="form.nombre"
                class="ws-input"
                placeholder="Proteina Whey, Bebida Energetica, etc."
              />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm ws-soft">Descripcion</span>
              <textarea
                v-model="form.descripcion"
                rows="2"
                class="ws-input"
                placeholder="Descripcion breve del producto..."
              ></textarea>
            </label>
            <label class="space-y-2">
              <span class="text-sm ws-soft">Categoría</span>
              <input
                v-model="form.categoria"
                class="ws-input"
                placeholder="Suplementos, Bebidas..."
              />
            </label>
            <label class="space-y-2">
              <span class="text-sm ws-soft">Item de almacen</span>
              <select v-model.number="form.id_item" class="ws-input">
                <option :value="null">Sin vincular</option>
                <option
                  v-for="item in inventario"
                  :key="item.id"
                  :value="Number(String(item.id).replace('item-', ''))"
                >
                  {{ item.inventoryCode }} - {{ item.name }}
                </option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-sm ws-soft">Unidad de venta</span>
              <input
                v-model="form.unidad_venta"
                class="ws-input"
                placeholder="unidad, botella, paquete..."
              />
            </label>
            <label class="space-y-2">
              <span class="text-sm ws-soft">Precio (S/.)</span>
              <input
                v-model.number="form.precio"
                type="number"
                min="0"
                step="0.01"
                class="ws-input"
              />
            </label>
            <label class="space-y-2">
              <span class="text-sm ws-soft">Cantidad en stock</span>
              <input
                v-model.number="form.cantidad"
                type="number"
                min="0"
                class="ws-input"
              />
            </label>
            <label class="space-y-2">
              <span class="text-sm ws-soft">Stock minimo</span>
              <input
                v-model.number="form.minimo"
                type="number"
                min="0"
                class="ws-input"
              />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm ws-soft">Estado</span>
              <select v-model="form.estado" class="ws-input">
                <option>Disponible</option>
                <option>Agotado</option>
                <option>Descatalogado</option>
              </select>
            </label>
            <div class="space-y-3 sm:col-span-2">
              <span class="text-sm ws-soft">Imagen del producto</span>
              <div class="grid gap-4 lg:grid-cols-[180px_1fr]">
                <div
                  class="flex aspect-square items-center justify-center overflow-hidden rounded-2xl border ws-border ws-inset p-2"
                >
                  <img
                    v-if="form.imagen_url"
                    :src="form.imagen_url"
                    :alt="form.nombre || 'Producto'"
                    class="h-full w-full object-contain"
                  />
                  <div v-else class="px-4 text-center text-xs ws-muted">
                    Sin imagen seleccionada
                  </div>
                </div>
                <div class="space-y-3">
                  <div class="flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="rounded-xl border ws-border-warning ws-tint-warning px-4 py-2 text-sm font-bold ws-warning transition ws-hover"
                      :disabled="isLoadingBucketImages"
                      @click="openBucketPicker"
                    >
                      {{
                        isLoadingBucketImages
                          ? 'Cargando...'
                          : 'Elegir de la galería'
                      }}
                    </button>
                    <button
                      v-if="form.imagen_url"
                      type="button"
                      class="rounded-xl border ws-border px-4 py-2 text-sm font-bold ws-text transition ws-hover"
                      @click="clearSelectedImage"
                    >
                      Quitar imagen
                    </button>
                  </div>
                  <label class="block space-y-2">
                    <span class="text-xs uppercase tracking-[0.22em] ws-muted"
                      >Subir desde tu dispositivo</span
                    >
                    <input
                      type="file"
                      accept="image/*"
                      class="ws-input"
                      :disabled="isUploadingImage"
                      @change="handleLocalImageUpload"
                    />
                  </label>
                  <p
                    v-if="isUploadingImage"
                    class="text-xs font-semibold ws-warning"
                  >
                    Subiendo imagen…
                  </p>
                  <div
                    v-if="isBucketPickerOpen"
                    class="ws-panel store-product-card"
                  >
                    <div class="mb-3 flex items-center justify-between gap-3">
                      <div>
                        <p class="text-xs uppercase tracking-[0.22em] ws-muted">
                          Galería de imágenes
                        </p>
                        <p class="mt-1 text-sm font-semibold ws-text">
                          Imágenes disponibles
                        </p>
                      </div>
                      <button
                        type="button"
                        class="rounded-xl border ws-border px-3 py-2 text-xs font-bold ws-text ws-hover"
                        @click="closeBucketPicker"
                      >
                        Cerrar
                      </button>
                    </div>
                    <div
                      v-if="bucketImages.length"
                      class="grid max-h-56 grid-cols-3 gap-3 overflow-y-auto sm:grid-cols-4"
                    >
                      <button
                        v-for="image in bucketImages"
                        :key="image.path || image.name"
                        type="button"
                        class="overflow-hidden rounded-xl border transition ws-hover-border"
                        :class="
                          form.imagen_url === image.url
                            ? 'ws-border-warning ring-2 ws-ring'
                            : 'ws-border'
                        "
                        @click="selectBucketImage(image)"
                      >
                        <img
                          :src="image.url"
                          :alt="image.name"
                          class="aspect-square h-full w-full object-contain ws-inset p-1"
                        />
                        <p class="truncate px-2 py-1 text-[10px] ws-muted">
                          {{ image.name }}
                        </p>
                      </button>
                    </div>
                    <p
                      v-else
                      class="rounded-xl border border-dashed ws-border px-4 py-6 text-center text-xs ws-muted"
                    >
                      Todavía no hay imágenes en la galería.
                    </p>
                  </div>
                  <p
                    v-if="imageFeedback"
                    class="rounded-xl border px-3 py-2 text-xs"
                    :class="
                      imageFeedbackTone === 'error'
                        ? 'ws-border-danger ws-tint-danger ws-danger'
                        : 'ws-border-success ws-tint-success ws-success'
                    "
                  >
                    {{ imageFeedback }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <p
            v-if="feedbackMessage && feedbackTone === 'error'"
            role="alert"
            class="ws-notice ws-tint-danger ws-danger mt-4"
          >
            {{ feedbackMessage }}
          </p>
          <button
            :disabled="isSaving || isUploadingImage"
            type="submit"
            class="mt-6 w-full rounded-2xl ws-primary px-4 py-3 font-bold ws-onaccent transition ws-primary-hover"
          >
            {{
              isSaving
                ? 'Guardando…'
                : editingId
                  ? 'Guardar cambios'
                  : 'Agregar producto'
            }}
          </button>
        </fieldset>
      </form>
    </WorkspaceDialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { Package, Search } from 'lucide-vue-next';
import WorkspaceDialog from '../components/WorkspaceDialog.vue';
import { useRoute, useRouter } from 'vue-router';
import { useGymStore } from '../stores/gymStore';
import {
  uploadStoreImage,
  listStoreImages,
} from '../services/storeImageService';

const route = useRoute();
const router = useRouter();
const gymStore = useGymStore();

const isAdmin = computed(() => route.path.startsWith('/admin/store'));
const productos = computed(() => gymStore.productos_tienda);
const productSearch = ref('');
const categoryFilter = ref('');
const isSaving = ref(false);
const catalogProducts = computed(() =>
  isAdmin.value
    ? productos.value
    : productos.value.filter((p) => p.estado !== 'Descatalogado'),
);
const categories = computed(() =>
  [
    ...new Set(catalogProducts.value.map((p) => p.categoria || 'General')),
  ].sort(),
);
const filteredProducts = computed(() => {
  const query = productSearch.value.trim().toLocaleLowerCase('es');
  return catalogProducts.value.filter(
    (p) =>
      (!categoryFilter.value ||
        (p.categoria || 'General') === categoryFilter.value) &&
      (!query ||
        `${p.nombre} ${p.categoria || 'General'} ${p.descripcion || ''}`
          .toLocaleLowerCase('es')
          .includes(query)),
  );
});
const visibleProducts = computed(() => filteredProducts.value);
const inventario = computed(() => gymStore.inventory);
const cart = computed(() => gymStore.cart);
const cartTotal = computed(() => gymStore.cartTotal);

const editingId = ref('');
const isProductEditorOpen = ref(false);
const cantidadInput = ref({});
const feedbackMessage = ref('');
const feedbackTone = ref('info');
const imageFeedback = ref('');
const imageFeedbackTone = ref('success');
const isUploadingImage = ref(false);
const isBucketPickerOpen = ref(false);
const isLoadingBucketImages = ref(false);
const bucketImages = ref([]);

const form = reactive({
  nombre: '',
  descripcion: '',
  categoria: 'General',
  id_item: null,
  unidad_venta: 'unidad',
  precio: 0,
  cantidad: 0,
  minimo: 5,
  estado: 'Disponible',
  imagen_url: '',
});

const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success')
    return 'ws-border-success ws-tint-success ws-success';
  if (feedbackTone.value === 'error')
    return 'ws-border-danger ws-tint-danger ws-danger';
  return 'ws-border-info ws-tint-info ws-info';
});

const currentProductCode = computed(() => {
  if (editingId.value) {
    return productCode(editingId.value);
  }
  return 'Se generara automaticamente';
});

/**
 * Gestiona esta acción de la vista.
 */
const productCode = (id) => `PROD-${String(id || 0).padStart(4, '0')}`;

/**
 * Valida los datos recibidos.
 */
const isProductLowStock = (producto) =>
  Number(producto.cantidad || 0) <= Number(producto.minimo || 0);

/**
 * Gestiona esta acción de la vista.
 */
const productStatusClass = (status) => {
  if (status === 'Disponible')
    return 'ws-border-success ws-tint-success ws-success';
  if (status === 'Agotado') return 'ws-border-danger ws-tint-danger ws-danger';
  return 'ws-border-warning ws-tint-warning ws-warning';
};

/**
 * Gestiona esta acción de la vista.
 */
const resetForm = () => {
  editingId.value = '';
  form.nombre = '';
  form.descripcion = '';
  form.categoria = 'General';
  form.id_item = null;
  form.unidad_venta = 'unidad';
  form.precio = 0;
  form.cantidad = 0;
  form.minimo = 5;
  form.estado = 'Disponible';
  form.imagen_url = '';
  imageFeedback.value = '';
  isBucketPickerOpen.value = false;
  bucketImages.value = [];
};

/**
 * Gestiona esta acción de la vista.
 */
const openNewProducto = () => {
  resetForm();
  feedbackMessage.value = '';
  isProductEditorOpen.value = true;
};

/**
 * Gestiona esta acción de la vista.
 */
const closeProductEditor = () => {
  if (isSaving.value || isUploadingImage.value) return;
  isProductEditorOpen.value = false;
  resetForm();
};

/**
 * Gestiona esta acción de la vista.
 */
const editProducto = (producto) => {
  editingId.value = producto.id_producto;
  form.nombre = producto.nombre;
  form.descripcion = producto.descripcion || '';
  form.categoria = producto.categoria || 'General';
  form.id_item = producto.id_item || null;
  form.unidad_venta = producto.unidad_venta || 'unidad';
  form.precio = Number(producto.precio || 0);
  form.cantidad = Number(producto.cantidad || 0);
  form.minimo = Number(producto.minimo || 5);
  form.estado = producto.estado || 'Disponible';
  form.imagen_url = producto.imagen_url || '';
  feedbackMessage.value = '';
  imageFeedback.value = '';
  isBucketPickerOpen.value = false;
  isProductEditorOpen.value = true;
};

/**
 * Consulta los datos del servidor.
 */
const loadBucketImages = async () => {
  isLoadingBucketImages.value = true;
  try {
    bucketImages.value = await listStoreImages();
  } catch (error) {
    imageFeedbackTone.value = 'error';
    imageFeedback.value =
      error instanceof Error
        ? error.message
        : 'No se pudieron cargar las imagenes del bucket.';
    bucketImages.value = [];
  } finally {
    isLoadingBucketImages.value = false;
  }
};

/**
 * Gestiona esta acción de la vista.
 */
const openBucketPicker = async () => {
  isBucketPickerOpen.value = true;
  if (!bucketImages.value.length) {
    await loadBucketImages();
  }
};

/**
 * Gestiona esta acción de la vista.
 */
const closeBucketPicker = () => {
  isBucketPickerOpen.value = false;
};

/**
 * Gestiona esta acción de la vista.
 */
const selectBucketImage = (image) => {
  form.imagen_url = image.url;
  imageFeedbackTone.value = 'success';
  imageFeedback.value = `Imagen seleccionada: ${image.name}`;
  isBucketPickerOpen.value = false;
};

/**
 * Elimina el registro indicado.
 */
const clearSelectedImage = () => {
  form.imagen_url = '';
  imageFeedback.value = '';
};

/**
 * Gestiona esta acción de la vista.
 */
const handleLocalImageUpload = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  isUploadingImage.value = true;
  imageFeedback.value = '';
  try {
    const uploaded = await uploadStoreImage(file);
    form.imagen_url = uploaded.url;
    imageFeedbackTone.value = 'success';
    imageFeedback.value = 'Imagen subida correctamente.';
  } catch (error) {
    imageFeedbackTone.value = 'error';
    imageFeedback.value =
      error instanceof Error ? error.message : 'No se pudo subir la imagen.';
  } finally {
    isUploadingImage.value = false;
    event.target.value = '';
  }
};

/**
 * Gestiona esta acción de la vista.
 */
const handleSubmit = async () => {
  if (isSaving.value || isUploadingImage.value) return;
  isSaving.value = true;
  feedbackMessage.value = '';
  try {
    await gymStore.upsertProductoTienda({
      id_producto: editingId.value || undefined,
      nombre: form.nombre,
      descripcion: form.descripcion,
      categoria: form.categoria,
      id_item: form.id_item || null,
      unidad_venta: form.unidad_venta,
      precio: form.precio,
      cantidad: form.cantidad,
      minimo: form.minimo,
      estado: form.estado,
      imagen_url: form.imagen_url,
    });
    const savedLabel = editingId.value
      ? 'Producto actualizado.'
      : 'Producto registrado.';
    isSaving.value = false;
    closeProductEditor();
    feedbackTone.value = 'success';
    feedbackMessage.value = savedLabel;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value =
      error instanceof Error
        ? error.message
        : 'No se pudo guardar el producto.';
  } finally {
    isSaving.value = false;
  }
};

/**
 * Elimina el registro indicado.
 */
const deleteProducto = async (idProducto) => {
  if (!window.confirm('Eliminar este producto?')) return;
  try {
    await gymStore.deleteProductoTienda(idProducto);
    feedbackTone.value = 'success';
    feedbackMessage.value = 'Producto eliminado.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value =
      error instanceof Error
        ? error.message
        : 'No se pudo eliminar el producto.';
  }
};

/**
 * Gestiona esta acción de la vista.
 */
const agregarAlCarrito = (producto) => {
  const requested = Number(cantidadInput.value[producto.id_producto] || 1);
  const stock = Number(producto.cantidad || 1);
  const cantidad = Math.max(1, Math.min(requested, stock));
  gymStore.addToCart(producto, cantidad);
  cantidadInput.value[producto.id_producto] = 1;
  feedbackTone.value = 'success';
  feedbackMessage.value = `${producto.nombre} añadido al carrito.`;
};

/**
 * Gestiona esta acción de la vista.
 */
const goToCheckout = () => {
  if (!cart.value.length) return;
  router.push('/user/store/payment');
};

onMounted(() => {
  gymStore
    .fetchFromBackend?.()
    .catch((error) => console.warn('No se pudo refrescar tienda:', error));
});
</script>

<style scoped>
.store-admin-table {
  min-width: 980px;
}
.store-product-card {
  display: flex;
  flex-direction: column;
}
.store-product-image {
  background: var(--ws-inset);
  border-color: var(--ws-border);
}
.store-product-card > div:last-child {
  margin-top: auto;
  padding-top: 1rem;
}
@media (max-width: 767px) {
  .store-admin-table {
    min-width: 0;
  }
  .store-admin-table thead {
    display: none;
  }
  .store-admin-table tbody,
  .store-admin-table tr {
    display: block;
  }
  .store-admin-table tr {
    padding: 0.75rem;
    border-bottom: 1px solid var(--ws-border);
  }
  .store-admin-table td {
    display: flex;
    justify-content: space-between;
    align-items: start;
    gap: 1rem;
    border: 0;
    padding: 0.5rem;
    max-width: none;
    overflow-wrap: anywhere;
  }
  .store-admin-table td::before {
    content: attr(data-label);
    color: var(--ws-muted);
    font-size: 0.75rem;
    flex-shrink: 0;
    padding-top: 0.15rem;
  }
}
</style>
