<template>
  <div class="space-y-6">

    <!-- ═══════════════════════════════════════════════
         HEADER
    ════════════════════════════════════════════════ -->
    <section class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p class="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.35em] text-slate-500">
            <span class="text-rose-400">Catalogo</span>
            <span class="text-slate-600">»</span>
            <span>{{ isAdmin ? 'Control de Productos de Tienda' : 'Tienda Online' }}</span>
          </p>
          <h1 class="mt-2 text-4xl font-black text-white">{{ isAdmin ? 'Tienda' : 'Tienda' }}</h1>
          <p class="mt-1.5 text-sm text-slate-400">
            {{ isAdmin ? 'Gestiona el catalogo de productos, precios, stock y estado de venta.' : 'Explora articulos, agrega al carrito y prepara tu compra.' }}
          </p>
        </div>

        <button
          v-if="isAdmin"
          class="group flex items-center gap-2.5 self-start rounded-2xl bg-rose-600 px-5 py-3.5 text-sm font-black text-white shadow-lg shadow-rose-600/30 transition-all hover:bg-rose-500 hover:shadow-rose-500/40 xl:self-auto"
          @click="openNewProducto"
        >
          <svg class="h-4 w-4 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Ingresar Nuevo Articulos
        </button>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         ADMIN — TABLA DE PRODUCTOS
    ════════════════════════════════════════════════ -->
    <section v-if="isAdmin" class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">

      <!-- Título + métricas (estilo Inventario) -->
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-[10px] font-bold uppercase tracking-[0.35em] text-slate-500">Estado</p>
          <h2 class="mt-1.5 flex items-center gap-2.5 text-2xl font-black text-white">
            Listado de productos
            <span class="rounded-lg bg-emerald-400/15 px-2 py-0.5 text-xs font-bold text-emerald-300">{{ productosFiltrados.length }} visibles</span>
          </h2>
        </div>

        <!-- Stats horizontales -->
        <div class="flex flex-wrap gap-4">
          <div class="text-center">
            <p class="text-xs text-slate-500">Total</p>
            <p class="mt-0.5 text-2xl font-black text-white">{{ productos.length }}</p>
            <span class="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-sky-400"></span>
          </div>
          <div class="text-center">
            <p class="text-xs text-slate-500">Stock bajo</p>
            <p class="mt-0.5 text-2xl font-black" :class="lowStockCount > 0 ? 'text-rose-300' : 'text-white'">{{ lowStockCount }}</p>
            <span class="mt-1 inline-block h-1.5 w-1.5 rounded-full" :class="lowStockCount > 0 ? 'bg-rose-400' : 'bg-slate-700'"></span>
          </div>
          <div class="text-center">
            <p class="text-xs text-slate-500">Agotados</p>
            <p class="mt-0.5 text-2xl font-black" :class="agotadosCount > 0 ? 'text-amber-300' : 'text-white'">{{ agotadosCount }}</p>
            <span class="mt-1 inline-block h-1.5 w-1.5 rounded-full" :class="agotadosCount > 0 ? 'bg-amber-400' : 'bg-slate-700'"></span>
          </div>
          <div class="text-center">
            <p class="text-xs text-slate-500">Disponibilidad</p>
            <p class="mt-0.5 text-2xl font-black text-emerald-300">{{ disponibilidadPct }}%</p>
            <span class="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
          </div>
        </div>
      </div>

      <!-- Búsqueda + filtros por categoría -->
      <div class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <!-- Buscador -->
        <div class="relative max-w-xs w-full">
          <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
          <input
            v-model="busqueda"
            type="text"
            placeholder="Buscar producto, codigo..."
            class="w-full rounded-xl border border-white/10 bg-slate-900/80 py-2.5 pl-9 pr-4 text-sm text-white placeholder-slate-500 outline-none transition focus:border-white/20"
          />
        </div>

        <!-- Tabs de categoría -->
        <div class="flex flex-wrap items-center gap-2">
          <button
            class="rounded-xl px-3.5 py-1.5 text-xs font-bold transition"
            :class="categoriaActiva === '' ? 'bg-rose-600 text-white shadow-sm' : 'border border-white/10 text-slate-400 hover:text-white hover:bg-white/5'"
            @click="categoriaActiva = ''; paginaActual = 1"
          >
            Todos ({{ productos.length }})
          </button>
          <button
            v-for="cat in categoriasUnicas"
            :key="cat"
            class="rounded-xl px-3.5 py-1.5 text-xs font-bold transition"
            :class="categoriaActiva === cat ? 'bg-rose-600 text-white shadow-sm' : 'border border-white/10 text-slate-400 hover:text-white hover:bg-white/5'"
            @click="categoriaActiva = cat; paginaActual = 1"
          >
            {{ cat }}
          </button>
        </div>
      </div>

      <!-- Feedback -->
      <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
        {{ feedbackMessage }}
      </p>

      <!-- Tabla -->
      <div v-if="productos.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[1160px] text-left text-sm">
            <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">
              <tr>
                <th class="px-5 py-4 font-bold">Producto</th>
                <th class="px-4 py-4 font-bold">Imagen</th>
                <th class="px-4 py-4 font-bold">Categoria</th>
                <th class="px-4 py-4 font-bold">Precio</th>
                <th class="px-4 py-4 font-bold">Stock</th>
                <th class="px-4 py-4 font-bold">Estado</th>
                <th class="px-4 py-4 font-bold">Almacen</th>
                <th class="px-5 py-4 text-right font-bold">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr v-for="producto in productosPaginados" :key="producto.id_producto" class="transition hover:bg-white/[0.04]">

                <!-- Producto -->
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

                <!-- Imagen -->
                <td class="px-4 py-4 align-top">
                  <img
                    v-if="producto.imagen_url"
                    :src="producto.imagen_url"
                    :alt="producto.nombre"
                    class="h-14 w-14 rounded-xl border border-white/10 bg-white/5 object-contain p-1"
                  />
                  <span v-else class="text-xs text-slate-500">Sin imagen</span>
                </td>

                <!-- Categoría -->
                <td class="px-4 py-4 align-top text-slate-300">{{ producto.categoria || 'General' }}</td>

                <!-- Precio -->
                <td class="whitespace-nowrap px-4 py-4 align-top font-black text-emerald-300">
                  S/. {{ Number(producto.precio || 0).toFixed(2) }}
                </td>

                <!-- Stock con barra -->
                <td class="px-4 py-4 align-top">
                  <p class="font-bold" :class="isProductLowStock(producto) ? 'text-rose-300' : 'text-white'">
                    {{ producto.cantidad }} {{ producto.unidad_venta || 'unidad' }}
                  </p>
                  <p class="mt-0.5 text-xs text-slate-400">Minimo: {{ producto.minimo || 0 }}</p>
                  <!-- Barra de stock -->
                  <div class="mt-2 w-full overflow-hidden rounded-full bg-slate-800/80" style="height: 5px;">
                    <div
                      class="h-full rounded-full transition-all duration-500"
                      :class="stockBarColor(producto)"
                      :style="{ width: stockBarWidth(producto) + '%' }"
                    ></div>
                  </div>
                  <p class="mt-1 text-[10px]" :class="isProductLowStock(producto) ? 'text-rose-400' : 'text-slate-600'">
                    {{ stockBarWidth(producto) }}% de capacidad
                  </p>
                </td>

                <!-- Estado -->
                <td class="px-4 py-4 align-top">
                  <span class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold" :class="productStatusClass(producto.estado)">
                    <span class="h-1.5 w-1.5 rounded-full" :class="productStatusDot(producto.estado)"></span>
                    {{ producto.estado }}
                  </span>
                </td>

                <!-- Almacen -->
                <td class="px-4 py-4 align-top">
                  <span v-if="producto.id_item" class="font-semibold text-amber-200">Item #{{ producto.id_item }}</span>
                  <span v-else class="text-slate-500">Sin vincular</span>
                </td>

                <!-- Acciones -->
                <td class="px-5 py-4 align-top">
                  <div class="flex justify-end gap-2">
                    <button
                      class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:border-white/20 hover:bg-white/5"
                      @click="editProducto(producto)"
                    >
                      Editar
                    </button>
                    <button
                      class="rounded-xl border border-rose-400/30 px-3 py-2 text-sm font-bold text-rose-300 transition hover:bg-rose-400/10"
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

      <!-- Paginación -->
      <div v-if="totalPages > 1" class="mt-4 flex items-center justify-between text-sm text-slate-400">
        <p>Mostrando {{ paginaInicio + 1 }} a {{ paginaFin }} de <span class="font-bold text-white">{{ productosFiltrados.length }}</span> productos</p>
        <div class="flex items-center gap-2">
          <button
            class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
            :disabled="paginaActual === 1"
            @click="paginaActual--"
          >Anterior</button>
          <button
            v-for="p in totalPages"
            :key="p"
            class="h-9 w-9 rounded-xl border text-sm font-bold transition"
            :class="p === paginaActual
              ? 'border-rose-500/40 bg-rose-600/20 text-rose-300'
              : 'border-white/10 text-white hover:bg-white/5'"
            @click="paginaActual = p"
          >{{ p }}</button>
          <button
            class="rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-white transition hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
            :disabled="paginaActual === totalPages"
            @click="paginaActual++"
          >Siguiente</button>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!productosFiltrados.length" class="mt-6 rounded-2xl border border-dashed border-white/10 px-6 py-14 text-center">
        <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-slate-900">
          <svg class="h-6 w-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 3H8l-2 4h12l-2-4z" />
          </svg>
        </div>
        <p class="text-sm font-semibold text-slate-300">{{ busqueda || categoriaActiva ? 'Sin resultados' : 'Sin productos registrados' }}</p>
        <p class="mt-1 text-xs text-slate-500">{{ busqueda || categoriaActiva ? 'Prueba con otro termino o categoria.' : 'Usa "Ingresar Nuevo Articulo" para agregar el primero.' }}</p>
      </div>

    </section>

    <!-- ═══════════════════════════════════════════════
         CLIENTE — VISTA DE TIENDA (CARRITO)
    ════════════════════════════════════════════════ -->
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
              <div class="mb-3 flex aspect-square items-center justify-center overflow-hidden rounded-xl border border-amber-200/20 bg-amber-300/10">
                <img
                  v-if="producto.imagen_url"
                  :src="producto.imagen_url"
                  :alt="producto.nombre"
                  class="h-full w-full object-contain p-2"
                />
                <div v-else class="text-center">
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
                <img
                  v-if="item.imagen_url"
                  :src="item.imagen_url"
                  :alt="item.nombre"
                  class="h-12 w-12 rounded-xl border border-white/10 bg-white/5 object-contain p-1"
                />
                <div class="min-w-0 flex-1">
                  <p class="truncate font-semibold text-white">{{ item.nombre }}</p>
                  <p class="mt-1 text-sm text-emerald-300">S/. {{ Number(item.precio || 0).toFixed(2) }}</p>
                </div>
                <button class="rounded-full bg-rose-500/20 px-2 py-1 text-sm font-bold text-rose-200 hover:bg-rose-500 hover:text-white" @click="() => gymStore.removeFromCart(item.id_producto)">
                  x
                </button>
              </div>

              <div class="mt-3 flex items-center gap-2">
                <button class="rounded bg-slate-800 px-2 py-1 text-sm text-white hover:bg-slate-700" @click="() => gymStore.updateCartQuantity(item.id_producto, Math.max(1, item.cantidad - 1))">-</button>
                <input
                  :value="item.cantidad"
                  type="number"
                  min="1"
                  class="w-full rounded bg-slate-800 px-2 py-1 text-center text-sm text-white outline-none"
                  @change="(event) => gymStore.updateCartQuantity(item.id_producto, Math.max(1, Number(event.target.value)))"
                />
                <button class="rounded bg-slate-800 px-2 py-1 text-sm text-white hover:bg-slate-700" @click="() => gymStore.updateCartQuantity(item.id_producto, item.cantidad + 1)">+</button>
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

    <!-- ═══════════════════════════════════════════════
         MODAL — INGRESAR / EDITAR PRODUCTO
    ════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="isAdmin && isProductEditorOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 p-4 backdrop-blur-sm">
        <form
          class="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-950 shadow-2xl"
          @submit.prevent="handleSubmit"
        >
          <!-- Modal header -->
          <div class="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-white/10 bg-slate-950 px-6 py-4">
            <div>
              <p class="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.35em] text-slate-500">
                <span class="text-amber-400">Producto</span>
                <span>•</span>
                <span>{{ editingId ? 'Edicion de registro' : 'Nuevo registro' }}</span>
              </p>
              <h2 class="mt-1 text-xl font-black text-white">{{ editingId ? 'Editar producto' : 'Nuevo producto' }}</h2>
            </div>
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-slate-400 transition hover:border-white/20 hover:bg-white/5 hover:text-white"
              @click="closeProductEditor"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Cerrar
            </button>
          </div>

          <div class="p-6 space-y-6">

            <!-- Identificador -->
            <div class="flex items-center gap-3 rounded-2xl border border-amber-400/25 bg-amber-400/8 px-4 py-3">
              <div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-amber-400/20">
                <svg class="h-4 w-4 text-amber-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a2 2 0 012-2z" />
                </svg>
              </div>
              <div>
                <p class="text-[10px] font-bold uppercase tracking-[0.3em] text-amber-300">Identificador unico</p>
                <p class="mt-0.5 font-black text-white">{{ currentProductCode }}</p>
              </div>
            </div>

            <!-- Sección: Informacion básica -->
            <div>
              <p class="mb-3 text-[10px] font-bold uppercase tracking-[0.3em] text-slate-500">Informacion del producto</p>
              <div class="grid gap-4 sm:grid-cols-2">
                <label class="space-y-2 sm:col-span-2">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Nombre del producto</span>
                  <input v-model="form.nombre" class="field-input" placeholder="Proteina Whey, Bebida Energetica, etc." />
                </label>
                <label class="space-y-2 sm:col-span-2">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Descripcion</span>
                  <textarea v-model="form.descripcion" rows="2" class="field-input" placeholder="Descripcion breve del producto..."></textarea>
                </label>
                <label class="space-y-2">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Categoria</span>
                  <input v-model="form.categoria" class="field-input" placeholder="Suplementos, Bebidas..." />
                </label>
                <label class="space-y-2">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Item de almacen</span>
                  <select v-model.number="form.id_item" class="field-input">
                    <option :value="null">Sin vincular</option>
                    <option v-for="item in inventario" :key="item.id" :value="Number(String(item.id).replace('item-', ''))">
                      {{ item.inventoryCode }} - {{ item.name }}
                    </option>
                  </select>
                </label>
              </div>
            </div>

            <div class="border-t border-white/10"></div>

            <!-- Sección: Precios y stock -->
            <div>
              <p class="mb-3 text-[10px] font-bold uppercase tracking-[0.3em] text-slate-500">Precios y stock</p>
              <div class="grid gap-4 sm:grid-cols-2">
                <label class="space-y-2">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Unidad de venta</span>
                  <input v-model="form.unidad_venta" class="field-input" placeholder="unidad, botella, paquete..." />
                </label>
                <label class="space-y-2">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Precio (S/.)</span>
                  <input v-model.number="form.precio" type="number" min="0" step="0.01" class="field-input" />
                </label>
                <label class="space-y-2">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Cantidad en stock</span>
                  <input v-model.number="form.cantidad" type="number" min="0" class="field-input" />
                </label>
                <label class="space-y-2">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Stock minimo</span>
                  <input v-model.number="form.minimo" type="number" min="0" class="field-input" />
                </label>
                <label class="space-y-2 sm:col-span-2">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Estado</span>
                  <select v-model="form.estado" class="field-input">
                    <option>Disponible</option>
                    <option>Agotado</option>
                    <option>Descatalogado</option>
                  </select>
                </label>
              </div>
            </div>

            <div class="border-t border-white/10"></div>

            <!-- Sección: Imagen -->
            <div>
              <p class="mb-3 text-[10px] font-bold uppercase tracking-[0.3em] text-slate-500">Imagen del producto</p>
              <div class="grid gap-4 lg:grid-cols-[160px_1fr]">
                <!-- Preview -->
                <div class="flex aspect-square items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-slate-900 p-2">
                  <img v-if="form.imagen_url" :src="form.imagen_url" :alt="form.nombre || 'Producto'" class="h-full w-full object-contain" />
                  <div v-else class="flex flex-col items-center gap-2 px-4 text-center">
                    <svg class="h-8 w-8 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p class="text-[10px] text-slate-600">Sin imagen</p>
                  </div>
                </div>

                <!-- Controles -->
                <div class="space-y-3">
                  <div class="flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-2 text-sm font-bold text-amber-200 transition hover:bg-amber-400/20"
                      :disabled="isLoadingBucketImages"
                      @click="openBucketPicker"
                    >
                      {{ isLoadingBucketImages ? 'Cargando...' : 'Seleccionar del bucket' }}
                    </button>
                    <button
                      v-if="form.imagen_url"
                      type="button"
                      class="rounded-xl border border-white/10 px-4 py-2 text-sm font-bold text-slate-300 transition hover:bg-white/5"
                      @click="clearSelectedImage"
                    >
                      Quitar imagen
                    </button>
                  </div>

                  <label class="block space-y-2">
                    <span class="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-500">Subir desde local</span>
                    <input type="file" accept="image/*" class="field-input" :disabled="isUploadingImage" @change="handleLocalImageUpload" />
                  </label>

                  <p v-if="isUploadingImage" class="flex items-center gap-2 text-xs font-semibold text-amber-300">
                    <svg class="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                    Subiendo imagen a Supabase...
                  </p>

                  <!-- Bucket picker -->
                  <div v-if="isBucketPickerOpen" class="rounded-2xl border border-white/10 bg-slate-900/80 p-4">
                    <div class="mb-3 flex items-center justify-between gap-3">
                      <div>
                        <p class="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-500">Bucket Supabase</p>
                        <p class="mt-0.5 text-sm font-semibold text-white">imagenestienda</p>
                      </div>
                      <button type="button" class="rounded-xl border border-white/10 px-3 py-1.5 text-xs font-bold text-white hover:bg-white/5" @click="closeBucketPicker">
                        Cerrar
                      </button>
                    </div>
                    <div v-if="bucketImages.length" class="grid max-h-56 grid-cols-3 gap-3 overflow-y-auto sm:grid-cols-4">
                      <button
                        v-for="image in bucketImages"
                        :key="image.path || image.name"
                        type="button"
                        class="overflow-hidden rounded-xl border transition hover:border-amber-300"
                        :class="form.imagen_url === image.url ? 'border-amber-300 ring-2 ring-amber-300/40' : 'border-white/10'"
                        @click="selectBucketImage(image)"
                      >
                        <img :src="image.url" :alt="image.name" class="aspect-square h-full w-full bg-slate-950/60 object-contain p-1" />
                        <p class="truncate px-2 py-1 text-[10px] text-slate-400">{{ image.name }}</p>
                      </button>
                    </div>
                    <p v-else class="rounded-xl border border-dashed border-white/10 px-4 py-6 text-center text-xs text-slate-400">
                      No hay imagenes en el bucket todavia.
                    </p>
                  </div>

                  <p v-if="imageFeedback" class="rounded-xl border px-3 py-2 text-xs" :class="imageFeedbackTone === 'error' ? 'border-rose-400/20 bg-rose-400/10 text-rose-200' : 'border-emerald-400/20 bg-emerald-400/10 text-emerald-200'">
                    {{ imageFeedback }}
                  </p>
                </div>
              </div>
            </div>

          </div>

          <!-- Modal footer -->
          <div class="border-t border-white/10 bg-slate-950/80 px-6 py-4">
            <button type="submit" class="w-full rounded-2xl bg-amber-400 px-4 py-3.5 font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300 hover:shadow-amber-400/30">
              {{ editingId ? 'Guardar cambios' : 'Registrar producto' }}
            </button>
          </div>
        </form>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useGymStore } from '../stores/gymStore';
