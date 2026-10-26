<template>
  <WorkspaceDialog
    :open="isEditorOpen"
    :busy="savingClient"
    :title="editingId ? 'Editar cliente' : 'Nuevo cliente'"
    @close="closeEditor"
  >
    <form @submit.prevent="handleSubmit">
      <fieldset :disabled="savingClient" class="mt-6 grid gap-4 sm:grid-cols-2">
        <label class="space-y-2 sm:col-span-2">
          <span class="text-sm ws-soft">Nombre</span>

          <input
            v-model="form.nombre"
            required
            class="ws-input"
            placeholder="Jose Perez"
          />
        </label>

        <label class="space-y-2 sm:col-span-2">
          <span class="text-sm ws-soft">Correo</span>

          <input
            v-model="form.correo"
            required
            type="email"
            class="ws-input"
            placeholder="cliente@correo.com"
          />
        </label>

        <label class="space-y-2 sm:col-span-2">
          <span class="text-sm ws-soft">Contraseña</span>

          <input
            v-model="form.password"
            :required="!editingId"
            minlength="6"
            type="password"
            autocomplete="new-password"
            class="ws-input"
            :placeholder="
              editingId
                ? 'Dejar vacio para conservar la actual'
                : 'Minimo 6 caracteres'
            "
          />
        </label>

        <label class="space-y-2">
          <span class="text-sm ws-soft">Teléfono</span>
          <input
            v-model="form.telefono"
            class="ws-input"
            placeholder="999 111 222"
          />
        </label>

        <label class="space-y-2">
          <span class="text-sm ws-soft">DNI</span>
          <input
            v-model="form.dni"
            required
            class="ws-input"
            placeholder="12345678"
          />
        </label>

        <label class="space-y-2">
          <span class="text-sm ws-soft">Plan</span>
          <select v-model="form.plan" class="ws-input">
            <option value="MENSUAL">MENSUAL</option>
            <option value="3 MESES">3 MESES</option>
            <option value="ANUAL">ANUAL</option>
          </select>
        </label>

        <label class="space-y-2">
          <span class="text-sm ws-soft">Promocion</span>
          <select v-model="form.id_promocion" class="ws-input">
            <option :value="0">SIN PROMOCION</option>
            <option
              v-for="p in availablePromotions"
              :key="p.id"
              :value="p.id_promocion"
            >
              {{ p.name }}
            </option>
          </select>
          <p class="text-xs ws-muted">
            Precio estimado: S/. {{ estimatedCharge.finalPrice }}
            <span v-if="estimatedCharge.discountAmount > 0" class="ws-warning">
              (descuento: S/. {{ estimatedCharge.discountAmount }})
            </span>
          </p>
        </label>

        <label v-if="editingId" class="space-y-2 sm:col-span-2">
          <span class="text-sm ws-soft">Estado de membresía</span>
          <p class="ws-input">{{ editingMembershipLabel }}</p>
          <p v-if="editingNeedsActivation" class="text-xs ws-muted">
            La preinscripción se activa desde «Activar», después de confirmar el
            pago.
          </p>
          <p v-if="editingExpired" class="text-xs ws-danger">
            La membresía está vencida. Se necesita una nueva membresía pagada y
            activada para recuperar el acceso.
          </p>
        </label>

        <label v-if="!editingId" class="space-y-2 sm:col-span-2">
          <span class="flex items-center gap-3 text-sm ws-text">
            <input v-model="form.pagar_con_stripe" type="checkbox" />
            Realizar el pago con Stripe al registrar
          </span>
          <p class="text-xs ws-muted">
            El cliente quedará en trámite, con pago pendiente. Puedes pagar
            ahora o después desde sus detalles. La membresía se activa después
            de confirmar el pago.
          </p>
        </label>
      </fieldset>

      <p v-if="submitError" role="alert" class="mt-4 text-sm ws-warning">
        {{ submitError }}
      </p>

      <button
        type="submit"
        :disabled="savingClient"
        class="mt-6 w-full rounded-2xl ws-primary px-4 py-3 font-bold transition disabled:opacity-50"
      >
        {{
          savingClient
            ? "Guardando..."
            : editingId
              ? "Guardar cambios"
              : form.pagar_con_stripe
                ? "Registrar y pagar con Stripe"
                : "Registrar cliente"
        }}
      </button>
    </form>
  </WorkspaceDialog>
</template>

<script setup>
import WorkspaceDialog from "../WorkspaceDialog.vue";
defineProps([
  "availablePromotions",
  "closeEditor",
  "editingExpired",
  "editingId",
  "editingMembershipLabel",
  "editingNeedsActivation",
  "estimatedCharge",
  "form",
  "handleSubmit",
  "isEditorOpen",
  "savingClient",
  "submitError",
]);
</script>

<style scoped src="../../styles/clients-view.css"></style>
