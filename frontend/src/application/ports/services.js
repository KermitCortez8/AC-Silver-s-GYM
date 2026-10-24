/** Cada instancia de Pinia es propietaria de sus adaptadores. */
import { getActivePinia } from "pinia";

const instances = new WeakMap();

export const configureApplicationServices = (
  adapters,
  pinia = getActivePinia(),
) => {
  if (!pinia)
    throw new Error(
      "Se necesita una instancia de Pinia para instalar los adaptadores.",
    );
  if (instances.has(pinia))
    throw new Error("Los adaptadores de esta aplicación ya están instalados.");
  for (const name of [
    "http",
    "auth",
    "session",
    "attendance",
    "images",
    "config",
    "storage",
    "preferences",
    "repositories",
  ]) {
    if (!adapters[name]) throw new Error(`Falta el adaptador de ${name}`);
  }
  const services = Object.freeze({
    ...adapters,
    pinia,
    config: Object.freeze({
      app: Object.freeze({ ...adapters.config.app }),
      google: Object.freeze({ ...adapters.config.google }),
    }),
  });
  instances.set(pinia, services);
  return services;
};

export const getApplicationServices = (pinia = getActivePinia()) => {
  const services = pinia && instances.get(pinia);
  if (!services)
    throw new Error(
      "Instala los adaptadores en esta aplicación antes de usar sus servicios.",
    );
  return services;
};