import { uploadStoreImage, listStoreImages } from '../services/storeImageService';

const route = useRoute();
const router = useRouter();
const gymStore = useGymStore();

const isAdmin = computed(() => route.path.startsWith('/admin/store'));
const productos = computed(() => gymStore.productos_tienda);
const visibleProducts = computed(() => productos.value.filter((producto) => producto.estado !== 'Descatalogado'));
const inventario = computed(() => gymStore.inventory);
const cart = computed(() => gymStore.cart);
const cartTotal = computed(() => gymStore.cartTotal);

// Búsqueda y filtro por categoría
const busqueda = ref('');
const categoriaActiva = ref('');

const categoriasUnicas = computed(() => {
  const cats = productos.value.map((p) => p.categoria || 'General').filter(Boolean);
  return [...new Set(cats)].sort();
});

const productosFiltrados = computed(() => {
  let lista = productos.value;
  if (categoriaActiva.value) {
    lista = lista.filter((p) => (p.categoria || 'General') === categoriaActiva.value);
  }
  const q = busqueda.value.trim().toLowerCase();
  if (q) {
    lista = lista.filter(
      (p) =>
        p.nombre?.toLowerCase().includes(q) ||
        productCode(p.id_producto).toLowerCase().includes(q) ||
        (p.descripcion || '').toLowerCase().includes(q)
    );
  }
  return lista;
});

