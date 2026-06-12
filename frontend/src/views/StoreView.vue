<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Catalogo</p>
          <h1 class="mt-2 text-3xl font-black text-white">{{ isAdmin ? 'Tienda - Administracion' : 'Tienda' }}</h1>
          <p class="mt-2 text-slate-300">
            {{ isAdmin ? 'Administra el catalogo de productos disponibles.' : 'Explora articulos, agrega al carrito y prepara tu compra.' }}
          </p>
        </div>

        <button
          v-if="isAdmin"
          class="rounded-2xl bg-amber-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300"
          @click="openNewProducto"
        >
          Ingresar Nuevo Articulo
        </button>
      </div>
    </section>

    <section v-if="isAdmin" class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Catalogo</p>
          <h2 class="mt-2 text-2xl font-black text-white">Listado de productos</h2>
        </div>
        <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-right">
          <p class="text-xs text-slate-400">Total productos</p>
          <p class="text-xl font-black text-white">{{ productos.length }}</p>
        </div>
      </div>

      <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
        {{ feedbackMessage }}
      </p>

      <div v-if="productos.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[1080px] text-left text-sm">
            <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
              <tr>
                <th class="px-5 py-4 font-bold">Producto</th>
                <th class="px-4 py-4 font-bold">Categoria</th>
                <th class="px-4 py-4 font-bold">Precio</th>
                <th class="px-4 py-4 font-bold">Stock</th>
                <th class="px-4 py-4 font-bold">Estado</th>
                <th class="px-4 py-4 font-bold">Almacen</th>
                <th class="px-5 py-4 text-right font-bold">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr v-for="producto in productos" :key="producto.id_producto" class="transition hover:bg-white/[0.04]">
                <td class="max-w-sm px-5 py-4 align-top">
                  <div class="flex items-start gap-3">
                    <span class="mt-0.5 rounded-lg bg-amber-400/10 px-2.5 py-1 text-xs font-black text-amber-200">
                      {{ productCode(producto.id_producto) }}
                    </span>
                    <div class="min-w-0">
                      <p class="font-bold text-white">{{ producto.nombre }}</p>
                      <p class="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">{{ producto.descripcion || 'Sin descripcion' }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-4 align-top text-slate-300">{{ producto.categoria || 'General' }}</td>
                <td class="whitespace-nowrap px-4 py-4 align-top font-black text-emerald-300">
                  S/. {{ Number(producto.precio || 0).toFixed(2) }}
                </td>
                <td class="px-4 py-4 align-top">
                  <p class="font-bold" :class="isProductLowStock(producto) ? 'text-rose-300' : 'text-white'">
                    {{ producto.cantidad }} {{ producto.unidad_venta || 'unidad' }}
                  </p>
                  <p class="mt-1 text-xs text-slate-400">Minimo: {{ producto.minimo || 0 }}</p>
                </td>
                <td class="px-4 py-4 align-top">
                  <span class="inline-flex rounded-full border px-2.5 py-1 text-xs font-bold" :class="productStatusClass(producto.estado)">
                    {{ producto.estado }}
                  </span>
                </td>
                <td class="px-4 py-4 align-top">
                  <span v-if="producto.id_item" class="font-semibold text-amber-200">Item #{{ producto.id_item }}</span>
                  <span v-else class="text-slate-500">Sin vincular</span>
                </td>
                <td class="px-5 py-4 align-top">
                  <div class="flex justify-end gap-2">
                    <button class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/5" @click="editProducto(producto)">
                      Editar
                    </button>
                    <button class="rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-100 transition hover:bg-rose-400/10" @click="deleteProducto(producto.id_producto)">
                      Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <p v-if="!productos.length" class="mt-6 rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-400">
        No hay productos aun. Usa "Ingresar Nuevo Articulo" para crear el primero.
      </p>
    </section>

    <section v-else class="space-y-6">
      <div class="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div class="space-y-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Ecommerce</p>
              <h2 class="mt-2 text-2xl font-black text-white">Articulos disponibles</h2>
            </div>
            <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-right">
              <p class="text-xs text-slate-400">Productos</p>
              <p class="text-xl font-black text-white">{{ visibleProducts.length }}</p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <article v-for="producto in visibleProducts" :key="producto.id_producto" class="rounded-2xl border border-white/10 bg-slate-900/80 p-4">
              <div class="mb-3 flex aspect-square items-center justify-center rounded-xl border border-amber-200/20 bg-amber-300/10">
                <div class="text-center">
                  <p class="text-xs uppercase tracking-[0.25em] text-amber-200">{{ producto.categoria }}</p>
                  <p class="mt-2 text-3xl font-black text-white">{{ productCode(producto.id_producto).slice(-4) }}</p>
                </div>
              </div>
              <p class="font-semibold text-white">{{ producto.nombre }}</p>
              <p class="mt-1 line-clamp-2 text-sm text-slate-400">{{ producto.descripcion || 'Producto disponible en tienda.' }}</p>
              <p class="mt-3 text-lg font-black text-emerald-300">S/. {{ Number(producto.precio || 0).toFixed(2) }}</p>
              <p class="mt-1 text-xs text-slate-400">Stock: {{ producto.cantidad }}</p>

              <div v-if="producto.estado === 'Disponible' && Number(producto.cantidad || 0) > 0" class="mt-4 flex gap-2">
                <input
                  v-model.number="cantidadInput[producto.id_producto]"
                  type="number"
                  min="1"
                  :max="producto.cantidad"
                  class="field-input flex-1 px-3 py-2 text-sm"
                />
                <button class="flex-1 rounded-xl bg-amber-400 px-3 py-2 text-sm font-bold text-slate-950 transition hover:bg-amber-300" @click="agregarAlCarrito(producto)">
                  Agregar
                </button>
              </div>
              <div v-else class="mt-4 rounded-xl bg-slate-950/60 px-3 py-2 text-center text-sm text-slate-400">
                {{ producto.estado !== 'Disponible' ? producto.estado : 'Agotado' }}
              </div>
            </article>
          </div>

          <p v-if="!visibleProducts.length" class="rounded-2xl border border-dashed border-white/10 p-10 text-center text-sm text-slate-400">
            No hay productos disponibles en la tienda.
          </p>
        </div>

        <aside class="h-fit rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur lg:sticky lg:top-4">
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Carrito</p>
          <h2 class="mt-2 text-2xl font-black text-white">Mi compra</h2>

          <div class="mt-5 max-h-96 space-y-3 overflow-y-auto">
            <article v-for="item in cart" :key="item.id_producto" class="rounded-2xl border border-white/10 bg-slate-950/80 p-3">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0 flex-1">
                  <p class="truncate font-semibold text-white">{{ item.nombre }}</p>
                  <p class="mt-1 text-sm text-emerald-300">S/. {{ Number(item.precio || 0).toFixed(2) }}</p>
                </div>
                <button class="rounded-full bg-rose-500/20 px-2 py-1 text-sm font-bold text-rose-200 hover:bg-rose-500 hover:text-white" @click="() => gymStore.removeFromCart(item.id_producto)">
                  x
                </button>
              </div>

              <div class="mt-3 flex items-center gap-2">
                <button class="rounded bg-slate-800 px-2 py-1 text-sm text-white hover:bg-slate-700" @click="() => gymStore.updateCartQuantity(item.id_producto, Math.max(1, item.cantidad - 1))">
                  -
                </button>
                <input
                  :value="item.cantidad"
                  type="number"
                  min="1"
                  class="w-full rounded bg-slate-800 px-2 py-1 text-center text-sm text-white outline-none"
                  @change="(event) => gymStore.updateCartQuantity(item.id_producto, Math.max(1, Number(event.target.value)))"
                />
                <button class="rounded bg-slate-800 px-2 py-1 text-sm text-white hover:bg-slate-700" @click="() => gymStore.updateCartQuantity(item.id_producto, item.cantidad + 1)">
                  +
                </button>
              </div>

              <p class="mt-2 text-right text-sm text-slate-300">
                Subtotal: S/. {{ (Number(item.precio || 0) * Number(item.cantidad || 0)).toFixed(2) }}
              </p>
            </article>

            <p v-if="!cart.length" class="rounded-2xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-400">
              Tu carrito esta vacio.
            </p>
          </div>

          <div v-if="cart.length" class="mt-6 space-y-3 border-t border-white/10 pt-4">
            <div class="flex justify-between text-sm">
              <p class="text-slate-300">Subtotal:</p>
              <p class="font-semibold text-white">S/. {{ cartTotal.subtotal.toFixed(2) }}</p>
            </div>
            <div class="flex justify-between text-sm">
              <p class="text-slate-300">IGV (18%):</p>
              <p class="font-semibold text-emerald-300">S/. {{ cartTotal.igv.toFixed(2) }}</p>
            </div>
            <div class="flex justify-between border-t border-white/10 pt-3">
              <p class="font-black text-white">Total:</p>
              <p class="text-xl font-black text-amber-300">S/. {{ cartTotal.total.toFixed(2) }}</p>
            </div>

            <button class="mt-4 w-full rounded-2xl bg-amber-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-amber-300" @click="goToCheckout">
              Procesar compra
            </button>
            <button class="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 font-bold text-white transition hover:bg-white/10" @click="() => gymStore.clearCart()">
              Limpiar carrito
            </button>
          </div>
        </aside>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="isAdmin && isProductEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
        <form class="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-2xl" @submit.prevent="handleSubmit">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Producto</p>
              <h2 class="mt-2 text-2xl font-black text-white">{{ editingId ? 'Editar producto' : 'Nuevo producto' }}</h2>
            </div>
            <button type="button" class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white hover:bg-white/5" @click="closeProductEditor">
              Cerrar
            </button>
          </div>

          <div class="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-50">
            <p class="text-xs uppercase tracking-[0.35em] text-amber-200">Identificador unico</p>
            <p class="mt-1 font-semibold text-white">{{ currentProductCode }}</p>
          </div>

          <div class="mt-5 grid gap-4 sm:grid-cols-2">
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Nombre del producto</span>
              <input v-model="form.nombre" class="field-input" placeholder="Proteina Whey, Bebida Energetica, etc." />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Descripcion</span>
              <textarea v-model="form.descripcion" rows="2" class="field-input" placeholder="Descripcion breve del producto..."></textarea>
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Categoria</span>
              <input v-model="form.categoria" class="field-input" placeholder="Suplementos, Bebidas..." />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Item de almacen</span>
              <select v-model.number="form.id_item" class="field-input">
                <option :value="null">Sin vincular</option>
                <option v-for="item in inventario" :key="item.id" :value="Number(String(item.id).replace('item-', ''))">
                  {{ item.inventoryCode }} - {{ item.name }}
                </option>
              </select>
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Unidad de venta</span>
              <input v-model="form.unidad_venta" class="field-input" placeholder="unidad, botella, paquete..." />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Precio (S/.)</span>
              <input v-model.number="form.precio" type="number" min="0" step="0.01" class="field-input" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Cantidad en stock</span>
              <input v-model.number="form.cantidad" type="number" min="0" class="field-input" />
            </label>
            <label class="space-y-2">
              <span class="text-sm text-slate-300">Stock minimo</span>
              <input v-model.number="form.minimo" type="number" min="0" class="field-input" />
            </label>
            <label class="space-y-2 sm:col-span-2">
              <span class="text-sm text-slate-300">Estado</span>
              <select v-model="form.estado" class="field-input">
                <option>Disponible</option>
                <option>Agotado</option>
                <option>Descatalogado</option>
              </select>
            </label>
          </div>

          <button type="submit" class="mt-6 w-full rounded-2xl bg-amber-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-amber-300">
            {{ editingId ? 'Guardar cambios' : 'Agregar producto' }}
          </button>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useGymStore } from '../stores/gymStore';

