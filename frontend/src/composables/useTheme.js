import { computed, ref } from 'vue';

const THEME_STORAGE_KEY = 'ac-silver-theme';
const theme = ref('dark');
let initialized = false;

const applyTheme = (value) => {
  if (typeof document === 'undefined') return;
  document.documentElement.dataset.theme = value;
  document.documentElement.style.colorScheme = value;
};

export const initializeTheme = () => {
  if (initialized || typeof window === 'undefined') return;

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  const preferredTheme = window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  theme.value = storedTheme === 'light' || storedTheme === 'dark' ? storedTheme : preferredTheme;
  applyTheme(theme.value);
  initialized = true;
};

export const useTheme = () => {
  initializeTheme();

  const setTheme = (value) => {
    theme.value = value === 'light' ? 'light' : 'dark';
    applyTheme(theme.value);
    window.localStorage.setItem(THEME_STORAGE_KEY, theme.value);
  };

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
