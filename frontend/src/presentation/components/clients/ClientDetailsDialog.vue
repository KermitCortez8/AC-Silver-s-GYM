<template>
  <WorkspaceDialog
    :open="isDetailsOpen && Boolean(viewingClient)"
    title="Detalles del cliente"
    @close="closeDetails"
  >
    <template v-if="viewingClient">
      <div class="mb-6 border-b ws-border pb-5">
        <h3 class="text-2xl font-black ws-text break-words">
          {{ viewingClient.name || "Sin nombre" }}
        </h3>
        <span class="ws-badge ws-tint-info ws-info mt-3">{{
          viewingClient.id
        }}</span>
      </div>
      <dl class="client-detail-grid">
        <div class="client-detail-wide">
          <dt>Correo electrónico</dt>
          <dd>{{ viewingClient.email || "Sin correo" }}</dd>
        </div>
        <div>
          <dt>DNI</dt>
          <dd>{{ viewingClient.dni || "Sin DNI" }}</dd>
        </div>
        <div>
          <dt>Teléfono</dt>
          <dd>{{ viewingClient.phone || "Sin teléfono" }}</dd>
        </div>
        <div>
          <dt>Plan</dt>
          <dd>{{ viewingClient.plan || "MENSUAL" }}</dd>
        </div>
        <div>
          <dt>Promoción</dt>
          <dd>{{ viewingClient.promocion && viewingClient.promocion !== 'SIN PROMOCION' ? viewingClient.promocion : "SIN PROMOCIÓN" }}</dd>
        </div>
        <div>
          <dt>Membresía</dt>
          <dd>
            <span
              class="ws-badge"
              :class="membershipBadgeClass(viewingClient)"
              >{{ clientMembershipLabel(viewingClient) }}</span
            >
          </dd>
        </div>
        <div>
          <dt>Vigencia</dt>
          <dd>
            {{ viewingClient.membershipStart || "Por activar" }}
            <span class="block ws-muted text-xs mt-1">
              hasta {{ viewingClient.membershipEnd || "Por activar" }}
            </span>
          </dd>
        </div>

        <div
          v-if="viewingClient.paymentReference || viewingClient.paymentStatus"
          class="client-detail-wide"
        >
          <dt>Pago</dt>
          <dd>
            {{ viewingClient.paymentStatus || "PENDIENTE" }}
            <span
              v-if="viewingClient.paymentReference"
              class="block ws-muted text-sm mt-1"
            >
              {{ viewingClient.paymentReference }}
            </span>
          </dd>
        </div>

        <div
          v-if="
            Number(viewingClient.membershipPrice || 0) > 0 &&
            getPlanPrice(viewingClient.plan) >
              Number(viewingClient.membershipPrice || 0)
          "
          class="client-detail-wide"
        >
          <dt>Descuento aplicado</dt>
          <dd>
            Precio base: S/. {{ getPlanPrice(viewingClient.plan).toFixed(2) }}
            <span class="block ws-success text-sm mt-1">
              Pagado: S/.
              {{ Number(viewingClient.membershipPrice || 0).toFixed(2) }} ·
              Ahorro: S/.
              {{
                (
                  getPlanPrice(viewingClient.plan) -
                  Number(viewingClient.membershipPrice || 0)
                ).toFixed(2)
              }}
            </span>
          </dd>
        </div>
      </dl>

      <p
        v-if="clientMembershipGroup(viewingClient) === 'expired'"
        class="mt-6 rounded-xl ws-tint-danger ws-danger p-4 text-sm"
        role="status"
      >
        Acceso bloqueado por membresía vencida. Para recuperar el acceso, el
        cliente necesita una nueva membresía pagada y activada.
      </p>

      <div class="mt-6 flex flex-col gap-3">
        <button
          v-if="
            isActiveStatus(viewingClient.status) &&
            isActiveStatus(viewingClient.membershipStatus)
          "
          type="button"
          class="ws-btn"
          :disabled="Boolean(notifyingClientId)"
          @click="retryActivationEmail(viewingClient)"
        >
          <Mail :size="17" aria-hidden="true" />{{
            notifyingClientId === viewingClient.id
              ? "Enviando…"
              : "Notificar activación"
          }}
        </button>
        <p v-if="paymentError" role="alert" class="text-sm ws-warning">
          {{ paymentError }}
        </p>
        <button
          v-if="canPayClientWithStripe(viewingClient)"
          type="button"
          class="w-full rounded-xl ws-primary px-4 py-3 font-bold disabled:opacity-50"
          :disabled="Boolean(payingClientId || confirmingPaymentClientId)"
          @click="payWithStripe(viewingClient)"
        >
          {{
            payingClientId
              ? "Abriendo Stripe..."
              : `Pagar S/. ${Number(viewingClient.membershipPrice || 0).toFixed(2)} con Stripe`
          }}
        </button>
        <button
          v-if="viewingClient.paymentStatus === 'PENDIENTE'"
          type="button"
          class="w-full rounded-xl border ws-border-warning ws-tint-warning px-4 py-3 font-bold ws-warning transition ws-hover"
          :disabled="Boolean(confirmingPaymentClientId || payingClientId)"
          :aria-busy="Boolean(confirmingPaymentClientId)"
          @click="markAsPaidManual(viewingClient)"
        >
          {{ confirmingPaymentClientId ? 'Confirmando pago…' : 'Confirmar Pago (Manual/Efectivo)' }}
        </button>
        <button
          v-if="
            viewingClient.paymentStatus === 'PAGADO' &&
            clientMembershipGroup(viewingClient) === 'pending'
          "
          type="button"
          class="w-full rounded-xl border ws-border-success ws-tint-success px-4 py-3 font-bold ws-success transition ws-hover"
          @click="requestActivation(viewingClient)"
        >
          Activar Membresía
        </button>
      </div>
    </template>
  </WorkspaceDialog>
</template>

<script setup>
import WorkspaceDialog from "../WorkspaceDialog.vue";
import { Mail } from "lucide-vue-next";
defineProps([
  "canPayClientWithStripe",
  "clientMembershipGroup",
  "clientMembershipLabel",
  "closeDetails",
  "getPlanPrice",
  "isActiveStatus",
  "isDetailsOpen",
  "markAsPaidManual",
  "membershipBadgeClass",
  "notifyingClientId",
  "confirmingPaymentClientId",
  "payWithStripe",
  "payingClientId",
  "paymentError",
  "requestActivation",
  "retryActivationEmail",
  "viewingClient",
]);
</script>

<style scoped src="../../styles/clients-view.css"></style>