const route = useRoute();
const router = useRouter();
const gymStore = useGymStore();

const isAdmin = computed(() => route.path.startsWith('/admin/store'));
const productos = computed(() => gymStore.productos_tienda);
const visibleProducts = computed(() => productos.value.filter((producto) => producto.estado !== 'Descatalogado'));
const inventario = computed(() => gymStore.inventory);
const cart = computed(() => gymStore.cart);
const cartTotal = computed(() => gymStore.cartTotal);

const editingId = ref('');
const isProductEditorOpen = ref(false);
const cantidadInput = ref({});
const feedbackMessage = ref('');
const feedbackTone = ref('info');

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
});

const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success') return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-50';
  if (feedbackTone.value === 'error') return 'border-rose-400/20 bg-rose-400/10 text-rose-50';
  return 'border-sky-400/20 bg-sky-400/10 text-sky-50';
});

const currentProductCode = computed(() => {
  if (editingId.value) {
    return productCode(editingId.value);
  }
  return 'Se generara automaticamente';
});

const productCode = (id) => `PROD-${String(id || 0).padStart(4, '0')}`;

const isProductLowStock = (producto) => Number(producto.cantidad || 0) <= Number(producto.minimo || 0);

const productStatusClass = (status) => {
  if (status === 'Disponible') return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300';
  if (status === 'Agotado') return 'border-rose-400/20 bg-rose-400/10 text-rose-300';
  return 'border-amber-400/20 bg-amber-400/10 text-amber-300';
};

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
};

