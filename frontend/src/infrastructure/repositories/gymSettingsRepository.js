/** Devuelve datos de configuración sin exponer respuestas HTTP a la aplicación. */
export const createGymSettingsRepository = ({ apiGet, apiPost }) => ({
  load: (token) => apiGet('/gym/configuracion', token),
  save: (settings, token) => apiPost('/gym/configuracion', settings, token),
});
