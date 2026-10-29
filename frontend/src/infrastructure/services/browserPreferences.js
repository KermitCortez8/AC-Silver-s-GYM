const THEME_STORAGE_KEY = 'ac-silver-theme';

export const readThemePreference = () => window.localStorage.getItem(THEME_STORAGE_KEY);
export const writeThemePreference = (theme) => window.localStorage.setItem(THEME_STORAGE_KEY, theme);
export const preferredTheme = () => window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';

// Favoritos de Tienda por usuario. Si el navegador bloquea el almacenamiento, se usa una lista vacia.
const FAVORITES_PREFIX = 'ac-silver-favoritos:';
export const readFavoriteProducts = (owner) => {
  try {
    const ids = JSON.parse(window.localStorage.getItem(`${FAVORITES_PREFIX}${owner}`) || '[]');
    return Array.isArray(ids) ? ids.map(Number).filter(Number.isFinite) : [];
  } catch {
    return [];
  }
};
export const writeFavoriteProducts = (owner, ids) => {
  try {
    window.localStorage.setItem(`${FAVORITES_PREFIX}${owner}`, JSON.stringify(ids));
  } catch {
    // Sin almacenamiento los favoritos duran solo mientras la pagina esta abierta.
  }
};
