const THEME_STORAGE_KEY = 'ac-silver-theme';

export const readThemePreference = () => window.localStorage.getItem(THEME_STORAGE_KEY);
export const writeThemePreference = (theme) => window.localStorage.setItem(THEME_STORAGE_KEY, theme);
export const preferredTheme = () => window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
