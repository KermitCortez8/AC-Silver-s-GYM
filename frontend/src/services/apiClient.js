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
  const response = await fetch(buildUrl(path), {
    ...options,
    headers: buildHeaders(token, options.headers),
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  return parseResponse(response);
};

export const apiGet = (path, token = '') => request(path, { method: 'GET' }, token);
export const apiPost = (path, body, token = '') => request(path, { method: 'POST', body: JSON.stringify(body ?? {}) }, token);
export const apiPut = (path, body, token = '') => request(path, { method: 'PUT', body: JSON.stringify(body ?? {}) }, token);
export const apiDelete = (path, token = '') => request(path, { method: 'DELETE' }, token);
