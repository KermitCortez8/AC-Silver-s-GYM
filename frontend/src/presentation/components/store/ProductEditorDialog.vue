<template>
  <ResourceModal
    :open="isAdmin && isProductEditorOpen"
    :icon="ShoppingBag"
    :eyebrow="editingId ? 'Tienda · Edición de registro' : 'Tienda · Nuevo registro'"
    :title="editingId ? 'Editar producto' : 'Nuevo producto'"
    subtitle="Define precio, stock e imagen del producto que verán los clientes."
    size="xl"
    :busy="isSaving || isUploadingImage"
    @close="closeProductEditor"
    @submit="handleSubmit"
  >
    <div v-if="formErrors.length" role="alert" class="inv-error">
      <AlertCircle :size="16" aria-hidden="true" />
      <p>{{ missingFieldsMessage(formErrors) }}</p>
    </div>

    <!-- Sección: Informacion básica -->
    <fieldset class="rm-section">
      <legend class="sr-only">Información del producto</legend>
      <p class="rm-section-title">
        <Info :size="14" aria-hidden="true" /> Información del producto
      </p>
      <div class="grid gap-4 sm:grid-cols-2">
        <label class="space-y-2 sm:col-span-2">
          <span class="inv-label inv-required">Nombre del producto</span>
          <input
            v-model="form.nombre"
            class="field-input"
            :class="{ 'is-invalid': formErrors.includes('Nombre') || warnings.nombre }"
            :maxlength="NAME_MAX_LENGTH"
            placeholder="Proteína Whey, Bebida Energética, etc."
            @beforeinput="blockNameChars"
            @input="cleanName"
          />
          <p v-if="warnings.nombre" class="inv-field-error">{{ warnings.nombre }}</p>
        </label>
        <label class="space-y-2 sm:col-span-2">
          <span class="inv-label">Descripción</span>
          <textarea
            v-model="form.descripcion"
            rows="2"
            class="field-input"
            placeholder="Descripción breve del producto..."
          ></textarea>
        </label>
        <div class="space-y-2">
          <label for="product-category" class="inv-label inv-required">Categoría</label>
          <ExtensibleSelect
            id="product-category"
            v-model="form.categoria"
            :options="categoryOptions"
            :invalid="formErrors.includes('Categoría')"
            placeholder="Selecciona una categoría"
            add-label="Agregar nueva categoría"
            add-placeholder="Ej. Suplementos"
          />
        </div>
        <label class="space-y-2">
          <span class="inv-label">Ítem de inventario</span>
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
                  : "Crear nuevo ítem en Inventario (Tipo Tienda)"
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
    </fieldset>

    <!-- Sección: Precios y stock -->
    <fieldset class="rm-section">
      <legend class="sr-only">Precios y stock</legend>
      <p class="rm-section-title">
        <Wallet :size="14" aria-hidden="true" /> Precios y stock
      </p>
      <div class="grid gap-4 sm:grid-cols-2">
        <label class="space-y-2">
          <span class="inv-label inv-required">Precio (S/.)</span>
          <input
            :value="form.precio"
            type="text"
            inputmode="decimal"
            class="field-input"
            :class="{ 'is-invalid': formErrors.includes('Precio') }"
            placeholder="0.00"
            @beforeinput="blockPriceChars"
            @input="cleanPrice"
          />
          <p v-if="warnings.precio" class="inv-field-error">{{ warnings.precio }}</p>
        </label>
        <div class="space-y-2">
          <label for="product-unit" class="inv-label">Unidad de venta</label>
          <ExtensibleSelect
            id="product-unit"
            v-model="form.unidad_venta"
            :options="unitOptions"
            placeholder="Selecciona una unidad"
            add-label="Agregar nueva unidad"
            add-placeholder="Ej. Botella"
          />
        </div>
        <label class="space-y-2">
          <span class="inv-label" :class="{ 'inv-required': stockEditable }">{{
            stockEditable ? "Stock inicial en Tienda" : "Stock en Tienda"
          }}</span>
          <QuantityInput
            v-if="stockEditable"
            v-model="form.cantidad"
            class="field-input"
            :class="{ 'is-invalid': formErrors.includes('Stock inicial') }"
            placeholder="0"
          />
          <input
            v-else
            :value="stockMostrado"
            type="text"
            class="field-input cursor-not-allowed opacity-70"
            readonly
          />
        </label>
        <label class="space-y-2">
          <span class="inv-label">Stock mínimo</span>
          <QuantityInput
            v-model="form.minimo"
            class="field-input"
          />
          <p v-if="warnings.stock" class="inv-field-error">{{ warnings.stock }}</p>
        </label>

        <div class="app-notice app-notice--info inv-info sm:col-span-2">
          <Info :size="16" aria-hidden="true" />
          <div>
            <p v-if="stockEditable">
              El stock inicial queda en la Tienda; la reserva de Inventario no
              cambia.
            </p>
            <p v-else class="font-bold">
              La Tienda tiene su propio stock: baja con las ventas y sube cuando
              Inventario la repone (Inventario &rarr; Movimientos, salida con
              destino Tienda).
            </p>

            <p class="mt-1">
              El estado se calcula solo:
              <span class="font-bold">Disponible</span> con stock,
              <span class="font-bold">Agotado</span> sin stock y
              <span class="font-bold">Descatalogado</span> (oculto a clientes)
              si no tiene precio o el ítem ya no es Tipo Tienda o está
              Descontinuado.
            </p>
          </div>
        </div>
      </div>
    </fieldset>

    <!-- Sección: Imagen -->
    <fieldset class="rm-section">
      <legend class="sr-only">Imagen del producto</legend>
      <p class="rm-section-title">
        <ImageIcon :size="14" aria-hidden="true" /> Imagen del producto
      </p>
      <div class="grid gap-4 sm:grid-cols-[160px_1fr]">
        <!-- Preview -->
        <div
          class="mx-auto flex aspect-square w-40 items-center justify-center overflow-hidden rounded-2xl border border-dashed border-white/20 bg-white/[0.04] p-2 sm:mx-0"
        >
          <img
            v-if="form.imagen_url"
            :src="form.imagen_url"
            :alt="form.nombre || 'Producto'"
            class="h-full w-full object-contain"
          />
          <div v-else class="flex flex-col items-center gap-2 px-4 text-center">
            <ImageIcon :size="32" class="text-slate-500" aria-hidden="true" />
            <p class="text-[11px] text-slate-500">Sin imagen</p>
          </div>
        </div>

        <!-- Controles -->
        <div class="space-y-3">
          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-2 text-sm font-bold text-amber-200 transition hover:bg-amber-400/20"
              :disabled="isLoadingBucketImages"
              @click="openBucketPicker"
            >
              <Images :size="16" aria-hidden="true" />
              {{
                isLoadingBucketImages ? "Cargando..." : "Elegir de la galería"
              }}
            </button>
            <button
              v-if="form.imagen_url"
              type="button"
              class="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm font-bold text-slate-300 transition hover:bg-white/5"
              @click="clearSelectedImage"
            >
              <Trash2 :size="16" aria-hidden="true" />
              Quitar imagen
            </button>
          </div>

          <label class="block space-y-2">
            <span class="inv-label">Subir desde local (.png o .jpg)</span>
            <input
              type="file"
              accept=".png,.jpg,.jpeg,image/png,image/jpeg"
              class="field-input"
              :disabled="isUploadingImage"
              @change="handleLocalImageUpload"
            />
          </label>

          <p
            v-if="isUploadingImage"
            class="flex items-center gap-2 text-xs font-semibold text-amber-300"
          >
            <Loader2 :size="14" class="animate-spin" aria-hidden="true" />
            Subiendo imagen a Supabase...
          </p>

          <!-- Bucket picker -->
          <div
            v-if="isBucketPickerOpen"
            class="rounded-2xl border border-white/10 bg-white/[0.04] p-4"
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
                class="rm-btn-secondary"
                style="padding: 0.4rem 0.75rem; font-size: 0.75rem"
                @click="closeBucketPicker"
              >
                Cerrar galería
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
                class="overflow-hidden rounded-xl border transition hover:border-amber-400"
                :class="
                  form.imagen_url === image.url
                    ? 'border-amber-400 ring-2 ring-amber-400/40'
                    : 'border-white/10'
                "
                :aria-pressed="form.imagen_url === image.url"
                @click="selectBucketImage(image)"
              >
                <img
                  :src="image.url"
                  :alt="image.name"
                  class="aspect-square h-full w-full object-contain p-1"
                />
                <p class="truncate px-2 py-1 text-[10px] text-slate-400">
                  {{ image.name }}
                </p>
              </button>
            </div>
            <p
              v-else
              class="rounded-xl border border-dashed border-white/10 px-4 py-6 text-center text-xs text-slate-400"
            >
              Todavía no hay imágenes en la galería.
            </p>
          </div>

          <p
            v-if="imageFeedback"
            class="rounded-xl border px-3 py-2 text-xs"
            :class="
              feedbackClass(imageFeedbackTone)
            "
          >
            {{ imageFeedback }}
          </p>
        </div>
      </div>
    </fieldset>

    <p
      v-if="feedbackMessage && feedbackTone === 'error'"
      role="alert"
      class="rounded-xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200"
    >
      {{ feedbackMessage }}
    </p>

    <template #footer>
      <button
        type="button"
        class="rm-btn-secondary"
        :disabled="isSaving || isUploadingImage"
        @click="closeProductEditor"
      >
        Cancelar
      </button>
      <button
        :disabled="isSaving || isUploadingImage"
        type="submit"
        class="rounded-2xl bg-amber-400 px-5 py-3 font-black text-slate-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {{
          isSaving
            ? "Guardando…"
            : editingId
              ? "Guardar cambios"
              : "Registrar producto"
        }}
      </button>
    </template>
  </ResourceModal>
