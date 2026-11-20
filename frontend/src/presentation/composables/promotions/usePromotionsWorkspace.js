import { promotionErrors } from '../../../domain/utils/formValidation.js';
import { limaDate } from '../../../domain/utils/dates.js';
import { discountedPrice, toCents } from '../../../domain/utils/money.js';
import { promotionStatus } from '../../../domain/utils/membershipCatalog.js';
import { filterMembershipPayments } from '../../../domain/utils/membershipPayments.js';
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../../../application/stores/gymStore';
import { useTheme } from '../useTheme';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';

const promotionStatuses = {
  current: { label: 'Activa', tone: 'emerald', icon: 'fa-solid fa-circle-check' },
  ended: { label: 'Terminada', tone: 'amber', icon: 'fa-solid fa-flag-checkered' },
  scheduled: { label: 'Programada', tone: 'rose', icon: 'fa-solid fa-clock' },
  paused: { label: 'Pausada', tone: 'slate', icon: 'fa-solid fa-pause' },
};

/** Gestiona promociones, sus indicadores y el borrador de la regla comercial. */
export const usePromotionsWorkspace = () => {
  ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

  const gymStore = useGymStore();
  const feedback = ref('');
  const feedbackTone = ref('success');
  const plans = computed(() => gymStore.planCatalog);
  const today = ref(limaDate());
  const promotions = computed(() => gymStore.promotions.map(promo => ({
    ...promo,
    status: promotionStatus(promo, today.value),
  })));

  const form = reactive({
    id_promocion: null,
    name: '',
    description: '',
    discountType: 'percent',
    discountValue: 10,
    startsAt: '',
    validUntil: '',
    icono_etiqueta: '🏷️',
    palabra_clave: '',
    appliesTo: [],
    limite_cupos: null,
    usos_actuales: 0,
    active: true,
  });

  const activePromotionsCount = computed(() => promotions.value.filter(promo => promo.status === 'current').length);
  const paymentsReady = ref(false);
  const paymentMetrics = computed(() => {
    const payments = filterMembershipPayments(gymStore.membershipPayments, {
      status: 'PAGADO', from: `${today.value.slice(0, 7)}-01`, to: today.value,
    });
    const withPromotion = [0, 0, 0, 0];
    const withoutPromotion = [0, 0, 0, 0];
    let promotionCount = 0;
    for (const payment of payments) {
      const index = Math.min(3, Math.floor((Number(payment.fecha_pago.slice(8, 10)) - 1) / 7));
      const hasPromotion = Number(payment.id_promocion) > 0;
      const series = hasPromotion ? withPromotion : withoutPromotion;
      series[index] += toCents(payment.monto_pago);
      if (hasPromotion) promotionCount++;
    }
    const collected = withPromotion.reduce((sum, amount) => sum + amount, 0) / 100;
    return {
      collected,
      share: payments.length ? 100 * promotionCount / payments.length : 0,
      average: promotionCount ? collected / promotionCount : 0,
      withPromotion: withPromotion.map(amount => amount / 100),
      withoutPromotion: withoutPromotion.map(amount => amount / 100),
    };
  });

  // Selección de Plan Único
  const selectSinglePlan = (planId) => {
    form.appliesTo = [planId];
  };

  const selectedPlan = computed(() => {
    if (!form.appliesTo.length) return plans.value[0] || null;
    return plans.value.find(p => p.id === form.appliesTo[0]) || plans.value[0] || null;
  });

  const previewCalculatedPrice = computed(() => {
    if (!selectedPlan.value) return 0;
    const basePrice = Number(selectedPlan.value.price || 0);
    const val = Number(form.discountValue || 0);
    return discountedPrice(basePrice, val, form.discountType);
  });

  const previewSavings = computed(() => {
    if (!selectedPlan.value) return 0;
    const basePrice = Number(selectedPlan.value.price || 0);
    return Math.max(0, basePrice - previewCalculatedPrice.value);
  });

  const getPromoStatus = (promo) => promotionStatuses[promo.status ?? promotionStatus(promo, today.value)];

  const isModalOpen = ref(false);
  const saving = ref(false);
  const modalError = ref('');
  const deleting = ref(false);
  const deleteError = ref('');
  const openNewModal = () => {
    reset();
    modalError.value = '';
    isModalOpen.value = true;
  };
  const closeModal = () => {
    if (saving.value) return;
    isModalOpen.value = false;
  };
  const editModal = (promo) => {
    if (getPromoStatus(promo).label === 'Terminada') {
      feedbackTone.value = 'error';
      feedback.value = 'Las promociones terminadas no se pueden editar, únicamente eliminar.';
      return;
    }
    modalError.value = '';
    edit(promo);
    isModalOpen.value = true;
  };

  const chartData = computed(() => ({
      labels: ['1–7', '8–14', '15–21', '22–fin'],
      datasets: [
        {
          label: 'Con promoción (S/)',
          backgroundColor: '#a855f7',
          data: paymentMetrics.value.withPromotion,
          borderRadius: 4,
        },
        {
          label: 'Sin promoción (S/)',
          backgroundColor: '#f43f5e',
          data: paymentMetrics.value.withoutPromotion,
          borderRadius: 4,
        }
      ]
  }));

  const { isDarkTheme } = useTheme();

  const chartOptions = computed(() => ({
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: isDarkTheme.value ? '#cbd5e1' : '#525252' } }
    },
    scales: {
      x: { ticks: { color: isDarkTheme.value ? '#94a3b8' : '#737373' }, grid: { color: isDarkTheme.value ? 'rgba(255,255,255,0.1)' : 'rgba(23,23,23,0.1)' } },
      y: { ticks: { color: isDarkTheme.value ? '#94a3b8' : '#737373' }, grid: { color: isDarkTheme.value ? 'rgba(255,255,255,0.1)' : 'rgba(23,23,23,0.1)' } }
    }
  }));

  const reset = () => {
    const defaultPlanId = plans.value[0]?.id || null;
    Object.assign(form, {
      id_promocion: null,
      name: '',
      description: '',
      discountType: 'percent',
      discountValue: 10,
      startsAt: '',
      validUntil: '',
      icono_etiqueta: '🏷️',
      palabra_clave: '',
      appliesTo: defaultPlanId ? [defaultPlanId] : [],
      limite_cupos: null,
      usos_actuales: 0,
      active: true,
    });
  };

  const planNames = (promo) => promo.appliesTo.map((id) => plans.value.find((plan) => plan.id === id)?.name).filter(Boolean);

  const edit = (promo) => {
    const plansList = Array.isArray(promo.appliesTo) ? promo.appliesTo : [];
    Object.assign(form, {
      id_promocion: promo.id_promocion,
      name: promo.name,
      description: promo.description,
      discountType: promo.discountType,
      discountValue: promo.discountValue,
      startsAt: promo.startsAt,
      validUntil: promo.validUntil,
      icono_etiqueta: promo.icono_etiqueta || '🏷️',
      palabra_clave: promo.palabra_clave || '',
      appliesTo: plansList.slice(0, 1),
      limite_cupos: promo.limite_cupos !== undefined && promo.limite_cupos !== null ? promo.limite_cupos : null,
      usos_actuales: promo.usos_actuales || 0,
      active: promo.active,
    });
  };

  const save = async () => {
    if (saving.value) return;
    modalError.value = '';
    const invalid = Object.values(promotionErrors(form))[0];
    if (invalid) {
      feedbackTone.value = 'error';
      modalError.value = invalid;
      return;
    }
    saving.value = true;
    try {
      await gymStore.upsertPromotion({ ...form });
      feedbackTone.value = 'success';
      feedback.value = 'Promoción guardada exitosamente.';
      saving.value = false;
      closeModal();
    } catch (error) {
      feedbackTone.value = 'error';
      modalError.value = error instanceof Error ? error.message : 'No se pudo guardar la promoción.';
    } finally { saving.value = false; }
  };

  const promoToDelete = ref(null);

  const requestDelete = (promo) => {
    if (deleting.value) return;
    deleteError.value = '';
    promoToDelete.value = promo;
  };

  const confirmDelete = async () => {
    if (!promoToDelete.value || deleting.value) return;
    const target = promoToDelete.value;
    deleting.value = true;
    deleteError.value = '';
    try {
      await gymStore.deletePromotion(target.id_promocion);
      promoToDelete.value = null;
      feedbackTone.value = 'success';
      feedback.value = 'Promoción eliminada exitosamente.';
    } catch (error) {
      feedbackTone.value = 'error';
      deleteError.value = error instanceof Error ? error.message : 'No se pudo eliminar la promoción.';
    } finally { deleting.value = false; }
  };

  let dateTimer;
  onMounted(() => {
    dateTimer = setInterval(() => { today.value = limaDate(); }, 60_000);
    gymStore.fetchFromBackend({ section: 'promotions' }).catch(() => {});
    gymStore.fetchFromBackend({ section: 'payments' })
      .then(() => { paymentsReady.value = true; }).catch(() => {});
  });
  onBeforeUnmount(() => clearInterval(dateTimer));

  return {
    gymStore, feedback, feedbackTone, plans, promotions,
    form, activePromotionsCount, paymentMetrics, paymentsReady,
    selectSinglePlan, selectedPlan, previewCalculatedPrice, previewSavings,
    getPromoStatus, isModalOpen, saving, modalError, deleting,
    deleteError, openNewModal, closeModal, editModal, chartData,
    isDarkTheme, chartOptions, reset, planNames, edit,
    save, promoToDelete, requestDelete, confirmDelete,
  };
};
