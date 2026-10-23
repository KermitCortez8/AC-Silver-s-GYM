import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import { useSessionStore } from './sessionStore.js';
import {
  saveAuthSession,
  getAuthSession,
  clearAuthStorage,
  disableGoogleAutoSelect,
} from '../services/authentication.js';
import { formatUserData, isValidUser } from '../../domain/utils/authRules.js';
import { APP_CONFIG } from '../services/appResources.js';
import { apiGet } from '../services/backendGateway.js';
import { createSessionValidator } from '../services/sessionValidation.js';

/**
 * Normaliza el valor recibido.
 */
const normalizeStoredUser = (userData) => {
  if (!userData) {
    return null;
  }

  if (userData.email && userData.name && (userData.id || userData.id_usuario)) {
    return {
      ...userData,
      id: userData.id_usuario || userData.id,
      id_usuario: userData.id_usuario || userData.id,
      role: userData.role || 'user',
      telefono: userData.telefono || '',
    };
  }

  return formatUserData(userData);
};

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null);
  const token = ref(null);
  const isLoading = ref(false);
  const userRole = ref(null);
  const isSignout = ref(false);
  const isInitialized = ref(false);
  const sessionErrorCode = ref('');
  const sessionRevision = ref(0);
  const session = useSessionStore();
  watch(() => [token.value, userRole.value, sessionRevision.value], () => session.invalidate(), { flush: 'sync' });
  const sessionValidator = createSessionValidator(async (storedToken) => {
    const sessionUser = normalizeStoredUser(
      await apiGet('/auth/me', storedToken),
    );
    if (!sessionUser || !isValidUser(sessionUser))
      throw new Error('Sesión inválida');
    return sessionUser;
  });

  // Getters
  const isAuthenticated = computed(() => !!user.value);
  const isAdmin = computed(() => ['admin', 'staff'].includes(userRole.value));
  const isTrainer = computed(() => userRole.value === 'trainer');
  const dashboardPath = computed(() => {
    if (isAdmin.value) return '/admin/dashboard';
    if (isTrainer.value) return '/trainer/dashboard';
    return '/user/dashboard';
  });

  // Actions
  /**
   * Gestiona esta acción de la vista.
   */
  const initializeAuth = async ({ force = false } = {}) => {
    const revision = sessionRevision.value;
    try {
      isLoading.value = true;
      const { token: storedToken } = getAuthSession();

      if (storedToken && APP_CONFIG.authApiBaseUrl) {
        try {
          const sessionUser = await sessionValidator.validate(storedToken, {
            force,
          });
          // Una respuesta anterior no debe restaurar una sesión cerrada o sustituida.
          if (revision !== sessionRevision.value) return;
          if (getAuthSession().token !== storedToken) return initializeAuth();

          if (sessionUser && isValidUser(sessionUser)) {
            user.value = sessionUser;
            token.value = storedToken;
            userRole.value = sessionUser.role || 'user';
            isSignout.value = false;
            sessionErrorCode.value = '';
            saveAuthSession(sessionUser, storedToken);
            return;
          }
        } catch (error) {
          if (revision !== sessionRevision.value) return;
          if (getAuthSession().token !== storedToken) return initializeAuth();
          sessionErrorCode.value = error.code || '';
          clearAuthStorage();
        }
      }

      clearAuthStorage();
      sessionValidator.clear();
      user.value = null;
      token.value = null;
      userRole.value = null;
      isSignout.value = true;
    } catch (error) {
      console.error('Error al inicializar autenticación:', error);
      clearAuthStorage();
      sessionValidator.clear();
      user.value = null;
      token.value = null;
      userRole.value = null;
      isSignout.value = true;
    } finally {
      isLoading.value = false;
      isInitialized.value = true;
    }
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const establishSession = (idToken, userData) => {
    if (!idToken || !userData?.email) throw new Error('Datos de autenticación incompletos');
    const formattedUser = normalizeStoredUser(userData);
    if (!isValidUser(formattedUser)) throw new Error('Datos de usuario inválidos');
    sessionRevision.value += 1;
    sessionErrorCode.value = '';
    sessionValidator.clear();
    user.value = formattedUser;
    token.value = idToken;
    userRole.value = formattedUser.role || 'user';
    isSignout.value = false;
    saveAuthSession(formattedUser, idToken, userData.expiresIn);
  };

  const signIn = async (idToken, userData) => {
    isLoading.value = true;
    try {
      establishSession(idToken, userData);
    } catch (error) {
      isSignout.value = true;
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  // Conserva el contrato público de registro con la misma política de sesión.
  const signUp = signIn;

  /**
   * Gestiona esta acción de la vista.
   */
  const signOut = async () => {
    sessionRevision.value += 1;
    sessionErrorCode.value = '';
    sessionValidator.clear();
    try {
      isLoading.value = true;
      clearAuthStorage();
      disableGoogleAutoSelect();
    } catch (error) {
      console.error('Error en signOut:', error);
    } finally {
      user.value = null;
      token.value = null;
      userRole.value = null;
      isSignout.value = true;
      isLoading.value = false;
    }
  };

  return {
    // State
    user,
    token,
    isLoading,
    userRole,
    isSignout,
    isInitialized,
    sessionErrorCode,
    sessionRevision,
    // Getters
    isAuthenticated,
    isAdmin,
    isTrainer,
    dashboardPath,
    // Actions
    initializeAuth,
    signIn,
    signUp,
    signOut,
  };
});
