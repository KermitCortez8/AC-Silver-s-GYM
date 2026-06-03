<template>
  <div class="space-y-6">
    <section class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Catálogo</p>
      <h1 class="mt-2 text-3xl font-black text-white">{{ isAdmin ? 'Tienda - Administración' : 'Tienda' }}</h1>
      <p class="mt-2 text-slate-300">{{ isAdmin ? 'Administra el catálogo de productos disponibles.' : 'Explora y compra los productos disponibles.' }}</p>
    </section>

    <!-- Sección Admin: Agregar/Editar Productos -->
    <section v-if="isAdmin" class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur" @submit.prevent="handleSubmit">
        <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Producto</p>
        <h2 class="mt-2 text-2xl font-black text-white">{{ editingId ? 'Editar producto' : 'Nuevo producto' }}</h2>

        <div class="mt-4 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-50">
          <p class="text-xs uppercase tracking-[0.35em] text-cyan-200">Identificador único</p>
          <p class="mt-1 font-semibold text-white">{{ currentProductCode }}</p>
        </div>

        <div class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Nombre del producto</span>
            <input v-model="form.nombre" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Proteína Whey, Bebida Energética, etc." />
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-sm text-slate-300">Descripción</span>
            <textarea
              v-model="form.descripcion"
              rows="2"
              class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none"
              placeholder="Descripción breve del producto..."
            ></textarea>
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Categoría</span>
            <input v-model="form.categoria" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" placeholder="Suplementos, Bebidas..." />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Precio (S/.)</span>
            <input v-model.number="form.precio" type="number" min="0" step="0.01" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Cantidad en stock</span>
            <input v-model.number="form.cantidad" type="number" min="0" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Stock Mínimo</span>
            <input v-model.number="form.minimo" type="number" min="0" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none" />
          </label>
          <label class="space-y-2">
            <span class="text-sm text-slate-300">Estado</span>
            <select v-model="form.estado" class="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-white outline-none">
              <option>Disponible</option>
              <option>Agotado</option>
              <option>Descatalogado</option>
            </select>
          </label>
        </div>

        <button type="submit" class="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
          {{ editingId ? 'Guardar cambios' : 'Agregar producto' }}
        </button>
      </form>

      <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Catálogo</p>
            <h2 class="mt-2 text-2xl font-black text-white">Listado de productos</h2>
          </div>
          <div class="rounded-2xl bg-slate-900/80 px-4 py-3 text-right">
            <p class="text-xs text-slate-400">Total productos</p>
            <p class="text-xl font-black text-white">{{ productos.length }}</p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="producto in productos" :key="producto.id_producto" class="rounded-3xl border border-white/10 bg-slate-900/80 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div class="flex-1">
                <p class="text-xs uppercase tracking-[0.35em] text-cyan-200">{{ productCode(producto.id_producto) }}</p>
                <p class="mt-1 font-semibold text-white">{{ producto.nombre }}</p>
                <p class="text-sm text-slate-400">{{ producto.categoria }}</p>
                <p class="mt-1 text-sm text-slate-300">{{ producto.descripcion }}</p>
                <p class="mt-2 text-sm font-bold text-green-400">S/. {{ producto.precio.toFixed(2) }}</p>
                <p class="text-sm text-slate-300">Stock: {{ producto.cantidad }} · Mínimo: {{ producto.minimo }}</p>
                <p class="mt-1 text-xs" :class="producto.estado === 'Disponible' ? 'text-green-400' : 'text-amber-400'">
                  Estado: {{ producto.estado }}
                </p>
              </div>

              <div class="flex gap-2">
                <button class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium" @click="editProducto(producto)">
                  Editar
                </button>
                <button class="rounded-full bg-rose-500 px-4 py-2 text-sm font-semibold text-white" @click="deleteProducto(producto.id_producto)">
                  Eliminar
                </button>
              </div>
            </div>
          </article>

          <div v-if="!productos.length" class="rounded-2xl border border-slate-700/50 bg-slate-900/30 py-8 text-center">
            <p class="text-slate-400">No hay productos aún. Comienza agregando un nuevo producto.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Sección Cliente: Catálogo de Compra -->
    <section v-else class="space-y-6">
      <div class="grid gap-6 lg:grid-cols-[1fr_350px]">
        <!-- Catálogo -->
        <div>
          <div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
            <div v-for="producto in productos" :key="producto.id_producto" class="rounded-2xl border border-white/10 bg-slate-900/80 p-4">
              <div class="aspect-square rounded-xl bg-gradient-to-br from-cyan-400/10 to-emerald-400/10 mb-3 flex items-center justify-center">
                <span class="text-5xl">📦</span>
              </div>
              <p class="text-sm font-bold text-cyan-200">{{ producto.categoria }}</p>
              <p class="mt-1 font-semibold text-white">{{ producto.nombre }}</p>
              <p class="mt-1 text-sm text-slate-400">{{ producto.descripcion }}</p>
              <p class="mt-3 text-lg font-black text-green-400">S/. {{ producto.precio.toFixed(2) }}</p>
              <p class="text-xs text-slate-400 mt-1">Stock: {{ producto.cantidad }}</p>
              
              <div v-if="producto.estado === 'Disponible' && producto.cantidad > 0" class="mt-4 flex gap-2">
                <input
                  v-model.number="cantidadInput[producto.id_producto]"
                  type="number"
                  min="1"
                  :max="producto.cantidad"
                  class="flex-1 rounded-lg border border-white/10 bg-slate-950/60 px-2 py-1 text-white text-sm outline-none"
                />
                <button
                  class="flex-1 rounded-lg bg-cyan-400 px-3 py-1 text-sm font-bold text-slate-950 transition hover:bg-cyan-300"
                  @click="agregarAlCarrito(producto)"
                >
                  Agregar
                </button>
              </div>
              <div v-else class="mt-4 rounded-lg bg-slate-950/60 px-3 py-2 text-center text-sm text-slate-400">
                {{ producto.estado !== 'Disponible' ? producto.estado : 'Agotado' }}
              </div>
            </div>
          </div>

          <div v-if="!productos.length" class="rounded-2xl border border-slate-700/50 bg-slate-900/30 py-12 text-center">
            <p class="text-slate-400">No hay productos disponibles en la tienda.</p>
          </div>
        </div>

        <!-- Carrito -->
        <div class="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur h-fit sticky top-4">
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Carrito</p>
          <h2 class="mt-2 text-2xl font-black text-white">Mi compra</h2>

          <div class="mt-5 space-y-3 max-h-96 overflow-y-auto">
            <div v-for="item in cart" :key="item.id_producto" class="rounded-2xl border border-white/10 bg-slate-950/80 p-3">
              <div class="flex items-start justify-between gap-2">
                <div class="flex-1 min-w-0">
                  <p class="font-semibold text-white truncate">{{ item.nombre }}</p>
                  <p class="mt-1 text-sm text-green-400">S/. {{ item.precio.toFixed(2) }}</p>
                </div>
                <button
                  class="rounded-full bg-rose-500/20 p-1 text-rose-300 hover:bg-rose-500 hover:text-white transition"
                  @click="() => gymStore.removeFromCart(item.id_producto)"
                >
                  ✕
                </button>
              </div>

              <div class="mt-3 flex items-center gap-2">
                <button
                  class="rounded px-2 py-1 bg-slate-800 text-sm text-white hover:bg-slate-700"
                  @click="() => gymStore.updateCartQuantity(item.id_producto, Math.max(1, item.cantidad - 1))"
                >
                  −
                </button>
                <input
                  :value="item.cantidad"
                  type="number"
                  min="1"
                  class="flex-1 text-center rounded px-2 py-1 bg-slate-800 text-white text-sm outline-none"
                  @change="(e) => gymStore.updateCartQuantity(item.id_producto, Math.max(1, Number(e.target.value)))"
                />
                <button
                  class="rounded px-2 py-1 bg-slate-800 text-sm text-white hover:bg-slate-700"
                  @click="() => gymStore.updateCartQuantity(item.id_producto, item.cantidad + 1)"
                >
                  +
                </button>
              </div>

              <p class="mt-2 text-right text-sm text-slate-300">
                Subtotal: S/. {{ (item.precio * item.cantidad).toFixed(2) }}
              </p>
            </div>

            <div v-if="!cart.length" class="rounded-2xl border border-slate-700/50 bg-slate-900/30 py-6 text-center">
              <p class="text-slate-400 text-sm">Tu carrito está vacío</p>
            </div>
          </div>

          <!-- Total -->
          <div v-if="cart.length" class="mt-6 space-y-3 border-t border-white/10 pt-4">
            <div class="flex justify-between text-sm">
              <p class="text-slate-300">Subtotal:</p>
              <p class="font-semibold text-white">S/. {{ cartTotal.subtotal.toFixed(2) }}</p>
            </div>
            <div class="flex justify-between text-sm">
              <p class="text-slate-300">IGV (18%):</p>
              <p class="font-semibold text-green-400">S/. {{ cartTotal.igv.toFixed(2) }}</p>
            </div>
            <div class="flex justify-between border-t border-white/10 pt-3">
              <p class="font-black text-white">Total:</p>
              <p class="text-xl font-black text-cyan-400">S/. {{ cartTotal.total.toFixed(2) }}</p>
            </div>

            <button class="mt-4 w-full rounded-2xl bg-cyan-400 px-4 py-3 font-bold text-slate-950 transition hover:bg-cyan-300">
              Procesar compra
            </button>
            <button
              class="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 font-bold text-white transition hover:bg-white/10"
              @click="() => gymStore.clearCart()"
            >
              Limpiar carrito
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import { useGymStore } from '../stores/gymStore';

