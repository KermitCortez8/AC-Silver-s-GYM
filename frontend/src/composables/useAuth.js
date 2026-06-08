import { storeToRefs } from 'pinia';
import { useAuthStore } from '../stores/authStore';

/**
 * Composable para usar autenticación en componentes
 * Similar a: const { user, signIn, signOut } = useContext(AuthContext)
 */
export const useAuth = () => {
  const authStore = useAuthStore();
  const {
    user,
    token,
    isLoading,
    userRole,
    isSignout,
    isInitialized,
    isAuthenticated,
    isAdmin,
  } = storeToRefs(authStore);

  return {
    user,
    token,
    isLoading,
    userRole,
    isSignout,
    isInitialized,
    isAuthenticated,
    isAdmin,
    initializeAuth: authStore.initializeAuth,
    signIn: authStore.signIn,
    signUp: authStore.signUp,
    signOut: authStore.signOut,
  };
};
