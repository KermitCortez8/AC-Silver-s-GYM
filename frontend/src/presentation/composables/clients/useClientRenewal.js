import { onScopeDispose, ref, watch } from 'vue';
import { useClientPayments } from '../../../application/services/clientPayments.js';
import { canRenewClientMembership } from '../../../domain/utils/adminClientPayment.js';

/** Revisa la recompra y confirma el cobro en caja o continúa al checkout existente. */
export const useClientRenewal = ({ authStore, gymStore, refreshClients, viewingClient, feedbackMessage, feedbackTone }) => {
  const payments = useClientPayments();
  const pendingRenewal = ref(null);
  const renewalDetails = ref(null);
  const renewalLoading = ref(false);
  const renewingClientId = ref('');
  const renewalError = ref('');
  const renewalMethod = ref('efectivo');
  const renewalCashReceived = ref(false);
  let version = 0;
  const resetRenewal = () => {
    version++;
    renewingClientId.value = '';
    pendingRenewal.value = null;
    renewalDetails.value = null;
    renewalLoading.value = false;
    renewalError.value = '';
  };
  const closeRenewal = () => { if (!renewingClientId.value) resetRenewal(); };
  watch(() => authStore.token, resetRenewal, { flush: 'sync' });
  const requestRenewal = async (client) => {
    if (renewingClientId.value || renewalLoading.value || !canRenewClientMembership(client)) return;
    const current = ++version, sessionToken = authStore.token;
    const isCurrent = () => current === version && sessionToken === authStore.token;
    pendingRenewal.value = { ...client };
    renewalDetails.value = null;
    renewalError.value = '';
    renewalCashReceived.value = false;
    renewalMethod.value = 'efectivo';
    renewalLoading.value = true;
    try {
      const details = await payments.getAdminRenewalDetails(client.id_cliente, sessionToken);
      if (!isCurrent()) return;
      renewalDetails.value = details;
      if (details.renovacion_pendiente) renewalMethod.value = 'stripe';
    } catch (error) {
      if (isCurrent()) renewalError.value = error.message || 'No se pudieron cargar los detalles de renovación.';
    } finally {
      if (isCurrent()) renewalLoading.value = false;
    }
  };
  const confirmRenewal = async () => {
    if (renewingClientId.value || renewalLoading.value || !pendingRenewal.value || !renewalDetails.value || renewalDetails.value.renovada) return;
    if (renewalMethod.value === 'efectivo' && (!renewalCashReceived.value || renewalDetails.value.renovacion_pendiente)) {
      renewalError.value = 'Confirma el pago recibido en efectivo o continúa con Stripe.';
      return;
    }
    const current = version, sessionToken = authStore.token;
    const isCurrent = () => current === version && sessionToken === authStore.token;
    const client = pendingRenewal.value, details = renewalDetails.value;
    renewingClientId.value = client.id;
    renewalError.value = '';
    try {
      const result = await payments.renewClientMembership(client.id_cliente, {
        id_membresia_origen: details.id_membresia_origen,
        monto_pago: Number(details.monto_pago),
        metodo_pago: renewalMethod.value,
        pago_recibido: renewalMethod.value === 'efectivo' && renewalCashReceived.value,
      }, sessionToken);
      if (!isCurrent()) return;
      if (result.metodo_pago === 'stripe') {
        if (!result.payment?.checkout_url) throw new Error('No se pudo abrir Stripe. Vuelve a revisar la renovación antes de reintentar.');
        window.location.assign(result.payment.checkout_url);
        return;
      }
      feedbackTone.value = 'success';
      feedbackMessage.value = `Membresía de ${client.id} renovada. Pago en efectivo registrado y renovación activa.`;
      await refreshClients(true);
      if (!isCurrent()) return;
      const saved = gymStore.members.find(member => member.id === client.id);
      if (saved && viewingClient.value?.id === client.id) viewingClient.value = { ...saved };
      renewingClientId.value = '';
      closeRenewal();
    } catch (error) {
      if (isCurrent()) renewalError.value = error.message || 'No se pudo completar la renovación.';
    } finally {
      if (isCurrent()) renewingClientId.value = '';
    }
  };
  onScopeDispose(() => { version++; });
  return { pendingRenewal, renewalDetails, renewalLoading, renewingClientId, renewalError,
    renewalMethod, renewalCashReceived, requestRenewal, closeRenewal, confirmRenewal };
};