const route = useRoute();
const authStore = useAuthStore();
const gymStore = useGymStore();

const isAdmin = computed(() => route.path.startsWith('/admin/store'));
const productos = computed(() => gymStore.productos_tienda);
const cart = computed(() => gymStore.cart);
const cartTotal = computed(() => gymStore.cartTotal);

const editingId = ref('');
const cantidadInput = ref({});

const currentProductCode = computed(() => {
  if (editingId.value) {
    return productos.value.find((p) => p.id_producto === editingId.value)?.id_producto || 'Se generará automáticamente';
  }
  return 'Se generará automáticamente';
});

const productCode = (id) => `PROD-${String(id).padStart(4, '0')}`;

const form = reactive({
  nombre: '',
  descripcion: '',
  categoria: 'General',
  precio: 0,
  cantidad: 0,
  minimo: 5,
  estado: 'Disponible',
});

const resetForm = () => {
  editingId.value = '';
  form.nombre = '';
  form.descripcion = '';
  form.categoria = 'General';
  form.precio = 0;
  form.cantidad = 0;
  form.minimo = 5;
  form.estado = 'Disponible';
};

const editProducto = (producto) => {
  editingId.value = producto.id_producto;
  form.nombre = producto.nombre;
  form.descripcion = producto.descripcion || '';
  form.categoria = producto.categoria;
  form.precio = producto.precio;
  form.cantidad = producto.cantidad;
  form.minimo = producto.minimo || 5;
  form.estado = producto.estado;
};

const handleSubmit = async () => {
  try {
    await gymStore.upsertProductoTienda({
      id_producto: editingId.value || undefined,
      nombre: form.nombre,
      descripcion: form.descripcion,
      categoria: form.categoria,
      precio: form.precio,
      cantidad: form.cantidad,
      minimo: form.minimo,
      estado: form.estado,
    });
    resetForm();
  } catch (error) {
    console.error('Error al guardar producto:', error);
  }
};

const deleteProducto = (id_producto) => {
  if (confirm('¿Estás seguro que deseas eliminar este producto?')) {
    gymStore.deleteProductoTienda(id_producto);
  }
};

const agregarAlCarrito = (producto) => {
  const cantidad = cantidadInput.value[producto.id_producto] || 1;
  gymStore.addToCart(producto, cantidad);
  cantidadInput.value[producto.id_producto] = 1;
};
</script>

