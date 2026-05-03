import { useAuthStore } from '../stores/authStore';

/**
 * Composable para usar autenticación en componentes
 * Similar a: const { user, signIn, signOut } = useContext(AuthContext)
 */
export const useAuth = () => {
  const authStore = useAuthStore();

  return {
    user: authStore.user,
    token: authStore.token,
    isLoading: authStore.isLoading,
    userRole: authStore.userRole,
    isSignout: authStore.isSignout,
    isInitialized: authStore.isInitialized,
    isAuthenticated: authStore.isAuthenticated,
    isAdmin: authStore.isAdmin,
    initializeAuth: authStore.initializeAuth,
    signIn: authStore.signIn,
    signUp: authStore.signUp,
    signOut: authStore.signOut,
  };
};
