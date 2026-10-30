import { computed, ref, watch } from 'vue';
import { useStoreFavoritesStorage } from '../../../application/services/storeFavorites.js';

/**
 * Favoritos del cliente en Tienda. Se guardan por usuario en este navegador.
 */
export const useStoreFavorites = (ownerRef) => {
  const { readFavorites, writeFavorites } = useStoreFavoritesStorage();
  const ids = ref([]);
  const owner = computed(() => String(ownerRef.value || 'invitado'));

  watch(owner, (value) => { ids.value = readFavorites(value); }, { immediate: true });

  const isFavorite = (idProducto) => ids.value.includes(Number(idProducto));
  const toggleFavorite = (idProducto) => {
    const id = Number(idProducto);
    ids.value = isFavorite(id) ? ids.value.filter((value) => value !== id) : [...ids.value, id];
    writeFavorites(owner.value, ids.value);
  };

  return { favoriteIds: ids, isFavorite, toggleFavorite };
};
