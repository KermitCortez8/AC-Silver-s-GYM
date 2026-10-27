<template>
  <Teleport to="body">
    <div
      v-if="isAdmin && isProductEditorOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 p-4 backdrop-blur-sm"
    >
      <form
        class="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-950 shadow-2xl"
        @submit.prevent="handleSubmit"
      >
        <!-- Modal header -->
        <div
          class="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-white/10 bg-slate-950 px-6 py-4"
        >
          <div>
            <p
              class="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.35em] text-slate-500"
            >
              <span class="text-orange-400">Producto</span>
              <span>•</span>
              <span>{{
                editingId ? "Edicion de registro" : "Nuevo registro"
              }}</span>
            </p>
            <h2 class="mt-1 text-xl font-black text-white">
              {{ editingId ? "Editar producto" : "Nuevo producto" }}
            </h2>
          </div>
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-2 text-sm font-bold text-slate-400 transition hover:border-white/20 hover:bg-white/5 hover:text-white"
            @click="closeProductEditor"
          >
            <svg
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            Cerrar
          </button>
        </div>

        <div class="p-6 space-y-6">
          <!-- Identificador -->
          <div
            class="flex items-center gap-3 rounded-2xl border border-orange-400/25 bg-orange-400/8 px-4 py-3"
          >
            <div
              class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-orange-400/20"
            >
              <svg
                class="h-4 w-4 text-orange-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a2 2 0 012-2z"
                />
              </svg>
            </div>
            <div>
              <p
                class="text-[10px] font-bold uppercase tracking-[0.3em] text-orange-300"
              >
                Identificador unico
              </p>
              <p class="mt-0.5 font-black text-white">
                {{ currentProductCode }}
              </p>
            </div>
          </div>

          <!-- Sección: Informacion básica -->
          <div>
            <p
              class="mb-3 text-[10px] font-bold uppercase tracking-[0.3em] text-slate-500"
            >
              Informacion del producto
            </p>
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="space-y-2 sm:col-span-2">
                <span
                  class="text-xs font-semibold uppercase tracking-wider text-slate-400"
                  >Nombre del producto</span
                >
                <input
                  v-model="form.nombre"
                  required
                  class="field-input"
                  placeholder="Proteina Whey, Bebida Energetica, etc."
                />
              </label>
              <label class="space-y-2 sm:col-span-2">
                <span
                  class="text-xs font-semibold uppercase tracking-wider text-slate-400"
                  >Descripcion</span
                >
                <textarea
                  v-model="form.descripcion"
                  rows="2"
                  class="field-input"
                  placeholder="Descripcion breve del producto..."
                ></textarea>
              </label>
              <label class="space-y-2">
                <span
                  class="text-xs font-semibold uppercase tracking-wider text-slate-400"
                  >Categoria</span
                >
                <input
                  v-model="form.categoria"
                  class="field-input"
                  placeholder="Suplementos, Bebidas..."
                />
              </label>
              <label class="space-y-2">
                <span
                  class="text-xs font-semibold uppercase tracking-wider text-slate-400"
                  >Item de inventario</span
                >
                <input
                  v-if="editingLinked"
                  :value="linkedItemLabel"
                  class="field-input cursor-not-allowed opacity-70"
                  readonly
                />
                <select v-else v-model="form.id_item" class="field-input">
                  <option :value="null">
                    {{
                      editingId
                        ? "Sin vincular"
                        : "Crear nuevo item en Inventario (Tipo Tienda)"
                    }}
                  </option>
                  <option
                    v-for="item in availableTiendaItems"
                    :key="item.id"
                    :value="itemNumber(item)"
                  >
                    {{ item.inventoryCode }} - {{ item.name }} (reserva
                    {{ item.quantity }})
                  </option>
                </select>
              </label>
            </div>
          </div>

          <div class="border-t border-white/10"></div>

          <!-- Sección: Precios y stock -->
          <div>
            <p
              class="mb-3 text-[10px] font-bold uppercase tracking-[0.3em] text-slate-500"
            >
              Precios y stock
            </p>
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="space-y-2">
                <span
                  class="text-xs font-semibold uppercase tracking-wider text-slate-400"
                  >Unidad de venta</span
                >
                <input
                  v-model="form.unidad_venta"
                  class="field-input"
                  placeholder="unidad, botella, paquete..."
                />
              </label>
              <label class="space-y-2">
                <span
                  class="text-xs font-semibold uppercase tracking-wider text-slate-400"
                  >Precio (S/.)</span
                >
                <input
                  v-model.number="form.precio"
                  type="number"
                  min="0"
                  step="0.01"
                  class="field-input"
                />
              </label>
              <label class="space-y-2">
                <span
                  class="text-xs font-semibold uppercase tracking-wider text-slate-400"
                  >{{
                    stockEditable
                      ? "Stock inicial en Tienda"
                      : "Stock en Tienda"
                  }}</span
                >
                <QuantityInput
                  v-if="stockEditable"
                  v-model="form.cantidad"
                  class="field-input"
                />
                <input
                  v-else
                  :value="stockMostrado"
                  type="number"
                  class="field-input cursor-not-allowed opacity-70"
                  readonly
                />
              </label>
              <label class="space-y-2">
                <span
                  class="text-xs font-semibold uppercase tracking-wider text-slate-400"
                  >Stock minimo</span
                >
                <QuantityInput
                  v-model="form.minimo"
                  class="field-input"
                />
              </label>

              <div
                class="app-notice app-notice--info rounded-2xl border px-4 py-3 text-xs leading-5 sm:col-span-2"
              >
                <p v-if="stockEditable">
                  El stock inicial queda en la Tienda; la reserva de Inventario
                  no cambia.
                </p>
                <p v-else class="font-bold">
                  La Tienda tiene su propio stock: baja con las ventas y sube
                  cuando Inventario la repone (Inventario &rarr; Movimientos,
                  salida con destino Tienda).
                </p>

                <p class="mt-1">
                  El estado se calcula solo:
                  <span class="font-bold">Disponible</span> con stock,
                  <span class="font-bold">Agotado</span> sin stock y
                  <span class="font-bold">Descatalogado</span> (oculto a
                  clientes) si no tiene precio o el item ya no es Tipo Tienda o
                  esta Descontinuado.
                </p>
              </div>
            </div>
          </div>

          <div class="border-t border-white/10"></div>

          <!-- Sección: Imagen -->
          <div>
            <p
              class="mb-3 text-[10px] font-bold uppercase tracking-[0.3em] text-slate-500"
            >
              Imagen del producto
            </p>
            <div class="grid gap-4 lg:grid-cols-[160px_1fr]">
              <!-- Preview -->
              <div
                class="flex aspect-square items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-slate-900 p-2"
              >
                <img
                  v-if="form.imagen_url"
                  :src="form.imagen_url"
                  :alt="form.nombre || 'Producto'"
                  class="h-full w-full object-contain"
                />
                <div
                  v-else
                  class="flex flex-col items-center gap-2 px-4 text-center"
                >
                  <svg
                    class="h-8 w-8 text-slate-700"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  <p class="text-[10px] text-slate-600">Sin imagen</p>
                </div>
              </div>

              <!-- Controles -->
              <div class="space-y-3">
                <div class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="rounded-xl border border-orange-400/30 bg-orange-400/10 px-4 py-2 text-sm font-bold text-orange-200 transition hover:bg-orange-400/20"
                    :disabled="isLoadingBucketImages"
                    @click="openBucketPicker"
                  >
                    {{
                      isLoadingBucketImages
                        ? "Cargando..."
                        : "Elegir de la galería"
                    }}
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
                  <span
                    class="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-500"
                    >Subir desde local</span
                  >
                  <input
                    type="file"
                    accept="image/*"
                    class="field-input"
                    :disabled="isUploadingImage"
                    @change="handleLocalImageUpload"
                  />
                </label>

                <p
                  v-if="isUploadingImage"
                  class="flex items-center gap-2 text-xs font-semibold text-orange-300"
                >
                  <svg
                    class="h-3.5 w-3.5 animate-spin"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    />
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v8z"
                    />
                  </svg>
                  Subiendo imagen a Supabase...
                </p>

                <!-- Bucket picker -->
                <div
                  v-if="isBucketPickerOpen"
                  class="rounded-2xl border border-white/10 bg-slate-900/80 p-4"
                >
                  <div class="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <p
                        class="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-500"
                      >
                        Bucket Supabase
                      </p>
                      <p class="mt-0.5 text-sm font-semibold text-white">
                        imagenestienda
                      </p>
                    </div>
                    <button
                      type="button"
                      class="rounded-xl border border-white/10 px-3 py-1.5 text-xs font-bold text-white hover:bg-white/5"
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
                        class="aspect-square h-full w-full bg-slate-950/60 object-contain p-1"
                      />
                      <p class="truncate px-2 py-1 text-[10px] text-slate-400">
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
                      ? 'app-notice app-notice--error'
                      : 'app-notice app-notice--info'
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
          class="app-notice app-notice--error mx-6 mt-4 rounded-xl border px-4 py-3 text-sm"
        >
          {{ feedbackMessage }}
        </p>

        <!-- Modal footer -->
        <div class="border-t border-white/10 bg-slate-950/80 px-6 py-4">
          <button
            :disabled="isSaving || isUploadingImage"
            type="submit"
            class="w-full rounded-2xl bg-orange-400 px-4 py-3.5 font-black text-slate-950 shadow-lg shadow-orange-500/20 transition hover:bg-orange-300 hover:shadow-orange-400/30 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {{
              isSaving
                ? "Guardando…"
                : editingId
                  ? "Guardar cambios"
                  : "Registrar producto"
            }}
          </button>
        </div>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import QuantityInput from "../QuantityInput.vue";
defineProps([
  "availableTiendaItems",
  "bucketImages",
  "clearSelectedImage",
  "closeBucketPicker",
  "closeProductEditor",
  "currentProductCode",
  "editingId",
  "editingLinked",
  "feedbackMessage",
  "feedbackTone",
  "form",
  "handleLocalImageUpload",
  "handleSubmit",
  "imageFeedback",
  "imageFeedbackTone",
  "isAdmin",
  "isBucketPickerOpen",
  "isLoadingBucketImages",
  "isProductEditorOpen",
  "isSaving",
  "isUploadingImage",
  "itemNumber",
  "linkedItemLabel",
  "openBucketPicker",
  "selectBucketImage",
  "stockEditable",
  "stockMostrado",
]);
</script>

<style scoped src="../../styles/store-view.css"></style>
