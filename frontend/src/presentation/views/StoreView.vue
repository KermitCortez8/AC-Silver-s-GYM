<template>
  <div class="workspace-view space-y-6">

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
          v-if="isAdmin && activeTab === 'productos'"
          class="group flex items-center gap-2.5 self-start rounded-2xl bg-rose-600 px-5 py-3.5 text-sm font-black text-white shadow-lg shadow-rose-600/30 transition-all hover:bg-rose-500 hover:shadow-rose-500/40 xl:self-auto"
          @click="openNewProducto"
        >
          <svg class="h-4 w-4 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Ingresar Nuevo Articulo
        </button>
      </div>

      <nav v-if="isAdmin" class="mt-5 flex border-b border-white/10" aria-label="Secciones de tienda">
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

    <div v-if="!isAdmin" class="ws-panel flex flex-col gap-4 sm:flex-row sm:items-end">
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
      v-if="!isAdmin && feedbackMessage && !isProductEditorOpen"
      role="status"
      class="ws-notice"
      :class="feedbackToneClass"
    >
      {{ feedbackMessage }}
    </p>
    <StoreMovementsPanel v-if="isAdmin && activeTab === 'movimientos'" />

    <section v-else-if="isAdmin" class="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Estado</p>
          <h2 class="mt-2 text-2xl font-black text-white">Listado de productos</h2>
        </div>
      </div>

      <!-- Stats cards con iconos (estilo Inventario) -->
      <div class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-blue-400 bg-slate-900/80 px-4 py-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
            <ShoppingBag :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Total productos</p>
            <p class="text-2xl font-black text-white">{{ productos.length }}</p>
          </div>

        </div>
        <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-green-400 bg-slate-900/80 px-4 py-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-green-100 text-green-600">
            <BarChart3 :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Disponibilidad</p>
            <p class="text-2xl font-black text-white">{{ disponibilidadPct }}%</p>
          </div>
         </div>
        <button
          type="button"
          class="flex items-center gap-3 rounded-2xl border-l-4 border-l-yellow-400 bg-slate-900/80 px-4 py-3 text-left transition hover:bg-slate-800/80"
          :class="soloStockBajo ? 'ring-2 ring-yellow-400/70' : ''"
          :aria-pressed="soloStockBajo"
          :title="soloStockBajo ? 'Quitar filtro de stock bajo' : 'Ver solo productos por reponer desde Inventario'"
          @click="toggleStockBajo"
        >
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-yellow-100 text-yellow-700">
            <TrendingDown :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Stock bajo</p>
            <p class="text-2xl font-black" :class="lowStockCount > 0 ? 'text-rose-300' : 'text-white'">{{ lowStockCount }}</p>
          </div>
        </button>

        <div class="flex items-center gap-3 rounded-2xl border-l-4 border-l-rose-400 bg-slate-900/80 px-4 py-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-600">
            <AlertTriangle :size="20" stroke-width="2.5" />
          </span>
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Agotados</p>
            <p class="text-2xl font-black" :class="agotadosCount > 0 ? 'text-rose-300' : 'text-white'">{{ agotadosCount }}</p>
          </div>
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
          Todas las categorias <span :class="categoriaActiva === '' ? 'text-white/70' : 'text-slate-500'">{{ productos.length }}</span>
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

      <p class="mt-3 text-xs text-slate-500">Mostrando {{ productosFiltrados.length }} de {{ productos.length }} productos</p>

      <!-- Buscador + select de estado en fila (estilo Inventario) -->
      <div class="mt-3 grid gap-3 sm:grid-cols-[1.5fr_1fr]">
        <div class="flex items-center gap-2 rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3">
          <Search :size="16" class="shrink-0 text-slate-500" />
          <input v-model="busqueda" class="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500" placeholder="Buscar producto, codigo..." />
        </div>
        <select v-model="filtroEstado" class="field-input">
          <option value="">Todos los estados</option>
          <option>Disponible</option>
          <option>Agotado</option>
          <option>Descatalogado</option>
        </select>
      </div>

      <!-- Feedback -->
      <p v-if="feedbackMessage" class="mt-4 rounded-2xl border px-4 py-3 text-sm" :class="feedbackToneClass">
        {{ feedbackMessage }}
      </p>

      <!-- Tabla con min-w fijo para no romperse en zoom -->
      <div v-if="productos.length" class="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70">
        <div class="overflow-x-auto">

         <table class="w-full text-left text-sm store-admin-table">
            <thead class="border-b border-white/10 bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-400">

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
            <tbody class="divide-y divide-white/10">
              <tr v-for="producto in productosPaginados" :key="producto.id_producto" class="transition hover:bg-white/[0.04]">

                <!-- Producto -->
                <td class="max-w-sm px-5 py-4 align-top">
                  <div class="flex items-start gap-3">
                    <span class="mt-0.5 rounded-lg bg-amber-400/10 px-2.5 py-1 text-xs font-bold text-amber-200">
                      {{ productCode(producto.id_producto) }}
                    </span>
                    <div class="min-w-0">
                      <p class="font-bold text-white">{{ producto.nombre }}</p>
                      <p class="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">
                        {{ producto.descripcion || 'Sin descripción' }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-4 align-top">
                  <img
                    v-if="producto.imagen_url"
                    :src="producto.imagen_url"
                    :alt="producto.nombre"
                    class="h-14 w-14 rounded-xl border border-white/10 bg-slate-950/60 object-contain p-1"
                  />
                  <span v-else class="text-xs text-slate-500">Sin imagen</span>
                </td>
                <td class="px-4 py-4 align-top">
                  <span class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-slate-200">
                    <span class="h-1.5 w-1.5 shrink-0 rounded-full" :style="{ background: categoriaDotColor(producto.categoria || 'General') }"></span>
                    {{ producto.categoria || 'General' }}
                  </span>
                </td>

                <!-- Precio -->
                <td data-label="Precio" class="whitespace-nowrap px-4 py-4 align-top font-black text-emerald-300">
                  S/. {{ Number(producto.precio || 0).toFixed(2) }}
                </td>

                <!-- Stock con barra -->
                <td class="px-4 py-4 align-top">
                  <p class="font-bold" :class="isProductLowStock(producto) ? 'text-rose-300' : 'text-white'">
                    {{ producto.cantidad }} {{ producto.unidad_venta || 'unidad' }}
                  </p>
                  <div class="mt-1.5 h-1.5 w-24 overflow-hidden rounded-full ws-inset">
                    <div class="h-full rounded-full transition-all" :class="isProductLowStock(producto) ? 'bg-rose-500' : 'bg-green-500'" :style="{ width: stockBarWidth(producto) + '%' }"></div>
                  </div>
                  <p class="mt-1 text-xs text-slate-400">Minimo: {{ producto.minimo || 0 }}</p>
                </td>

                <!-- Estado -->
                <td class="px-4 py-4 align-top">
                  <span class="inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold" :class="productStatusClass(producto.estado)">
                    {{ producto.estado }}
                  </span>
                </td>

                <!-- Almacen -->
                <td data-label="Almacén" class="px-4 py-4 align-top">
                  <span v-if="producto.id_item" class="font-semibold text-amber-200">Item #{{ producto.id_item }}</span>
                  <span v-else class="text-slate-500">Sin vincular</span>
                </td>

                <!-- Acciones -->
                <td data-label="Acciones" class="px-5 py-4 align-top">
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

    <!-- ═══════════════════════════════════════════════
         MODAL — INGRESAR / EDITAR PRODUCTO
    ════════════════════════════════════════════════ -->
    <ProductEditorDialog
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
import { useProductEditor } from '../composables/store/useProductEditor.js';
import ProductEditorDialog from '../components/store/ProductEditorDialog.vue';
import { computed, onMounted, ref } from 'vue';
import { Package, Search, ShoppingBag, TrendingDown, AlertTriangle, BarChart3 } from 'lucide-vue-next';
import { useRoute, useRouter } from 'vue-router';
import StoreMovementsPanel from '../components/store/StoreMovementsPanel.vue';
import { useGymStore } from '../../application/stores/gymStore';

const route = useRoute();
const router = useRouter();
const gymStore = useGymStore();

const isAdmin = computed(() => route.path.startsWith('/admin/store'));
const tabs = [
  { value: 'productos', label: 'Productos' },
  { value: 'movimientos', label: 'Movimientos' },
];
const activeTab = computed({
  get: () => (route.query.tab === 'movimientos' ? 'movimientos' : 'productos'),
  set: (tab) => router.replace({ query: { ...route.query, tab } }),
});
const productos = computed(() => gymStore.productos_tienda);
const productSearch = ref('');
const categoryFilter = ref('');

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

// Búsqueda y filtro por categoría
const busqueda = ref('');
const categoriaActiva = ref('');
const filtroEstado = ref('');

const categoriasUnicas = computed(() => {
  const cats = productos.value.map((p) => p.categoria || 'General').filter(Boolean);
  return [...new Set(cats)].sort();
});

// Paleta de colores para puntos de categorías
const CATEGORY_COLORS = [
  '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
  '#ec4899', '#06b6d4', '#f97316', '#84cc16',
];
function categoriaDotColor(cat) {
  const idx = categoriasUnicas.value.indexOf(cat);
  return CATEGORY_COLORS[idx % CATEGORY_COLORS.length] ?? '#94a3b8';
}
// Filtro de la tarjeta "Stock bajo": productos que hay que reponer desde Inventario.
const soloStockBajo = ref(false);
const toggleStockBajo = () => {
  soloStockBajo.value = !soloStockBajo.value;
  paginaActual.value = 1;
};

const productosFiltrados = computed(() => {
  let lista = productos.value;
  if (soloStockBajo.value) {
    lista = lista.filter((p) => isProductLowStock(p));
  }
  if (categoriaActiva.value) {
    lista = lista.filter((p) => (p.categoria || 'General') === categoriaActiva.value);
  }
  if (filtroEstado.value) {
    lista = lista.filter((p) => p.estado === filtroEstado.value);
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
const porPagina = 10;
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

const cantidadInput = ref({});
const feedbackMessage = ref('');
const feedbackTone = ref('info');

const feedbackToneClass = computed(() => {
  if (feedbackTone.value === 'success')
    return 'ws-border-success ws-tint-success ws-success';
  if (feedbackTone.value === 'error')
    return 'ws-border-danger ws-tint-danger ws-danger';
  return 'ws-border-info ws-tint-info ws-info';
});

const productCode = (id) => `PROD-${String(id || 0).padStart(4, '0')}`;

// Items Tipo Tienda que todavia no tienen producto (el vinculo es 1:1).

// Solo un producto nuevo acepta stock inicial; despues cambia con ventas y reposiciones.

const isProductLowStock = (producto) => Number(producto.cantidad || 0) <= Number(producto.minimo || 0);

const productStatusClass = (status) => {
  if (status === 'Disponible')
    return 'ws-border-success ws-tint-success ws-success';
  if (status === 'Agotado') return 'ws-border-danger ws-tint-danger ws-danger';
  return 'ws-border-warning ws-tint-warning ws-warning';
};

const productStatusDot = (status) => {
  if (status === 'Disponible') return 'bg-emerald-400';
  if (status === 'Agotado') return 'bg-rose-400';
  return 'bg-amber-400';
};

const stockBarWidth = (producto) => {
  const cantidad = Number(producto.cantidad || 0);
  return Math.round((cantidad / maxStock.value) * 100);
};

const stockBarColor = (producto) => {
  const cantidad = Number(producto.cantidad || 0);
  const minimo = Number(producto.minimo ?? 1);
  if (cantidad <= minimo) return 'bg-rose-400';
  if (cantidad <= minimo * 2) return 'bg-amber-400';
  return 'bg-emerald-400';
};

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

const agregarAlCarrito = (producto) => {
  const requested = Number(cantidadInput.value[producto.id_producto] || 1);
  const stock = Number(producto.cantidad || 1);
  const cantidad = Math.max(1, Math.min(requested, stock));
  gymStore.addToCart(producto, cantidad);
  cantidadInput.value[producto.id_producto] = 1;
  feedbackTone.value = 'success';
  feedbackMessage.value = `${producto.nombre} añadido al carrito.`;
};

const goToCheckout = () => {
  if (!cart.value.length) return;
  router.push('/user/store/payment');
};

const { isSaving, editingId, isProductEditorOpen, form, currentProductCode, itemNumber, findItem, availableTiendaItems, editingLinked, linkedItemLabel, stockEditable, stockMostrado, resetForm, openNewProducto, closeProductEditor, editProducto, handleSubmit, imageFeedback, imageFeedbackTone, isUploadingImage, isBucketPickerOpen, isLoadingBucketImages, bucketImages, loadBucketImages, openBucketPicker, closeBucketPicker, selectBucketImage, clearSelectedImage, handleLocalImageUpload } = useProductEditor({ gymStore, productos, inventario, feedbackMessage, feedbackTone, productCode });

onMounted(() => {
  gymStore
    .fetchFromBackend?.({ section: 'store' })
    .catch((error) => console.warn('No se pudo refrescar tienda:', error));
});
</script>

<style scoped src="../styles/store-view.css"></style>