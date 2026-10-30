import { ref } from "vue";
import { useClientPayments } from "../../../application/services/clientPayments.js";
import { canPayClientWithStripe } from "../../../domain/utils/adminClientPayment.js";

export const useClientMembershipActions = ({
  gymStore,
  authStore,
  feedbackMessage,
  feedbackTone,
  viewingClient,
  route,
  router,
  refreshClients,
}) => {
  const {
    retryActivationEmail: sendActivationEmail,
    startClientPayment,
    confirmMembershipPayment,
  } = useClientPayments();
  const activatingClientId = ref("");

  const pendingActivation = ref(null);

  const activationError = ref("");

  const notifyingClientId = ref("");

  const payingClientId = ref("");
  const confirmingPaymentClientId = ref("");

  const paymentError = ref("");

  const requestActivation = (client) => {
    if (activatingClientId.value) return;
    pendingActivation.value = { ...client };
    activationError.value = "";
  };

  const cancelActivation = () => {
    if (activatingClientId.value) return;
    pendingActivation.value = null;
    activationError.value = "";
  };

  const notificationMessage = (notification) => {
    if (notification?.status === "sent")
      return "Correo de activación enviado al cliente.";
    if (notification?.status === "queued")
      return "El correo está pendiente de envío y se reintentará automáticamente.";
    return "El correo no se pudo enviar. Revisa la configuración del servicio y usa Notificar activación para reintentarlo.";
  };

  const retryActivationEmail = async (client) => {
    if (notifyingClientId.value) return;
    notifyingClientId.value = client.id;
    try {
      const idCliente =
        client.id_cliente || Number(String(client.id).replace(/^SGCLI/i, ""));
      const notification = await sendActivationEmail(
        idCliente,
        authStore.token,
      );
      feedbackTone.value = ["sent", "queued"].includes(notification.status)
        ? "success"
        : "info";
      feedbackMessage.value = notificationMessage(notification);
    } catch (error) {
      feedbackTone.value = "error";
      feedbackMessage.value = error.message || "No se pudo enviar el correo.";
    } finally {
      notifyingClientId.value = "";
    }
  };

  const markAsPaidManual = async (client) => {
    if (confirmingPaymentClientId.value || payingClientId.value) return;
    if (
      !client ||
      !window.confirm(
        `¿Confirmas que recibiste el pago en efectivo para la membresía de ${client.name}?`,
      )
    )
      return;
    const idCliente =
      client.id_cliente ||
      Number(String(client.id || "").replace(/^SGCLI/i, ""));

    if (!idCliente) {
      feedbackTone.value = "error";
      feedbackMessage.value = "No se encontró el identificador del cliente.";
      return;
    }

    confirmingPaymentClientId.value = client.id || String(idCliente);
    try {
      const saved = await gymStore.confirmarPagoEfectivo(idCliente);
      if (viewingClient.value && viewingClient.value.id === saved.id) {
        viewingClient.value = { ...saved };
      }
      feedbackTone.value = "success";
      feedbackMessage.value = `Pago de ${saved.id} confirmado correctamente. Ya puedes activar la membresía.`;
    } catch (error) {
      feedbackTone.value = "error";
      feedbackMessage.value =
        error instanceof Error
          ? error.message
          : "No se pudo registrar el pago.";
    } finally {
      confirmingPaymentClientId.value = "";
    }
  };

  const activateMembership = async (client) => {
    if (!client || activatingClientId.value) return;
    const idCliente =
      client.id_cliente ||
      Number(String(client.id || "").replace(/^SGCLI/i, ""));

    if (!idCliente) {
      feedbackTone.value = "error";

      feedbackMessage.value = "No se encontro el ID numerico del cliente.";
      activationError.value = feedbackMessage.value;

      return;
    }

    activatingClientId.value = client.id;
    activationError.value = "";

    try {
      const saved = await gymStore.activateClientMembership(idCliente);
      if (viewingClient.value?.id === saved.id) {
        viewingClient.value = { ...saved };
      }

      feedbackTone.value = "success";

      feedbackMessage.value = `Membresía de ${saved.id} activada. ${notificationMessage(saved.notification)}`;
      pendingActivation.value = null;
    } catch (error) {
      feedbackTone.value = "error";

      feedbackMessage.value =
        error instanceof Error
          ? error.message
          : "No se pudo activar la membresia.";
      activationError.value = feedbackMessage.value;
    } finally {
      activatingClientId.value = "";
    }
  };

  const payWithStripe = async (client) => {
    if (payingClientId.value || confirmingPaymentClientId.value || !canPayClientWithStripe(client)) return;
    payingClientId.value = client.id;
    paymentError.value = "";
    try {
      const payment = await startClientPayment(
        client.id_cliente,
        authStore.token,
      );
      if (!payment.checkout_url)
        throw new Error(payment.message || "No se pudo abrir Stripe.");
      window.location.assign(payment.checkout_url);
    } catch (error) {
      paymentError.value = error.message || "No se pudo iniciar el pago.";
      feedbackTone.value = "error";
      feedbackMessage.value = paymentError.value;
    } finally {
      payingClientId.value = "";
    }
  };
  const initializeDirectory = async () => {
    const stripeResult = route.query.stripe_result;
    if (stripeResult) {
      try {
        if (stripeResult === "success") {
          if (!route.query.session_id)
            throw new Error(
              "Falta la sesión de Stripe para verificar el pago.",
            );
          const result = await confirmMembershipPayment(
            route.query.session_id,
            authStore.token,
          );
          feedbackTone.value = result.confirmed ? "success" : "info";
          feedbackMessage.value = result.confirmed
            ? `Pago de SGCLI${String(result.id_cliente).padStart(3, "0")} confirmado. Ya puedes activar su membresía.`
            : "Stripe todavía no confirmó el pago. Actualiza la lista en unos momentos.";
        } else {
          feedbackTone.value = "info";
          feedbackMessage.value =
            "Pago cancelado. El cliente sigue registrado y puedes retomar el pago desde sus detalles.";
        }
        const { stripe_result, session_id, ...query } = route.query;
        await router.replace({ path: route.path, query });
      } catch (error) {
        feedbackTone.value = "error";
        feedbackMessage.value = `${error.message || "No se pudo verificar el pago."} Recarga esta página para volver a comprobarlo.`;
      }
    }
    await refreshClients(Boolean(stripeResult));
  };

  return {
    activatingClientId,
    pendingActivation,
    activationError,
    notifyingClientId,
    payingClientId,
    confirmingPaymentClientId,
    paymentError,
    requestActivation,
    cancelActivation,
    notificationMessage,
    retryActivationEmail,
    markAsPaidManual,
    activateMembership,
    payWithStripe,
    initializeDirectory,
  };
};
