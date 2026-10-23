import { getApplicationServices } from '../ports/services.js';

export const listStoreImages = (...args) => getApplicationServices().images.listStoreImages(...args);
export const uploadStoreImage = (...args) => getApplicationServices().images.uploadStoreImage(...args);
export { storeImageUrl } from './appResources.js';
