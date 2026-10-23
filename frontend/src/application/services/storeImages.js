import { useAuthStore } from '../stores/authStore.js';
import { getApplicationServices } from '../ports/services.js';

export const listStoreImages = (...args) => getApplicationServices().images.listStoreImages(...args);
export const uploadStoreImage = (file) => getApplicationServices().images.uploadStoreImage(file, useAuthStore().token);
export { storeImageUrl } from './appResources.js';
