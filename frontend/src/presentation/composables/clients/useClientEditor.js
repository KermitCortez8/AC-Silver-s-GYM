import { validateAccountForm } from "../../../domain/utils/formValidation.js";
import { useFormValidation } from "../useFormValidation.js";
import { computed, reactive, ref, watch } from "vue";
import { useClientMembershipCatalog } from "./useClientMembershipCatalog.js";
import { normalizePlanName, promotionAvailableForPlan } from "../../../domain/utils/membershipCatalog.js";
import { discountedPrice } from "../../../domain/utils/money.js";
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
  const { plans, promotions, catalogLoading, catalogReady, catalogError, loadCatalog } = useClientMembershipCatalog({ includeHistorical: true });
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
    plan: "",
    id_promocion: 0,
    estado: "EN_TRAMITE",
    pagar_con_stripe: false,
  });

  const { fieldErrors, validateField, revalidateField, validateForm, resetValidation } = useFormValidation(form,
    value => validateAccountForm(value, { requirePassword: !editingId.value }));

  const selectedPlan = computed(() => plans.value.find(p => normalizePlanName(p.name) === normalizePlanName(form.plan)));
  const editorPlans = computed(() => {
    const available = plans.value.filter(p => p.active);
    if (editingId.value && form.plan && !available.some(p => normalizePlanName(p.name) === normalizePlanName(form.plan))) {
      return [...available, selectedPlan.value || { id: 'current-plan', name: form.plan, active: false }];
    }
    return available;
  });
  const availablePromotions = computed(() => {
    const available = promotions.value.filter(p => promotionAvailableForPlan(p, selectedPlan.value?.id));
    if (!editingId.value || !form.id_promocion) return available;
    const current = promotions.value.find(p => Number(p.id_promocion) === Number(form.id_promocion));
    if (!available.some(p => Number(p.id_promocion) === Number(form.id_promocion))) {
      return [...available, current || { id: `promo-${form.id_promocion}`, id_promocion: form.id_promocion,
        name: editingClient.value?.promocion || `Promoción registrada #${form.id_promocion}` }];
    }
    return available;
  });
  const estimatedCharge = computed(() => {
    const basePrice = Number(selectedPlan.value?.price || 0);
    const promotion = availablePromotions.value.find(p => Number(p.id_promocion) === Number(form.id_promocion));
    const finalPrice = promotion && promotionAvailableForPlan(promotion, selectedPlan.value?.id)
      ? discountedPrice(basePrice, promotion.discountValue || 0, promotion.discountType) : basePrice;
    return { finalPrice, discountAmount: Math.round((basePrice - finalPrice) * 100) / 100 };
  });
  const canSaveClient = computed(() => catalogReady.value && !catalogLoading.value
    && (Boolean(editingId.value) || editorPlans.value.some(p => p.name === form.plan && p.active)));
  const refreshCatalog = async () => {
    const loaded = await loadCatalog();
    if (!loaded || !isEditorOpen.value) return;
    if (!editingId.value && !editorPlans.value.some(p => p.name === form.plan)) form.plan = editorPlans.value[0]?.name || '';
    else if (selectedPlan.value) form.plan = selectedPlan.value.name;
  };
  watch([() => form.plan, availablePromotions], () => {
    if (!editingId.value && !availablePromotions.value.some(p => Number(p.id_promocion) === Number(form.id_promocion))) form.id_promocion = 0;
  }, { flush: 'sync' });

  const resetForm = () => {
    resetValidation();
    editingId.value = "";

    form.nombre = "";
    form.correo = "";
    form.telefono = "";
    form.dni = "";
    form.password = "";
    form.plan = "";
    form.id_promocion = 0;
    form.estado = "EN_TRAMITE";
    form.pagar_con_stripe = false;
    submitError.value = "";
  };

  const openNewClient = () => {
    resetForm();
    feedbackMessage.value = "";
    isEditorOpen.value = true;
    return refreshCatalog();
  };

  const closeEditor = () => {
    if (savingClient.value) return;
    isEditorOpen.value = false;
    resetForm();
  };

  const editClient = (client) => {
    resetValidation();
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
    return refreshCatalog();
  };

  const handleSubmit = async () => {
    if (savingClient.value) return;
    savingClient.value = true;
    const isNewClient = !editingId.value;
    submitError.value = "";
    try {
      if (!validateForm()) throw new Error(Object.values(fieldErrors)[0]);
      if (!canSaveClient.value) throw new Error(catalogError.value || 'Espera a que carguen los planes y promociones disponibles.');
      if (!editingId.value && form.id_promocion && !availablePromotions.value.some(p => Number(p.id_promocion) === Number(form.id_promocion))) {
        throw new Error('La promoción seleccionada no está disponible para este plan.');
      }
      const saved = await gymStore.upsertClient({
        id_usuario: editingId.value || undefined,

        nombre: form.nombre,

        correo: form.correo.trim().toLowerCase(),

        telefono: form.telefono,

        dni: form.dni,

        password: form.password,

        plan: editingId.value ? editingClient.value?.plan || form.plan : form.plan,

        id_promocion: editingId.value ? editingClient.value?.id_promocion || undefined : form.id_promocion || undefined,

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
      Object.assign(fieldErrors, error?.fieldErrors || {});
      submitError.value = feedbackMessage.value;
    } finally {
      savingClient.value = false;
    }
  };

  const clientEditorProps = computed(() => ({
    fieldErrors, validateField, revalidateField, availablePromotions: availablePromotions.value,
    editorPlans: editorPlans.value, catalogLoading: catalogLoading.value, catalogError: catalogError.value,
    catalogReady: catalogReady.value, refreshCatalog, canSaveClient: canSaveClient.value,
    closeEditor, editingExpired: editingExpired.value, editingId: editingId.value,
    editingMembershipLabel: editingMembershipLabel.value, editingNeedsActivation: editingNeedsActivation.value,
    registeredAmount: editingClient.value?.membershipPrice,
    estimatedCharge: estimatedCharge.value, form, handleSubmit, isEditorOpen: isEditorOpen.value,
    savingClient: savingClient.value, submitError: submitError.value,
  }));

  return {
    clientEditorProps, editorPlans, catalogLoading, catalogReady, catalogError, refreshCatalog, canSaveClient,
    fieldErrors,
    validateField,
    revalidateField,
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
