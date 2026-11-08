import { promotionErrors } from '../../../domain/utils/formValidation.js';
import { limaDate } from '../../../domain/utils/dates.js';
import { discountedPrice } from '../../../domain/utils/money.js';
import { computed, onMounted, reactive, ref } from 'vue';
import { useGymStore } from '../../../application/stores/gymStore';
import { useTheme } from '../useTheme';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';

/** Gestiona promociones, sus indicadores y el borrador de la regla comercial. */
export const usePromotionsWorkspace = () => {
  ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

  const gymStore = useGymStore();
  const feedback = ref('');
  const feedbackTone = ref('success');
  const plans = computed(() => gymStore.planCatalog);
  const promotions = computed(() => {
    return gymStore.promotions.map((promo) => {
      const usesInStore = gymStore.members.filter((m) => {
        if (!m || m.status === 'INACTIVO') return false;
        const mPromoId = Number(
          m.id_promocion || (m.promocion && String(m.promocion).startsWith('promo-') ? String(m.promocion).replace('promo-', '') : 0)
        );
        return mPromoId === Number(promo.id_promocion);
      }).length;

      const usosActuales = Number(promo.usos_actuales ?? usesInStore);
      return {
        ...promo,
        usos_actuales: usosActuales,
      };
    });
  });

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

  const activePromotionsCount = computed(() => promotions.value.filter(p => p.active).length);

  const activeClients = computed(() => gymStore.members.filter(m => m.status === 'ACTIVO' && m.membershipPrice > 0));

  const totalAhorrado = computed(() => {
    return activeClients.value.reduce((acc, client) => {
      const plan = plans.value.find(p => p.name === client.plan);
      if (plan && client.membershipPrice < plan.price) {
        return acc + (plan.price - client.membershipPrice);
      }
      return acc;
    }, 0);
  });

  const porcentajeVentasConPromo = computed(() => {
    if (activeClients.value.length === 0) return 0;
    const withPromo = activeClients.value.filter(client => {
      const plan = plans.value.find(p => p.name === client.plan);
      return plan && client.membershipPrice < plan.price;
    });
    return (withPromo.length / activeClients.value.length) * 100;
  });

  const ticketMedioConDescuento = computed(() => {
    const withPromo = activeClients.value.filter(client => {
      const plan = plans.value.find(p => p.name === client.plan);
      return plan && client.membershipPrice < plan.price;
    });
    if (withPromo.length === 0) return 0;
    const totalPagado = withPromo.reduce((acc, client) => acc + client.membershipPrice, 0);
    return totalPagado / withPromo.length;
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

  const getPromoStatus = (promo) => {
    if (!promo.active) return { label: 'Pausada', tone: 'slate', icon: 'fa-solid fa-pause' };
    const today = limaDate();
    const isCupoCumplido = promo.limite_cupos && promo.usos_actuales >= promo.limite_cupos;
    const isExpirada = promo.validUntil && promo.validUntil < today;
    if (isCupoCumplido || isExpirada) {
      return { label: 'Terminada', tone: 'amber', icon: 'fa-solid fa-flag-checkered' };
    }
    return { label: 'Activa', tone: 'emerald', icon: 'fa-solid fa-circle-check' };
  };

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

  const chartData = computed(() => {
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();

    const withPromoThisMonth = activeClients.value.filter(client => {
      const plan = plans.value.find(p => p.name === client.plan);
      const hasPromo = plan && client.membershipPrice < plan.price;
      if (!hasPromo) return false;
      
      const startDate = client.membershipStart ? new Date(`${client.membershipStart}T00:00:00`) : new Date();
      return startDate.getMonth() === currentMonth && startDate.getFullYear() === currentYear;
    });
    
    const baseValuesNeto = [0, 0, 0, 0];
    const baseValuesDesc = [0, 0, 0, 0];

    withPromoThisMonth.forEach((client) => {
      const plan = plans.value.find(p => p.name === client.plan);
      const neto = client.membershipPrice;
      const desc = plan.price - client.membershipPrice;
      
      const startDate = client.membershipStart ? new Date(`${client.membershipStart}T00:00:00`) : new Date();
      const day = startDate.getDate();
      
      let weekIndex = 0;
      if (day <= 7) weekIndex = 0;
      else if (day <= 14) weekIndex = 1;
      else if (day <= 21) weekIndex = 2;
      else weekIndex = 3;

      baseValuesNeto[weekIndex] += neto;
      baseValuesDesc[weekIndex] += desc;
    });
    
    return {
      labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
      datasets: [
        {
          label: 'Descuento Otorgado (S/.)',
          backgroundColor: '#a855f7',
          data: baseValuesDesc,
          borderRadius: 4,
        },
        {
          label: 'Ingreso Neto Caja (S/.)',
          backgroundColor: '#f43f5e',
          data: baseValuesNeto,
          borderRadius: 4,
        }
      ]
    };
  });

  const { isDarkTheme } = useTheme();

  const chartOptions = computed(() => ({
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

  onMounted(() => gymStore.fetchFromBackend?.({ section: 'promotions' }).catch(() => {}));

  return {
    gymStore, feedback, feedbackTone, plans, promotions,
    form, activePromotionsCount, activeClients, totalAhorrado, porcentajeVentasConPromo,
    ticketMedioConDescuento, selectSinglePlan, selectedPlan, previewCalculatedPrice, previewSavings,
    getPromoStatus, isModalOpen, saving, modalError, deleting,
    deleteError, openNewModal, closeModal, editModal, chartData,
    isDarkTheme, chartOptions, reset, planNames, edit,
    save, promoToDelete, requestDelete, confirmDelete,
  };
};
