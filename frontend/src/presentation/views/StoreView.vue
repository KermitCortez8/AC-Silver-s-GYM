<template>
  <div class="workspace-view inv-store-theme space-y-6">

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

    <div v-if="!isAdmin" class="ws-panel store-toolbar">
      <div class="store-toolbar-search">
        <span class="ws-field-label">Buscar</span>
        <TableSearch
          v-model="productSearch"
          label="Buscar productos por nombre o categoria"
          placeholder="Buscar por nombre o categoria"
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
                <SortableTh class="px-5 py-4 font-bold" label="N° producto" column="code" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="px-4 py-4 font-bold" label="Nombre" column="nombre" :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <th class="px-4 py-4 font-bold">Imagen</th>
                <th class="px-4 py-4 font-bold">Categoría</th>
                <SortableTh class="px-4 py-4 font-bold" label="Precio" column="precio" numeric :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
                <SortableTh class="px-4 py-4 font-bold" label="Stock" column="cantidad" numeric :sort-key="sortKey" :sort-dir="sortDir" @sort="toggleSort" />
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

                <!-- Stock con barra -->
                <td data-label="Stock" class="px-4 py-4 align-top">
                  <p class="font-bold" :class="isProductLowStock(producto) ? 'text-rose-300' : 'text-white'">
                    {{ producto.cantidad }} {{ producto.unidad_venta || 'unidad' }}
                  </p>
                  <div class="mt-1.5 h-1.5 w-24 overflow-hidden rounded-full ws-inset">
                    <div class="h-full rounded-full transition-all" :class="isProductLowStock(producto) ? 'bg-rose-500' : 'bg-green-500'" :style="{ width: stockBarWidth(producto) + '%' }"></div>
                  </div>
                  <p class="mt-1 text-xs text-slate-400">Minimo: {{ producto.minimo || 0 }}</p>
                </td>

                <!-- Estado -->
                <td data-label="Estado" class="px-4 py-4 align-top">
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
                      class="inline-flex items-center gap-1.5 rounded-xl border border-sky-400/30 bg-sky-400/10 px-3 py-2 text-sm font-bold text-sky-200 transition hover:bg-sky-400/20"
                      @click="detailProduct = producto"
                    >
                      <Eye :size="15" aria-hidden="true" /> Detalles
                    </button>
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
        <p class="mt-1 text-xs text-slate-500">{{ busqueda || categoriaActiva ? 'Prueba con otro termino o categoria.' : 'Usa "Ingresar Nuevo Articulo" para agregar el primero.' }}</p>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════
         CLIENTE — VISTA DE TIENDA (CARRITO)
    ════════════════════════════════════════════════ -->
    <section v-else class="space-y-6">
      <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div class="space-y-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p class="ws-eyebrow">Para tu entrenamiento</p>
              <h2 class="mt-2 text-2xl font-black ws-text">Encuentra tu complemento ideal</h2>
            </div>
            <div class="flex gap-2">
              <div class="rounded-2xl ws-inset px-4 py-3 text-right">
                <p class="text-xs ws-muted">Productos</p>
                <p class="text-xl font-black ws-text">{{ visibleProducts.length }}</p>
              </div>
              <div class="rounded-2xl ws-inset px-4 py-3 text-right">
                <p class="text-xs ws-muted">Favoritos</p>
                <p class="text-xl font-black ws-text">{{ favoriteIds.length }}</p>
              </div>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <article
              v-for="producto in visibleProducts"
              :key="producto.id_producto"
              class="ws-panel store-product-card store-card"
              :class="{ 'is-unavailable': !canBuy(producto) }"
            >
              <button
                type="button"
                class="store-card-fav"
                :class="{ 'is-active': isFavorite(producto.id_producto) }"
                :aria-pressed="isFavorite(producto.id_producto)"
                :aria-label="isFavorite(producto.id_producto) ? `Quitar ${producto.nombre} de favoritos` : `Agregar ${producto.nombre} a favoritos`"
                @click="toggleFavorite(producto.id_producto)"
              >
                <Heart :size="18" :fill="isFavorite(producto.id_producto) ? 'currentColor' : 'none'" aria-hidden="true" />
              </button>
              <button
                type="button"
                class="store-card-open"
                :aria-label="`Ver detalle de ${producto.nombre}`"
                @click="openClientDetail(producto)"
              >
                <span class="store-product-image store-card-image">
                  <img v-if="producto.imagen_url" :src="producto.imagen_url" :alt="producto.nombre" class="h-full w-full object-contain p-3" />
                  <Package v-else :size="48" class="ws-muted" aria-hidden="true" />
                  <span v-if="!canBuy(producto)" class="store-card-badge">{{ producto.estado !== 'Disponible' ? producto.estado : 'Agotado' }}</span>
                </span>
                <span class="store-card-category">{{ producto.categoria || 'General' }}</span>
                <span class="block font-bold ws-text">{{ producto.nombre }}</span>
                <span class="mt-1 line-clamp-2 block text-sm ws-muted">{{ producto.descripcion || 'Producto disponible en tienda.' }}</span>
              </button>
              <div class="mt-3 flex items-end justify-between gap-2">
                <p class="text-xl font-black ws-success">S/. {{ Number(producto.precio || 0).toFixed(2) }}</p>
                <p class="text-xs ws-muted">Stock: {{ producto.cantidad }}</p>
              </div>

              <div v-if="canBuy(producto)" class="mt-4 flex gap-2">
                <input
                  :value="cantidadInput[producto.id_producto] ?? 1"
                  :aria-label="`Cantidad de ${producto.nombre}`"
                  type="text"
                  inputmode="numeric"
                  class="ws-input w-16 px-3 py-2 text-center text-sm"
                  @beforeinput="blockQuantityChars"
                  @input="setQuantity(producto, $event)"
                />
                <button
                  class="flex-1 rounded-xl ws-primary px-3 py-2 text-sm font-bold ws-onaccent transition ws-primary-hover"
                  @click="agregarAlCarrito(producto)"
                >
                  Agregar
                </button>
              </div>
              <div v-else class="mt-4 rounded-xl ws-inset px-3 py-2 text-center text-sm ws-muted">
                {{ producto.estado !== 'Disponible' ? producto.estado : 'Agotado' }}
              </div>
            </article>
          </div>

          <p
            v-if="!visibleProducts.length"
            class="rounded-2xl border border-dashed ws-border p-10 text-center text-sm ws-muted"
          >
            {{
              onlyFavorites && !favoriteIds.length
                ? 'Aun no tienes favoritos. Toca el corazon de un producto para guardarlo aqui.'
                : hasClientFilters
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
                <button type="button" class="inv-btn-ghost h-11 w-11 text-lg" aria-label="Sumar uno" @click="stepDetailQuantity(1)">+</button>
              </div>
            </div>
            <p v-else class="inv-error">Este producto no esta disponible por ahora.</p>
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
              <p class="text-xs text-slate-400">{{ detailProduct.unidad_venta || 'unidad' }} · minimo {{ detailProduct.minimo || 0 }}</p>
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
import { useProductEditor } from '../composables/store/useProductEditor.js';
import ProductEditorDialog from '../components/store/ProductEditorDialog.vue';
import { computed, onMounted, ref } from 'vue';
import { Eye, Heart, Package, ShoppingBag, TrendingDown, AlertTriangle, BarChart3 } from 'lucide-vue-next';
import { useStoreFavorites } from '../composables/store/useStoreFavorites.js';
import { blockNonInteger } from '../utils/inputGuards.js';
import { useAuthStore } from '../../application/stores/authStore';
import ResourceModal from '../components/ResourceModal.vue';
import SortableTh from '../components/common/SortableTh.vue';
import TablePager from '../components/common/TablePager.vue';
import TableSearch from '../components/common/TableSearch.vue';
import { cleanInteger, DEFAULT_PAGE_SIZE, matchesSearch, sortRows, uniqueOptions } from '../../domain/utils/inputRules.js';
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
// El buscador del cliente mira el nombre y la categoria.
const filteredProducts = computed(() => catalogProducts.value.filter((p) =>
  (!categoryFilter.value || (p.categoria || 'General') === categoryFilter.value)
  && matchesSearch(productSearch.value, [p.nombre, p.categoria || 'General'])
  && (!onlyFavorites.value || isFavorite(p.id_producto))));

// Favoritos por usuario, guardados en este navegador.
const authStore = useAuthStore();
const favoriteOwner = computed(() => authStore.user?.id_usuario || authStore.user?.email || '');
const { favoriteIds, isFavorite, toggleFavorite } = useStoreFavorites(favoriteOwner);
const onlyFavorites = ref(false);
const clientSort = ref('recomendados');
const canBuy = (producto) => producto.estado === 'Disponible' && Number(producto.cantidad || 0) > 0;
const CLIENT_SORTS = {
  nombre: (rows) => sortRows(rows, (p) => p.nombre),
  'precio-asc': (rows) => sortRows(rows, (p) => p.precio, 'asc', 'number'),
  'precio-desc': (rows) => sortRows(rows, (p) => p.precio, 'desc', 'number'),
  // Primero lo que se puede comprar, luego los favoritos.
  recomendados: (rows) => [...rows].sort((a, b) => Number(canBuy(b)) - Number(canBuy(a)) || Number(isFavorite(b.id_producto)) - Number(isFavorite(a.id_producto))),
};
const visibleProducts = computed(() => (CLIENT_SORTS[clientSort.value] || CLIENT_SORTS.recomendados)(filteredProducts.value));
const hasClientFilters = computed(() => Boolean(productSearch.value || categoryFilter.value || onlyFavorites.value || clientSort.value !== 'recomendados'));
const clearClientFilters = () => {
  productSearch.value = '';
  categoryFilter.value = '';
  onlyFavorites.value = false;
  clientSort.value = 'recomendados';
};

// Cantidades: solo enteros entre 1 y el stock disponible.
const blockQuantityChars = blockNonInteger();
const clampQuantity = (value, producto) => Math.max(1, Math.min(Number(value) || 1, Number(producto?.cantidad || 1)));
const setQuantity = (producto, event) => {
  const digits = cleanInteger(event.target.value);
  event.target.value = digits;
  if (digits) cantidadInput.value[producto.id_producto] = clampQuantity(digits, producto);
};

// Detalle del producto para el cliente.
const clientDetail = ref(null);
const detailQuantity = ref(1);
const openClientDetail = (producto) => {
  clientDetail.value = producto;
  detailQuantity.value = 1;
};
const stepDetailQuantity = (delta) => {
  detailQuantity.value = clampQuantity(detailQuantity.value + delta, clientDetail.value);
};
const setDetailQuantity = (event) => {
  const digits = cleanInteger(event.target.value);
  event.target.value = digits;
  if (digits) detailQuantity.value = clampQuantity(digits, clientDetail.value);
};
const addDetailToCart = () => {
  const producto = clientDetail.value;
  if (!producto) return;
  cantidadInput.value[producto.id_producto] = detailQuantity.value;
  agregarAlCarrito(producto);
  clientDetail.value = null;
};
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
// El enlace "Stock bajo" del Home llega con ?stock=bajo y abre la lista ya filtrada.
const soloStockBajo = ref(route.query.stock === 'bajo');

// Orden por columna: clic alterna ascendente y descendente.
const sortKey = ref('');
const sortDir = ref('asc');
const SORT_COLUMNS = {
  code: { accessor: (p) => Number(p.id_producto || 0), type: 'number' },
  nombre: { accessor: (p) => p.nombre, type: 'text' },
  precio: { accessor: (p) => p.precio, type: 'number' },
  cantidad: { accessor: (p) => p.cantidad, type: 'number' },
};
const toggleSort = (column) => {
  sortDir.value = sortKey.value === column && sortDir.value === 'asc' ? 'desc' : 'asc';
  sortKey.value = column;
  paginaActual.value = 1;
};
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
  // El buscador solo mira el N° de producto y el nombre.
  lista = lista.filter((p) => matchesSearch(busqueda.value, [productCode(p.id_producto), p.nombre]));
  const column = SORT_COLUMNS[sortKey.value];
  return column ? sortRows(lista, column.accessor, sortDir.value, column.type) : lista;
});

