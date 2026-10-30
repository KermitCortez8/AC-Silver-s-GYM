import { discountedPrice } from '../../../domain/utils/money.js';
import { dayLabel } from '../../../domain/utils/scheduleEnrollment.js';
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useServiceImages } from '../../config/serviceImages';
import { usePublicCatalog } from '../../../application/services/publicCatalog.js';
import { useAppResources } from '../../../application/services/appResources.js';

/** Carga el catálogo público y coordina la selección de planes y horarios. */
export const useLandingPage = () => {
  const serviceImages = useServiceImages();

  const { loadPublicSchedules, loadMembershipPlans, loadCurrentPromotions } = usePublicCatalog();

  const { landingImageUrl } = useAppResources();

  const heroBanner = landingImageUrl('hero-banner.png');

  const route = useRoute();
  const router = useRouter();
  const showRegistrationNotice = computed(() => String(route.query.registro || '') === 'inicializado');
  const registrationCode = computed(() => {
    const id = Number(route.query.solicitud || 0);
    return id > 0 ? `SGCLI${String(id).padStart(3, '0')}` : '';
  });

  const dismissRegistrationNotice = () => {
    const query = { ...route.query };
    delete query.registro;
    delete query.solicitud;
    router.replace({ path: '/', query });
  };

  watch(
    showRegistrationNotice,
    (visible) => {
      if (!visible) return;
      setTimeout(() => {
        if (showRegistrationNotice.value) dismissRegistrationNotice();
      }, 6000);
    },
    { immediate: true },
  );

  const selectedService = ref(null);
             
  const defaultSchedules = [
    { dia: 'Lunes',     hora: '06:00–07:00', servicio: 'Fitness',     entrenador: 'Diego Alejandro Castro Flores' },
    { dia: 'Lunes',     hora: '18:00–19:00', servicio: 'Musculación', entrenador: 'Andrea Milagros Torres Paredes' },
    { dia: 'Lunes',     hora: '20:00–21:00', servicio: 'Baile',       entrenador: 'Valeria Nicole Mendoza Rojas' },
    { dia: 'Martes',    hora: '06:00–07:00', servicio: 'Musculación', entrenador: 'Diego Alejandro Castro Flores' },
    { dia: 'Martes',    hora: '19:00–20:00', servicio: 'Cardio',      entrenador: 'Luis Fernando Quispe Huamán' },
    { dia: 'Miércoles', hora: '07:00–08:00', servicio: 'Fitness',     entrenador: 'Andrea Milagros Torres Paredes' },
    { dia: 'Miércoles', hora: '20:00–21:00', servicio: 'Baile',       entrenador: 'Valeria Nicole Mendoza Rojas' },
    { dia: 'Jueves',    hora: '06:00–07:00', servicio: 'Cardio',      entrenador: 'Luis Fernando Quispe Huamán' },
    { dia: 'Jueves',    hora: '19:00–20:00', servicio: 'Musculación', entrenador: 'Andrea Milagros Torres Paredes' },
    { dia: 'Viernes',   hora: '07:00–08:00', servicio: 'Cardio',      entrenador: 'Luis Fernando Quispe Huamán' },
    { dia: 'Viernes',   hora: '18:00–19:00', servicio: 'Fitness',     entrenador: 'Carlos Eduardo Ramírez Salazar' },
    { dia: 'Viernes',   hora: '20:00–21:00', servicio: 'Baile',       entrenador: 'Valeria Nicole Mendoza Rojas' },
    { dia: 'Sábado',    hora: '09:00–10:00', servicio: 'Fitness',     entrenador: 'Diego Alejandro Castro Flores' },
    { dia: 'Sábado',    hora: '10:00–11:00', servicio: 'Musculación', entrenador: 'Carlos Eduardo Ramírez Salazar' },
    { dia: 'Sábado',    hora: '11:00–12:00', servicio: 'Baile',       entrenador: 'Andrea Milagros Torres Paredes' },
    { dia: 'Domingo',   hora: '09:00–10:00', servicio: 'Cardio',      entrenador: 'Diego Alejandro Castro Flores' },
  ];

  const backendSchedules = ref([]);

  const DAY_ORDER = {
    lunes: 1,
    martes: 2,
    miercoles: 3,
    jueves: 4,
    viernes: 5,
    sabado: 6,
    domingo: 7,
  };

  // Match card title (e.g. "Musculacion") to schedule servicio (e.g. "Musculación")
  /**
   * Normaliza el valor recibido.
   */
  const normalizeService = (str) =>
    String(str || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

  const capitalizeDay = (day) => {
    const str = String(day || '').trim();
    if (!str) return '';
    return dayLabel(str.charAt(0).toUpperCase() + str.slice(1).toLowerCase());
  };

  const normalizeScheduleItem = (item) => {
    const hora = item.hora || (item.hora_inicio && item.hora_fin ? `${item.hora_inicio}–${item.hora_fin}` : item.hora_inicio || '');
    const dia = capitalizeDay(item.dia);
    const entrenador = item.entrenador || item.rutina_nombre || 'Instructor Silver Gym';
    return {
      ...item,
      dia,
      hora,
      entrenador,
      servicio: item.servicio || '',
    };
  };

  const schedules = computed(() => {
    const source = backendSchedules.value.length ? backendSchedules.value : defaultSchedules;
    return source
      .map(normalizeScheduleItem)
      .sort((a, b) => {
        const dayA = DAY_ORDER[normalizeService(a.dia)] || 99;
        const dayB = DAY_ORDER[normalizeService(b.dia)] || 99;
        if (dayA !== dayB) return dayA - dayB;
        return String(a.hora || '').localeCompare(String(b.hora || ''));
      });
  });

  const filteredSchedules = computed(() =>
    selectedService.value
      ? schedules.value.filter(
          (s) => normalizeService(s.servicio) === normalizeService(selectedService.value),
        )
      : [],
  );

  /**
   * Consulta los horarios del servidor.
   */
  const loadSchedules = async () => {
    try {
      const list = await loadPublicSchedules();
      backendSchedules.value = Array.isArray(list) ? list : [];
    } catch {
      backendSchedules.value = [];
    }
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const toggleService = (title) => {
    selectedService.value = selectedService.value === title ? null : title;
  };

  const landingImages = serviceImages;

  /**
   * Gestiona esta acción de la vista.
   */
  const handleImageError = (event) => {
    event.currentTarget.style.display = 'none';
  };

  const gymAddress = 'Jirón Vista Alegre 606, Lima 15056';
  const mapEmbedUrl = `https://www.google.com/maps?q=${encodeURIComponent(gymAddress)}&output=embed`;
  const backendPlans = ref([]);
  const activePromotions = ref([]);
  const defaultPlans = [
    { id_pm: 1, nombre_plan: 'MENSUAL', duracion: '30 días', precio: 79, descripcion: 'Acceso completo por 30 días para entrenar con flexibilidad.', activo: true },
    { id_pm: 2, nombre_plan: '3 MESES', duracion: '90 días', precio: 199, descripcion: 'Plan trimestral para sostener progreso y ahorrar frente al pago mensual.', activo: true },
    { id_pm: 3, nombre_plan: 'ANUAL', duracion: '365 días', precio: 699, descripcion: 'Membresía anual para clientes constantes con mejor precio acumulado.', activo: true },
  ];

  /**
   * Normaliza el valor recibido.
   */
  const normalizePlanName = (value) => String(value || '').trim().toUpperCase();
  /**
   * Formatea el valor para mostrarlo.
   */
  const formatPlanLabel = (value) =>
    normalizePlanName(value)
      .toLowerCase()
      .replace(/\b\w/g, (letter) => letter.toUpperCase());

  const plans = computed(() =>
    (backendPlans.value.length ? backendPlans.value : defaultPlans)
      .filter((plan) => plan.activo ?? plan.active ?? true)
      .map((plan) => {
        const name = normalizePlanName(plan.nombre_plan || plan.name);
        const originalPrice = Number(plan.precio ?? plan.price ?? 0);
        const idPm = Number(plan.id_pm || 0);

        const promo = activePromotions.value.find((p) => {
          const applicable = p.planes_aplicables || [];
          return !applicable.length || (idPm && applicable.includes(idPm));
        });

        let finalPrice = originalPrice;
        let promoBadge = null;
        let promoName = null;

        if (promo) {
          promoName = promo.nombre;
          const valor = Number(promo.valor_descuento || 0);
          const icon = promo.icono_etiqueta || '🏷️';
          const tagText = promo.palabra_clave ? promo.palabra_clave : (promo.nombre || '');
          if (promo.tipo_descuento === 'monto') {
            finalPrice = discountedPrice(originalPrice, valor, 'fixed');
            promoBadge = `${icon} -S/${valor} ${tagText}`.trim();
          } else {
            finalPrice = discountedPrice(originalPrice, valor);
            promoBadge = `${icon} -${valor}% ${tagText}`.trim();
          }
        }

        return {
          id: name,
          id_pm: idPm,
          label: formatPlanLabel(name),
          price: finalPrice,
          originalPrice: promo ? originalPrice : null,
          hasPromo: Boolean(promo),
          promoBadge,
          promoName,
          description: plan.duracion || plan.description || 'Plan disponible para registro.',
        };
      })
      .filter((plan) => plan.id),
  );

  /**
   * Consulta los datos del servidor.
   */
  const loadPlans = async () => {
    try {
      const list = await loadMembershipPlans();
      backendPlans.value = Array.isArray(list) ? list : [];
    } catch {
      backendPlans.value = defaultPlans;
    }
  };

  const loadPromotions = async () => {
    try {
      const list = await loadCurrentPromotions();
      activePromotions.value = Array.isArray(list) ? list : [];
    } catch {
      activePromotions.value = [];
    }
  };

  const stats = [
    { label: 'Horario', value: 'Lun a sab' },
    { label: 'Servicios', value: '4 areas' },
    { label: 'Plataforma', value: 'Digital' },
  ];

  const services = [
    { tag: '01', title: 'Fitness', description: 'Entrenamiento general para mantenerte activo y construir hábitos saludables.', image: landingImages.fitness, imageClass: 'object-cover object-center' },
    { tag: '02', title: 'Musculación', description: 'Trabajo de fuerza con horarios definidos y control de cupos.', image: landingImages.musculacion, imageClass: 'object-cover object-center' },
    { tag: '03', title: 'Cardio', description: 'Bloques de entrenamiento para resistencia, energia y salud.', image: landingImages.cardio, imageClass: 'object-cover object-center' },
    { tag: '04', title: 'Baile', description: 'Clases grupales dinámicas para entrenar con movimiento y motivación.', image: landingImages.baile, imageClass: 'object-cover object-[40%_center]' },
  ];

  onMounted(() => {
    loadPlans();
    loadPromotions();
    loadSchedules();
  });

  return {
    serviceImages, loadPublicSchedules, loadMembershipPlans, loadCurrentPromotions, landingImageUrl,
    heroBanner, route, router, showRegistrationNotice, registrationCode,
    dismissRegistrationNotice, selectedService, defaultSchedules, backendSchedules, DAY_ORDER,
    normalizeService, capitalizeDay, normalizeScheduleItem, schedules, filteredSchedules,
    loadSchedules, toggleService, landingImages, handleImageError, gymAddress,
    mapEmbedUrl, backendPlans, activePromotions, defaultPlans, normalizePlanName,
    formatPlanLabel, plans, loadPlans, loadPromotions, stats,
    services,
  };
};
