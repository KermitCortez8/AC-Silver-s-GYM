<template>
  <section class="space-y-6">
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
              @click="$emit('favorite', producto.id_producto)"
            >
              <Heart :size="18" :fill="isFavorite(producto.id_producto) ? 'currentColor' : 'none'" aria-hidden="true" />
            </button>
            <button
              type="button"
              class="store-card-open"
              :aria-label="`Ver detalle de ${producto.nombre}`"
              @click="$emit('detail', producto)"
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

            <div
              v-if="
                producto.estado === 'Disponible' &&
                Number(producto.cantidad || 0) > 0
              "
              class="mt-4 flex gap-2"
            >
              <input
                :value="cantidadInput[producto.id_producto] ?? 1"
                :aria-label="`Cantidad de ${producto.nombre}, máximo ${availableFor(producto)}`"
                type="text"
                inputmode="numeric"
                maxlength="10"
                class="ws-input flex-1 px-3 py-2 text-sm"
                :disabled="!availableFor(producto)"
                @beforeinput="$emit('quantity-guard', $event)"
                @input="$emit('quantity-change', producto, $event)"
              />
              <button
                class="flex-1 rounded-xl ws-primary px-3 py-2 text-sm font-bold ws-onaccent transition ws-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="!availableFor(producto)"
                @click="$emit('add', producto)"
              >
                {{ availableFor(producto) ? 'Agregar' : 'Todo en tu carrito' }}
              </button>
            </div>
            <div v-else class="mt-4 rounded-xl ws-inset px-3 py-2 text-center text-sm ws-muted">
              {{ producto.estado !== 'Disponible' ? producto.estado : 'Agotado' }}
            </div>
            <p v-if="stockWarning[producto.id_producto]" class="mt-2 text-xs ws-warning">{{ stockWarning[producto.id_producto] }}</p>
          </article>
        </div>

        <p
          v-if="!visibleProducts.length"
          class="rounded-2xl border border-dashed ws-border p-10 text-center text-sm ws-muted"
        >
          {{
            onlyFavorites && !favoriteIds.length
              ? 'Aún no tienes favoritos. Toca el corazón de un producto para guardarlo aquí.'
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
                @click="$emit('remove', item.id_producto)"
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
                    $emit('update-cart', 
                      item.id_producto,
                      Math.max(1, item.cantidad - 1),
                    )
                "
              >
                -
              </button>
              <QuantityInput
                :model-value="item.cantidad"
                :aria-label="`Cantidad de ${item.nombre} en el carrito`"
                class="w-full rounded ws-inset px-2 py-1 text-center text-sm ws-text outline-none"
                @update:model-value="$emit('update-cart', item.id_producto, $event)"
              />
              <button
                class="rounded ws-inset px-2 py-1 text-sm ws-text ws-hover"
                :aria-label="`Aumentar cantidad de ${item.nombre}`"
                :disabled="item.cantidad >= cartItemStock(item)"
                :title="item.cantidad >= cartItemStock(item) ? `Máximo disponible: ${cartItemStock(item)}` : ''"
                @click="
                  () =>
                    $emit('update-cart', 
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
            Tu carrito está vacío.
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
            @click="$emit('checkout')"
          >
            Procesar compra
          </button>
          <button
            class="w-full rounded-2xl border ws-border ws-surface px-4 py-3 font-bold ws-text transition ws-hover"
            @click="$emit('clear')"
          >
            Limpiar carrito
          </button>
        </div>
      </aside>
    </div>
  </section>
</template>
<script setup>
import QuantityInput from '../QuantityInput.vue';
import { Heart, Package } from 'lucide-vue-next';
defineProps({
  favoriteIds: Array, isFavorite: Function, onlyFavorites: Boolean, canBuy: Function,
  visibleProducts: Array, hasClientFilters: Boolean, availableFor: Function, stockWarning: Object,
  cart: Array, cartItemStock: Function, cartTotal: Object, cantidadInput: Object,
});
defineEmits(['favorite', 'detail', 'quantity-guard', 'quantity-change', 'add', 'remove', 'clear', 'update-cart', 'checkout']);
</script>
<style scoped src="../../styles/store-view.css"></style>
