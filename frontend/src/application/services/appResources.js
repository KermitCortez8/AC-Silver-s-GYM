import { getApplicationServices } from '../ports/services.js';

// Lectura diferida: importar una vista no fija la configuración del entorno.
export const APP_CONFIG = new Proxy({}, {
  get: (_, name) => getApplicationServices().config.app[name],
});
export const GOOGLE_CONFIG = new Proxy({}, {
  get: (_, name) => getApplicationServices().config.google[name],
});
export const landingImageUrl = (...args) => getApplicationServices().storage.landingImageUrl(...args);
export const storeImageUrl = (...args) => getApplicationServices().storage.storeImageUrl(...args);
