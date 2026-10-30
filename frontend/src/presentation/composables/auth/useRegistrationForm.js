import { emailError, validateAccountForm } from '../../../domain/utils/formValidation.js';
import { useFormValidation } from '../useFormValidation.js';
import { discountedPrice } from '../../../domain/utils/money.js';
import { computed, onMounted, reactive, ref } from 'vue';
import { useClientMembershipCatalog } from '../clients/useClientMembershipCatalog.js';
import { normalizePlanName, promotionAvailableForPlan } from '../../../domain/utils/membershipCatalog.js';
import { useRoute } from 'vue-router';
import { useAuthentication } from '../../../application/services/authentication.js';
import { useGymStore } from '../../../application/stores/gymStore';

/** Coordina el registro y conserva el borrador y los errores del formulario. */
export const useRegistrationForm = () => {
  const { getVerifiedGoogleProfile } = useAuthentication();

  const { plans: backendPlans, promotions: activePromotions, catalogLoading, catalogReady, catalogError, loadCatalog } = useClientMembershipCatalog();

  /* -------------------------------------------------------------------------- */
  /* INSTANCIAS                                                                 */
  /* -------------------------------------------------------------------------- */

  const route = useRoute();

  const gymStore = useGymStore();

  /* -------------------------------------------------------------------------- */
  /* ESTADOS                                                                    */
  /* -------------------------------------------------------------------------- */

  const googleCredential = ref('');

  const googleProcessing = ref(false);

  const googleError = ref('');

  const feedback = ref('');

  const feedbackTone = ref('success');

  const isSubmitting = ref(false);

  const registeredClient = ref(null);
  const registeredPreregistration = ref(null);

  const formatPlanLabel = (value) =>
    normalizePlanName(value)
      .toLowerCase()
      .replace(/(^|\s)(\p{L})/gu, (_, space, letter) => space + letter.toUpperCase());


  /* -------------------------------------------------------------------------- */
  /* OPCIONES DE PLAN                                                           */
  /* -------------------------------------------------------------------------- */

  const planOptions = computed(() =>
    backendPlans.value
      .filter((plan) => plan.active)
      .map((plan) => {
        const name = normalizePlanName(plan.name);

        const duration = String(plan.duration || '').trim();

        const originalPrice = Number(plan.price ?? 0);
        const promo = activePromotions.value.find((p) => promotionAvailableForPlan(p, plan.id));

        let finalPrice = originalPrice;
        let promoTag = null;

        if (promo) {
          const valor = Number(promo.discountValue || 0);
          const icon = promo.icono_etiqueta || '🏷️';
          const tagWord = promo.palabra_clave || promo.name || '';
          if (promo.discountType === 'fixed') {
            finalPrice = discountedPrice(originalPrice, valor, 'fixed');
            promoTag = `${icon} -S/${valor} ${tagWord}`.trim();
          } else {
            finalPrice = discountedPrice(originalPrice, valor);
            promoTag = `${icon} -${valor}% ${tagWord}`.trim();
          }
        }

        const tags = [];
        if (promoTag) tags.push(promoTag);
        if (duration) tags.push(duration);

        return {
          id: name,

          label: formatPlanLabel(name),

          price: finalPrice,

          originalPrice: promo ? originalPrice : null,

          hasPromo: Boolean(promo),

          promoTag,

          detail: duration
            ? `Acceso por ${duration}.`
            : 'Plan disponible para registro.',

          tags,
        };
      })
      .filter((plan) => plan.id),
  );

  /* -------------------------------------------------------------------------- */
  /* FORMULARIO                                                                 */
  /* -------------------------------------------------------------------------- */

  const form = reactive({
    nombre: '',

    correo: '',

    telefono: '',

    dni: '',

    password: '',

    plan: normalizePlanName(route.query.plan),
  });

  const { fieldErrors, validateField, revalidateField, validateForm } = useFormValidation(form,
    value => validateAccountForm(value, { requirePhone: true, google: Boolean(googleCredential.value) }));

  const updateTelefono = (event) => {
    form.telefono = event.target.value;
    revalidateField('telefono');
  };

  /* -------------------------------------------------------------------------- */
  /* SINCRONIZAR PLAN SELECCIONADO                                              */
  /* -------------------------------------------------------------------------- */

  const syncSelectedPlan = () => {
    if (!planOptions.value.length) {
      form.plan = '';
      return;
    }

    const planExists = planOptions.value.some((plan) => plan.id === form.plan);

    if (!planExists) {
      form.plan = planOptions.value[0].id;
    }
  };

  /* -------------------------------------------------------------------------- */
  /* CARGAR PLANES                                                              */
  /* -------------------------------------------------------------------------- */

  const loadPlans = async () => {
    const loaded = await loadCatalog();
    if (loaded) syncSelectedPlan();
  };
  const loadPromotions = loadPlans;
  const canRegister = computed(() => catalogReady.value && !catalogLoading.value
    && planOptions.value.some(plan => plan.id === form.plan));

  /* -------------------------------------------------------------------------- */
  /* LIMPIAR CUENTA GOOGLE                                                      */
  /* -------------------------------------------------------------------------- */

  const clearGoogleAccount = () => {
    googleCredential.value = '';

    googleError.value = '';

    /*
     * El correo deja de estar bloqueado y el usuario
     * puede introducir una cuenta manualmente.
     */
    form.correo = '';

    form.password = '';
  };

  /* -------------------------------------------------------------------------- */
  /* SELECCIONAR CUENTA GOOGLE                                                  */
  /* -------------------------------------------------------------------------- */

  const selectGoogleAccount = async (credential) => {
    if (isSubmitting.value || googleProcessing.value) {
      return;
    }

    if (!credential) {
      googleError.value = 'Google no devolvió una credencial válida.';

      return;
    }

    googleProcessing.value = true;

    googleError.value = '';

    /*
     * Eliminamos cualquier Google Credential anterior
     * antes de verificar la nueva.
     */
    googleCredential.value = '';

    try {
      const profile = await getVerifiedGoogleProfile(credential);

      if (!profile?.email) {
        throw new Error('Google no devolvió un correo válido.');
      }

      const invalidEmail = emailError(profile.email);
      if (invalidEmail) throw new Error(invalidEmail);
      form.nombre = profile.name || form.nombre;

      form.correo = profile.email;

      /*
       * Cuando esto tiene valor:
       * - correo queda readonly
       * - contraseña desaparece
       * - credential se manda al backend.
       */
      googleCredential.value = credential;

      /*
       * No necesitamos contraseña local cuando
       * el registro utiliza Google.
       */
      form.password = '';
    } catch (error) {
      googleCredential.value = '';

      googleError.value =
        error?.message || 'No se pudo verificar tu cuenta de Google';
    } finally {
      googleProcessing.value = false;
    }
  };

  /* -------------------------------------------------------------------------- */
  /* ENVIAR REGISTRO                                                           */
  /* -------------------------------------------------------------------------- */

  const submitRegistration = async () => {
    if (isSubmitting.value || googleProcessing.value) {
      return;
    }

    isSubmitting.value = true;

    feedback.value = '';

    registeredClient.value = null;
    registeredPreregistration.value = null;

    try {
      if (!validateForm()) throw new Error(Object.values(fieldErrors)[0]);
      if (!canRegister.value) {
        throw new Error(catalogError.value || 'Selecciona un plan activo del catálogo para registrar al cliente.');
      }

      /*
       * Conservamos ambas formas de registro:
       *
       * Registro tradicional:
       * google_credential = ''
       *
       * Registro Google:
       * google_credential = credencial Google
       */
      const result = await gymStore.registerPublicClient({
        ...form,
        correo: form.correo.trim().toLowerCase(),
        google_credential: googleCredential.value,
      });

      const { client, payment } = result;

      registeredClient.value = client;
      registeredPreregistration.value = result.preregistration || null;

      /*
       * Verificar que Stripe haya generado
       * correctamente el Checkout.
       */
      if (!payment?.checkout_url) {
        throw new Error(
          payment?.message ||
            'Stripe no está configurado. Contacta al administrador.',
        );
      }

      feedbackTone.value = 'success';

      feedback.value =
        'Solicitud temporal guardada. Abriendo Stripe. Tu cuenta se creará al confirmar el pago y requerirá activación administrativa.';

      /*
       * Redirección a Stripe Checkout.
       */
      window.location.assign(payment.checkout_url);
    } catch (error) {
      feedbackTone.value = 'error';
      Object.assign(fieldErrors, error?.fieldErrors || {});

      feedback.value =
        error instanceof Error
          ? error.message
          : 'No se pudo completar el registro.';
    } finally {
      isSubmitting.value = false;
    }
  };


  /* -------------------------------------------------------------------------- */
  /* INICIALIZACIÓN                                                             */
  /* -------------------------------------------------------------------------- */

  onMounted(() => {
    void loadPlans();
  });

  return {
    getVerifiedGoogleProfile, route, catalogLoading, catalogReady, catalogError, canRegister,
    gymStore, googleCredential, googleProcessing, googleError, feedback,
    feedbackTone, isSubmitting, registeredClient, registeredPreregistration, backendPlans,
    normalizePlanName, formatPlanLabel, activePromotions, planOptions, form,
    fieldErrors, validateField, revalidateField, validateForm, updateTelefono,
    syncSelectedPlan, loadPlans, clearGoogleAccount, selectGoogleAccount, submitRegistration,
    loadPromotions,
  };
};