</template>

<script setup>
import QuantityInput from "../QuantityInput.vue";
import { feedbackClass } from "../../utils/feedback.js";
import { reactive } from "vue";
import {
  AlertCircle,
  Image as ImageIcon,
  Images,
  Info,
  Loader2,
  ShoppingBag,
  Trash2,
  Wallet,
} from "lucide-vue-next";
import ResourceModal from "../ResourceModal.vue";
import ExtensibleSelect from "../common/ExtensibleSelect.vue";
import { blockNonDecimal, blockSpecialChars } from "../../utils/inputGuards.js";
import {
  cleanDecimal,
  cleanText,
  missingFieldsMessage,
  NAME_MAX_LENGTH,
} from "../../../domain/utils/inputRules.js";

const props = defineProps([
  "categoryOptions",
  "unitOptions",
  "formErrors",
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

// Avisos al escribir: el campo bloquea lo no permitido y explica por que.
const warnings = reactive({ nombre: "", precio: "", stock: "" });
const blockNameChars = blockSpecialChars((message) => { warnings.nombre = message; });
const blockPriceChars = blockNonDecimal((message) => { warnings.precio = message; });

const cleanName = (event) => {
  const { value, rejected } = cleanText(event.target.value, NAME_MAX_LENGTH);
  if (value !== event.target.value) event.target.value = value;
  props.form.nombre = value;
  warnings.nombre = rejected ? "Sin caracteres especiales: solo letras, números y espacios." : "";
};

const cleanPrice = (event) => {
  const value = cleanDecimal(event.target.value);
  if (value !== event.target.value) event.target.value = value;
  props.form.precio = value;
  warnings.precio = "";
};

</script>

<style scoped src="../../styles/store-view.css"></style>