// Paginación (sobre lista filtrada)
const paginaActual = ref(1);
const porPagina = 7;
const totalPages = computed(() => Math.ceil(productosFiltrados.value.length / porPagina));
const paginaInicio = computed(() => (paginaActual.value - 1) * porPagina);
const paginaFin = computed(() => Math.min(paginaInicio.value + porPagina, productosFiltrados.value.length));
const productosPaginados = computed(() => productosFiltrados.value.slice(paginaInicio.value, paginaFin.value));

// Métricas
const lowStockCount = computed(() => productos.value.filter((p) => isProductLowStock(p)).length);
const disponiblesCount = computed(() => productos.value.filter((p) => p.estado === 'Disponible').length);
const agotadosCount = computed(() => productos.value.filter((p) => p.estado === 'Agotado').length);
const disponibilidadPct = computed(() => {
  if (!productos.value.length) return 0;
  return Math.round((disponiblesCount.value / productos.value.length) * 100);
});

// Stock max para la barra
const maxStock = computed(() => Math.max(1, ...productos.value.map((p) => Number(p.cantidad || 0))));

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

/**
 * Gestiona esta acción de la vista.
 */
const productCode = (id) => `PROD-${String(id || 0).padStart(4, '0')}`;

/**
 * Valida los datos recibidos.
 */