const openNewProducto = () => {
  resetForm();
  feedbackMessage.value = '';
  isProductEditorOpen.value = true;
};

const closeProductEditor = () => {
  isProductEditorOpen.value = false;
  resetForm();
};

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
  feedbackMessage.value = '';
  isProductEditorOpen.value = true;
};

const handleSubmit = async () => {
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
    });
    const savedLabel = editingId.value ? 'Producto actualizado.' : 'Producto registrado.';
    closeProductEditor();
    feedbackTone.value = 'success';
    feedbackMessage.value = savedLabel;
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo guardar el producto.';
  }
};

const deleteProducto = async (idProducto) => {
  if (!window.confirm('Eliminar este producto?')) return;
  try {
    await gymStore.deleteProductoTienda(idProducto);
    feedbackTone.value = 'success';
    feedbackMessage.value = 'Producto eliminado.';
  } catch (error) {
    feedbackTone.value = 'error';
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo eliminar el producto.';
  }
};

const agregarAlCarrito = (producto) => {
  const requested = Number(cantidadInput.value[producto.id_producto] || 1);
  const stock = Number(producto.cantidad || 1);
  const cantidad = Math.max(1, Math.min(requested, stock));
  gymStore.addToCart(producto, cantidad);
  cantidadInput.value[producto.id_producto] = 1;
};

const goToCheckout = () => {
  if (!cart.value.length) return;
  router.push('/user/store/payment');
};

onMounted(() => {
  gymStore.fetchFromBackend?.().catch((error) => console.warn('No se pudo refrescar tienda:', error));
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
