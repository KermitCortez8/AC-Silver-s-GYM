import { getApplicationServices } from "../ports/services.js";

/** Captura los recursos de la aplicación durante setup; no depende de lecturas globales posteriores. */
export const useAppResources = () => {
  const { config, storage } = getApplicationServices();
  return {
    APP_CONFIG: config.app,
    GOOGLE_CONFIG: config.google,
    landingImageUrl: (...args) => storage.landingImageUrl(...args),
    storeImageUrl: (...args) => storage.storeImageUrl(...args),
  };
};
