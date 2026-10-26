/** Transporte y frontera de sesión ligados a una aplicación concreta. */
import { getApplicationServices } from "../ports/services.js";
import { captureSession, inCurrentSession } from "./sessionBoundary.js";

export const createBackendGateway = (
  services = getApplicationServices(),
  pinia = services.pinia,
) => {
  const { http } = services;
  const run = (operation) => inCurrentSession(operation, pinia);
  return {
    apiGet: (...args) => run(() => http.apiGet(...args)),
    apiPost: (...args) => run(() => http.apiPost(...args)),
    apiPut: (...args) => run(() => http.apiPut(...args)),
    apiDelete: (...args) => run(() => http.apiDelete(...args)),
    parseError: (...args) => http.parseError(...args),
    authHeaders: (...args) => http.authHeaders(...args),
    backendRequest: async (...args) => {
      const assertCurrent = captureSession(pinia);
      const response = await http.rawRequest(...args);
      assertCurrent();
      return new Proxy(response, {
        get(target, name) {
          if (name === "json" || name === "text")
            return async () => {
              assertCurrent();
              const data = await target[name]();
              assertCurrent();
              return data;
            };
          const value = Reflect.get(target, name, target);
          return typeof value === "function" ? value.bind(target) : value;
        },
      });
    },
  };
};
