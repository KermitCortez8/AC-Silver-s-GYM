import { getApplicationServices } from '../ports/services.js';

/** Favoritos de Tienda del cliente, guardados en este navegador. */
export const useStoreFavoritesStorage = () => {
  const { preferences } = getApplicationServices();
  return {
    readFavorites: owner => preferences.readFavoriteProducts?.(owner) || [],
    writeFavorites: (owner, ids) => preferences.writeFavoriteProducts?.(owner, ids),
  };
};
