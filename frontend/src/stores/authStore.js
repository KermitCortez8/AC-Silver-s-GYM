import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import {
  saveAuthSession,
  getAuthSession,
  clearAuthStorage,
  formatUserData,
  isValidUser,
} from '../utils/authUtils';

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null);
  const token = ref(null);
  const isLoading = ref(false);
  const userRole = ref(null);
  const isSignout = ref(false);
  const isInitialized = ref(false);

  // Getters
  const isAuthenticated = computed(() => !!user.value);
  const isAdmin = computed(() => userRole.value === 'admin');

  // Actions
  const initializeAuth = async () => {
    try {
      isLoading.value = true;
      const { user: storedUser, token: storedToken } = getAuthSession();

      if (storedUser && isValidUser(storedUser)) {
        user.value = storedUser;
        token.value = storedToken;
        userRole.value = storedUser.role || 'user';
        isSignout.value = false;
      } else {
        user.value = null;
        token.value = null;
        userRole.value = null;
        isSignout.value = true;
      }
    } catch (error) {
      console.error('Error al inicializar autenticación:', error);
      isSignout.value = true;
    } finally {
      isLoading.value = false;
      isInitialized.value = true;
    }
  };

  const signIn = async (idToken, userData) => {
    try {
      isLoading.value = true;

      if (!idToken || !userData || !userData.email) {
        throw new Error('Datos de autenticación incompletos');
      }

      const formattedUser = formatUserData(userData);
      if (!isValidUser(formattedUser)) {
        throw new Error('Datos de usuario inválidos');
      }

      user.value = formattedUser;
      token.value = idToken;
      userRole.value = userData.role || formattedUser.role || 'user';
      isSignout.value = false;

      // Guardar sesión
      saveAuthSession(formattedUser, idToken, userData.expiresIn);
    } catch (error) {
      console.error('Error en signIn:', error);
      isSignout.value = true;
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const signUp = async (idToken, userData) => {
    try {
      isLoading.value = true;

      if (!idToken || !userData || !userData.email) {
        throw new Error('Datos de registro incompletos');
      }

      const formattedUser = formatUserData(userData);
      if (!isValidUser(formattedUser)) {
        throw new Error('Datos de usuario inválidos');
      }

      user.value = formattedUser;
      token.value = idToken;
      userRole.value = formattedUser.role || 'user';
      isSignout.value = false;

      saveAuthSession(formattedUser, idToken, userData.expiresIn);
    } catch (error) {
      console.error('Error en signUp:', error);
      isSignout.value = true;
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const signOut = async () => {
    try {
      isLoading.value = true;
      clearAuthStorage();
      user.value = null;
      token.value = null;
      userRole.value = null;
      isSignout.value = true;
    } catch (error) {
      console.error('Error en signOut:', error);
    } finally {
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
    // Getters
    isAuthenticated,
    isAdmin,
    // Actions
    initializeAuth,
    signIn,
    signUp,
    signOut,
  };
});
