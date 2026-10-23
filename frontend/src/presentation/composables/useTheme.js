import { computed, ref } from 'vue';
import { readThemePreference, writeThemePreference, preferredTheme } from '../../application/services/themePreferences.js';

const theme = ref('dark');
let initialized = false;

/**
 * Gestiona esta acción de la vista.
 */
const applyTheme = (value) => {
  if (typeof document === 'undefined') return;
  document.documentElement.dataset.theme = value;
  document.documentElement.style.colorScheme = value;
};

export const initializeTheme = () => {
  if (initialized || typeof window === 'undefined') return;

  const storedTheme = readThemePreference();
  theme.value = storedTheme === 'light' || storedTheme === 'dark' ? storedTheme : preferredTheme();
  applyTheme(theme.value);
  initialized = true;
};

export const useTheme = () => {
  initializeTheme();

  /**
   * Gestiona esta acción de la vista.
   */
  const setTheme = (value) => {
    theme.value = value === 'light' ? 'light' : 'dark';
    applyTheme(theme.value);
    writeThemePreference(theme.value);
  };

  /**
   * Gestiona esta acción de la vista.
   */
  const toggleTheme = () => {
    setTheme(theme.value === 'dark' ? 'light' : 'dark');
  };

  return {
    theme,
    isDarkTheme: computed(() => theme.value === 'dark'),
    setTheme,
    toggleTheme,
  };
};