// Paginación (sobre lista filtrada y ordenada)
const paginaActual = ref(1);
const porPagina = ref(DEFAULT_PAGE_SIZE);
const productosPaginados = computed(() => productosFiltrados.value.slice((paginaActual.value - 1) * porPagina.value, paginaActual.value * porPagina.value));

// Detalles de solo lectura del producto.
const detailProduct = ref(null);
const linkedItemName = (idItem) => {
  const item = findItem(idItem);
  return item ? `${item.inventoryCode} - ${item.name}` : `Item #${idItem}`;
};
// Desplegables extensibles del modal: valores existentes en la base + sugeridos.
const productCategoryOptions = computed(() => uniqueOptions(productos.value.map((p) => p.categoria)));
const productUnitOptions = computed(() => uniqueOptions(['Unidad', 'Paquete', 'Docena', 'Caja', 'Combo'], productos.value.map((p) => p.unidad_venta)));
const editFromDetails = () => {
  const producto = detailProduct.value;
  detailProduct.value = null;
  if (producto) editProducto(producto);
};

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

const { isSaving, editingId, isProductEditorOpen, form, formErrors: productFormErrors, currentProductCode, itemNumber, findItem, availableTiendaItems, editingLinked, linkedItemLabel, stockEditable, stockMostrado, resetForm, openNewProducto, closeProductEditor, editProducto, handleSubmit, imageFeedback, imageFeedbackTone, isUploadingImage, isBucketPickerOpen, isLoadingBucketImages, bucketImages, loadBucketImages, openBucketPicker, closeBucketPicker, selectBucketImage, clearSelectedImage, handleLocalImageUpload } = useProductEditor({ gymStore, productos, inventario, feedbackMessage, feedbackTone, productCode });

onMounted(() => {
  gymStore
    .fetchFromBackend?.({ section: 'store' })
    .catch((error) => console.warn('No se pudo refrescar tienda:', error));
});
</script>

<style scoped src="../styles/store-view.css"></style>