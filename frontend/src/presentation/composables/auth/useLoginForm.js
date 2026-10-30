import { emailError } from '../../../domain/utils/formValidation.js';
import { nextTick, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '../../../application/composables/useAuth';
import { useAppResources } from '../../../application/services/appResources.js';
import { useAuthentication } from '../../../application/services/authentication.js';

/** Gestiona el acceso con contraseña y Google, sus validaciones y estados. */
export const useLoginForm = () => {
  const { GOOGLE_CONFIG, landingImageUrl } = useAppResources();

  const { authenticateWithGoogleCredential,
    authenticateWithPassword,
    loadGoogleIdentityScript, } = useAuthentication();

  const router = useRouter();
  const route = useRoute();

  const {
    signIn,
    initializeAuth,
    isAuthenticated,
    dashboardPath,
  } = useAuth();

  /* -------------------------------------------------------------------------- */
  /* ESTADOS                                                                    */
  /* -------------------------------------------------------------------------- */

  const googleError = ref(route.query.reason === 'membership_expired'
    ? 'Tu membresía ha vencido y tu acceso está bloqueado. Contacta al administrador para renovar.'
    : '');

  const linkCredential = ref('');

  const linkPassword = ref('');

  const processing = ref(false);

  const googleReady = ref(false);

  const googleButtonRef = ref(null);

  const passwordForm = reactive({
    correo: '',
    password: '',
  });

  /* -------------------------------------------------------------------------- */
  /* IMAGEN                                                                     */
  /* -------------------------------------------------------------------------- */

  const panelImage = landingImageUrl('fitness.jpg');

  const handlePanelImageError = (event) => {
    event.currentTarget.style.display = 'none';
  };

  /* -------------------------------------------------------------------------- */
  /* NAVEGACIÓN SEGÚN ROL                                                       */
  /* -------------------------------------------------------------------------- */

  const navigateByRole = (role) => {
    if (role === 'trainer') {
      router.replace('/trainer/dashboard');
      return;
    }

    if (['admin', 'staff'].includes(role)) {
      router.replace('/admin/dashboard');
      return;
    }

    router.replace('/user/dashboard');
  };

  /* -------------------------------------------------------------------------- */
  /* CANCELAR VINCULACIÓN GOOGLE                                                */
  /* -------------------------------------------------------------------------- */

  const cancelLink = () => {
    linkCredential.value = '';
    linkPassword.value = '';
    googleError.value = '';
  };

  /* -------------------------------------------------------------------------- */
  /* LOGIN / VINCULACIÓN CON GOOGLE                                             */
  /* -------------------------------------------------------------------------- */

  const completeLogin = async (credential, password = '') => {
    if (processing.value) {
      return;
    }

    if (!credential) {
      googleError.value =
        'No se recibió una credencial válida de Google.';
      return;
    }

    processing.value = true;
    googleError.value = '';

    try {
      const result = await authenticateWithGoogleCredential(
        credential,
        password
      );

      await signIn(result.token, {
        ...result.user,

        expiresIn: result.expiresIn,

        role: result.user.role,

        authSource: result.source,
      });

      cancelLink();

      navigateByRole(result.user.role);
    } catch (error) {
      /*
       * Si el backend indica que la cuenta Google tiene que
       * vincularse con la cuenta actual del gimnasio,
       * guardamos temporalmente la credential.
       */
      if (error?.code === 'google_link_required') {
        linkCredential.value = credential;
      } else {
        linkCredential.value = '';
      }

      linkPassword.value = '';

      googleError.value =
        error?.message ||
        'No se pudo completar el inicio de sesión con Google.';
    } finally {
      processing.value = false;
    }
  };

  /* -------------------------------------------------------------------------- */
  /* LOGIN CORREO / PASSWORD                                                    */
  /* -------------------------------------------------------------------------- */

  const handlePasswordLogin = async () => {
    if (processing.value) {
      return;
    }

    processing.value = true;
    googleError.value = '';

    try {
      const invalid = emailError(passwordForm.correo, { account: false });
      if (invalid) throw new Error(invalid);
      if (!passwordForm.password) throw new Error('La contraseña es obligatoria.');
      const result = await authenticateWithPassword({
        correo: passwordForm.correo.trim(),
        password: passwordForm.password,
      });

      await signIn(result.token, {
        ...result.user,

        expiresIn: result.expiresIn,

        role: result.user.role,

        authSource: result.source,
      });

      navigateByRole(result.user.role);
    } catch (error) {
      googleError.value =
        error?.message ||
        'Correo o contraseña incorrectos.';
    } finally {
      processing.value = false;
    }
  };

  /* -------------------------------------------------------------------------- */
  /* INICIALIZAR GOOGLE IDENTITY SERVICES                                       */
  /* -------------------------------------------------------------------------- */

  const initializeGoogleSignIn = async () => {
    try {
      /*
       * Conservamos el sistema que estaba implementando
       * la rama develop.
       */
      await loadGoogleIdentityScript();

      const googleAccounts = window.google?.accounts?.id;

      if (!googleAccounts) {
        throw new Error(
          'Google Identity Services no pudo inicializarse.'
        );
      }

      const clientId = GOOGLE_CONFIG.webClientId;

      if (!clientId) {
        throw new Error(
          'No se encontró el Client ID de Google.'
        );
      }

      /*
       * Primero hacemos visible el contenedor.
       */
      googleReady.value = true;

      /*
       * Esperamos a que Vue lo coloque en el DOM.
       */
      await nextTick();

      if (!googleButtonRef.value) {
        throw new Error(
          'No se pudo crear el contenedor del botón de Google.'
        );
      }

      /*
       * Configurar Google Identity.
       */
      googleAccounts.initialize({
        client_id: clientId,

        callback: (response) => {
          if (!response?.credential) {
            googleError.value =
              'Google no devolvió una credencial válida.';
            return;
          }

          completeLogin(response.credential);
        },

        auto_select: false,

        cancel_on_tap_outside: true,
      });

      /*
       * Evitar que se duplique el botón si por alguna razón
       * la función vuelve a ejecutarse.
       */
      googleButtonRef.value.innerHTML = '';

      /*
       * Renderizar botón Google.
       */
      googleAccounts.renderButton(
        googleButtonRef.value,
        {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          shape: 'pill',
          logo_alignment: 'left',
          width: 320,
        }
      );
    } catch (error) {
      console.error(
        'Error inicializando Google Sign-In:',
        error
      );

      googleReady.value = false;

      googleError.value =
        error?.message ||
        'No se pudo cargar el inicio de sesión con Google.';
    }
  };

  /* -------------------------------------------------------------------------- */
  /* MOUNT                                                                      */
  /* -------------------------------------------------------------------------- */

  onMounted(async () => {
    /*
     * Primero verificar si ya existe una sesión.
     */
    await initializeAuth();

    if (isAuthenticated.value) {
      router.replace(dashboardPath.value);
      return;
    }

    /*
     * Solo cargar Google si realmente necesitamos mostrar
     * la pantalla de login.
     */
    await initializeGoogleSignIn();
  });

  return {
    GOOGLE_CONFIG, landingImageUrl, authenticateWithGoogleCredential, authenticateWithPassword, loadGoogleIdentityScript,
    router, route, signIn, initializeAuth, isAuthenticated,
    dashboardPath, googleError, linkCredential, linkPassword, processing,
    googleReady, googleButtonRef, passwordForm, panelImage, handlePanelImageError,
    navigateByRole, cancelLink, completeLogin, handlePasswordLogin, initializeGoogleSignIn,
  };
};
