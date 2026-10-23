/** Contrato de acceso al backend; el transporte se inyecta en bootstrap.js. */
import { getApplicationServices } from '../ports/services.js';
import { captureSession, inCurrentSession } from './sessionBoundary.js';

export const apiGet = (...args) => inCurrentSession(() => getApplicationServices().http.apiGet(...args));
export const apiPost = (...args) => inCurrentSession(() => getApplicationServices().http.apiPost(...args));
export const apiPut = (...args) => inCurrentSession(() => getApplicationServices().http.apiPut(...args));
export const apiDelete = (...args) => inCurrentSession(() => getApplicationServices().http.apiDelete(...args));
export const backendRequest = async (...args) => {
  const assertCurrent = captureSession();
  const response = await getApplicationServices().http.rawRequest(...args);
  assertCurrent();
  return new Proxy(response, {
    get(target, name) {
      if (name === 'json' || name === 'text') return async () => {
        assertCurrent();
        const data = await target[name]();
        assertCurrent();
        return data;
      };
      const value = Reflect.get(target, name, target);
      return typeof value === 'function' ? value.bind(target) : value;
    },
  });
};
export const parseError = (...args) => getApplicationServices().http.parseError(...args);
export const authHeaders = (token) => getApplicationServices().http.authHeaders(token);
