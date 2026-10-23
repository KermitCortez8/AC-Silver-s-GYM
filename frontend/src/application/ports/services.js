/** Dependencias de la aplicación. El punto de entrada conecta los adaptadores. */
let services;

export const configureApplicationServices = (adapters) => {
  for (const name of ['http', 'auth', 'session', 'attendance', 'images', 'config', 'storage', 'preferences', 'repositories']) {
    if (!adapters[name]) throw new Error(`Falta el adaptador de ${name}`);
  }
  services = adapters;
};

export const getApplicationServices = () => {
  if (!services) throw new Error('Inicializa los adaptadores de la aplicación antes de usar sus servicios.');
  return services;
};