const isProductLowStock = (producto) => Number(producto.cantidad || 0) <= Number(producto.minimo || 0);

/**
 * Devuelve la clase de color para el badge de estado.
 */
const productStatusClass = (status) => {
  if (status === 'Disponible') return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300';
  if (status === 'Agotado') return 'border-rose-400/20 bg-rose-400/10 text-rose-300';
  return 'border-amber-400/20 bg-amber-400/10 text-amber-300';
};

/**
 * Devuelve la clase del punto indicador de estado.
 */
const productStatusDot = (status) => {
  if (status === 'Disponible') return 'bg-emerald-400';
  if (status === 'Agotado') return 'bg-rose-400';
  return 'bg-amber-400';
};

/**
 * Devuelve el ancho (%) de la barra de stock.
 */
const stockBarWidth = (producto) => {
  const cantidad = Number(producto.cantidad || 0);
  return Math.round((cantidad / maxStock.value) * 100);
};

/**
 * Devuelve el color de la barra de stock según nivel crítico.
 */
const stockBarColor = (producto) => {
  const cantidad = Number(producto.cantidad || 0);
  const minimo = Number(producto.minimo || 1);
  if (cantidad <= minimo) return 'bg-rose-400';
  if (cantidad <= minimo * 2) return 'bg-amber-400';
  return 'bg-emerald-400';
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
    imageFeedback.value = error instanceof Error ? error.message : 'No se pudieron cargar las imagenes del bucket.';
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
    imageFeedback.value = 'Imagen subida a Supabase desde tu ordenador.';
  } catch (error) {
    imageFeedbackTone.value = 'error';
    imageFeedback.value = error instanceof Error ? error.message : 'No se pudo subir la imagen.';
  } finally {
    isUploadingImage.value = false;
    event.target.value = '';
  }
};

/**
 * Gestiona esta acción de la vista.
 */
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
      imagen_url: form.imagen_url,
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
    feedbackMessage.value = error instanceof Error ? error.message : 'No se pudo eliminar el producto.';
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
};

/**
 * Gestiona esta acción de la vista.
 */
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
  transition: border-color 0.2s;
}

.field-input:focus {
  border-color: rgba(251, 191, 36, 0.4);
}

.field-input::placeholder {
  color: #64748b;
}

.bg-amber-400\/8 {
  background-color: rgba(251, 191, 36, 0.08);
}
</style>
