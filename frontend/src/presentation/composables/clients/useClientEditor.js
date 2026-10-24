import { computed, reactive, ref } from "vue";
import {
  clientMembershipGroup,
  clientMembershipLabel,
} from "../../../domain/utils/clientDirectory.js";

export const useClientEditor = ({
  gymStore,
  clients,
  feedbackMessage,
  feedbackTone,
  resetFilters,
  sortOrder,
  openDetails,
  paymentError,
  normalizeStatus,
}) => {
  const editingId = ref("");

  const isEditorOpen = ref(false);

  const savingClient = ref(false);

  const submitError = ref("");

  const editingClient = computed(() =>
    clients.value.find((entry) => entry.id === editingId.value),
  );

  const editingMembershipLabel = computed(() =>
    clientMembershipLabel(editingClient.value || {}),
  );

  const editingNeedsActivation = computed(
    () =>
      editingClient.value &&
      clientMembershipGroup(editingClient.value) === "pending",
  );

  const editingExpired = computed(() => {
    const client = clients.value.find((entry) => entry.id === editingId.value);
    return (
      client &&
      (clientMembershipGroup(client) === "expired" ||
        normalizeStatus(client.status) === "VENCIDA")
    );
  });

  const form = reactive({
    nombre: "",
    correo: "",
    telefono: "",
    dni: "",
    password: "",
    plan: "MENSUAL",
    id_promocion: 0,
    estado: "EN_TRAMITE",
    pagar_con_stripe: false,
  });

  const availablePromotions = computed(() => {
    const active = gymStore.activePromotions;
    if (form.id_promocion) {
      const current = gymStore.promotions.find(
        (p) => Number(p.id_promocion) === Number(form.id_promocion),
      );
      if (
        current &&
        !active.some(
          (p) => Number(p.id_promocion) === Number(current.id_promocion),
        )
      ) {
        return [...active, current];
      }
    }
    return active;
  });

  const estimatedCharge = computed(() => {
    try {
      const plan =
        gymStore.planCatalog.find((p) => p.name === form.plan) ||
        gymStore.planCatalog[0];
      if (!plan) return { finalPrice: 0, discountAmount: 0 };
      return gymStore.calculatePlanCharge(
        plan.id,
        form.id_promocion ? `promo-${form.id_promocion}` : "",
      );
    } catch (e) {
      return { finalPrice: 0, discountAmount: 0 };
    }
  });

  const resetForm = () => {
    editingId.value = "";

    form.nombre = "";
    form.correo = "";
    form.telefono = "";
    form.dni = "";
    form.password = "";
    form.plan = "MENSUAL";
    form.id_promocion = 0;
    form.estado = "EN_TRAMITE";
    form.pagar_con_stripe = false;
    submitError.value = "";
  };

  const openNewClient = () => {
    resetForm();
    feedbackMessage.value = "";
    isEditorOpen.value = true;
  };

  const closeEditor = () => {
    if (savingClient.value) return;
    isEditorOpen.value = false;
    resetForm();
  };

  const editClient = (client) => {
    submitError.value = "";
    editingId.value = client.id;

    form.nombre = client.name || "";
    form.correo = client.email || "";
    form.telefono = client.phone || "";
    form.dni = client.dni || "";
    form.password = "";
    form.plan = client.plan || "MENSUAL";
    form.id_promocion = Number(client.id_promocion || 0);
    form.estado = client.status || "ACTIVO";

    feedbackMessage.value = "";
    isEditorOpen.value = true;
  };

  const handleSubmit = async () => {
    if (savingClient.value) return;
    savingClient.value = true;
    const isNewClient = !editingId.value;
    submitError.value = "";
    try {
      const saved = await gymStore.upsertClient({
        id_usuario: editingId.value || undefined,

        nombre: form.nombre,

        correo: form.correo,

        telefono: form.telefono,

        dni: form.dni,

        password: form.password,

        plan: form.plan,

        id_promocion: form.id_promocion || undefined,

        estado: form.estado,
        pagar_con_stripe: !editingId.value && form.pagar_con_stripe,
      });

      if (isNewClient) {
        resetFilters();
        sortOrder.value = "recent";
      }
      savingClient.value = false;
      closeEditor();

      feedbackTone.value = "success";

      feedbackMessage.value = `Cliente ${saved.id} guardado con estado ${saved.status || form.estado}.`;
      if (saved.payment?.checkout_url) {
        window.location.assign(saved.payment.checkout_url);
      } else if (saved.payment?.message) {
        feedbackTone.value = "info";
        feedbackMessage.value = `Cliente ${saved.id} registrado. ${saved.payment.message}. Puedes retomar el pago desde sus detalles.`;
        openDetails(saved);
        paymentError.value = saved.payment.message;
      }
    } catch (error) {
      feedbackTone.value = "error";

      feedbackMessage.value =
        error instanceof Error
          ? error.message
          : "No se pudo guardar el cliente.";
      submitError.value = feedbackMessage.value;
    } finally {
      savingClient.value = false;
    }
  };

  return {
    editingId,
    isEditorOpen,
    savingClient,
    submitError,
    editingClient,
    editingMembershipLabel,
    editingNeedsActivation,
    editingExpired,
    form,
    availablePromotions,
    estimatedCharge,
    resetForm,
    openNewClient,
    closeEditor,
    editClient,
    handleSubmit,
  };
};
