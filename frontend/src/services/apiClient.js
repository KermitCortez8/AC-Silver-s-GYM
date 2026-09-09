import { APP_CONFIG } from '../config/appConfig';
import { parseError, parseResponse } from './apiResponse.js';

/**
 * Crea el registro correspondiente.
 */
const buildUrl = (path) => {
  if (!APP_CONFIG.authApiBaseUrl) {
    throw new Error('No hay backend configurado en VITE_AUTH_API_BASE_URL');
  }

  const normalizedPath = String(path || '').startsWith('/') ? path : `/${path}`;
  return `${APP_CONFIG.authApiBaseUrl}${normalizedPath}`;
};

/**
 * Crea el registro correspondiente.
 */
const buildHeaders = (token, headers = {}) => {
  const requestHeaders = {
    'Content-Type': 'application/json',
    ...headers,
  };

  if (token) {
    requestHeaders.Authorization = `Bearer ${token}`;
  }

  return requestHeaders;
};

export const request = async (path, options = {}, token = '') => {
  let response;
  try {
    response = await fetch(buildUrl(path), {
      ...options,
      headers: buildHeaders(token, options.headers),
    });
  } catch {
    throw new Error('No se pudo contactar con el servidor. Comprueba tu conexión e inténtalo de nuevo.');
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status !== 204 && !(response.headers.get('content-type') || '').includes('application/json')) {
    throw new Error('El servidor no devolvió los datos esperados. Inténtalo de nuevo o contacta con administración.');
  }
  return parseResponse(response);
};

export const apiGet = (path, token = '') => request(path, { method: 'GET' }, token);
export const apiPost = (path, body, token = '') => request(path, { method: 'POST', body: JSON.stringify(body ?? {}) }, token);
export const apiPut = (path, body, token = '') => request(path, { method: 'PUT', body: JSON.stringify(body ?? {}) }, token);
export const apiDelete = (path, token = '') => request(path, { method: 'DELETE' }, token);
