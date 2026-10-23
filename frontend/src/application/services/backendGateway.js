/** Contrato de acceso al backend; el transporte se inyecta en bootstrap.js. */
import { getApplicationServices } from '../ports/services.js';

export const apiGet = (...args) => getApplicationServices().http.apiGet(...args);
export const apiPost = (...args) => getApplicationServices().http.apiPost(...args);
export const apiPut = (...args) => getApplicationServices().http.apiPut(...args);
export const apiDelete = (...args) => getApplicationServices().http.apiDelete(...args);
export const backendRequest = (...args) => getApplicationServices().http.rawRequest(...args);
export const parseError = (...args) => getApplicationServices().http.parseError(...args);
export const authHeaders = (token) => getApplicationServices().http.authHeaders(token);
