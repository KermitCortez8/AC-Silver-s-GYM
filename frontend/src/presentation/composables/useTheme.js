import { computed, ref } from 'vue';
import { getActivePinia } from 'pinia';
import { useThemePreferences } from '../../application/services/themePreferences.js';

const instances = new WeakMap();
const themeState = () => {
  const pinia = getActivePinia();
  if (!instances.has(pinia)) instances.set(pinia, { theme: ref('dark'), initialized: false, preferences: useThemePreferences() });
  return instances.get(pinia);
};

/**
 * Gestiona esta acción de la vista.
 */
const applyTheme = (value) => {
  if (typeof document === 'undefined') return;
  document.documentElement.dataset.theme = value;
  document.documentElement.style.colorScheme = value;
};

export const initializeTheme = () => {
  const state = themeState();
  const { theme, preferences: { readThemePreference, preferredTheme } } = state;
  if (state.initialized || typeof window === 'undefined') return;

  const storedTheme = readThemePreference();
  theme.value = storedTheme === 'light' || storedTheme === 'dark' ? storedTheme : preferredTheme();
  applyTheme(theme.value);
  state.initialized = true;
};

export const useTheme = () => {
  initializeTheme();
  const { theme, preferences: { writeThemePreference } } = themeState();

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
