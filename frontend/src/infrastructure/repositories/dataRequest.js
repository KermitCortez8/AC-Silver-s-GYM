/** Único límite HTTP para los repositorios que devuelven datos de negocio. */
import { parseError } from '../services/apiResponse.js';

export const dataRequest = async (http, url, options = {}, token = '') => {
  let response;
  try {
    response = await http.rawRequest(url, {
      ...options,
      headers: http.authHeaders(token),
    });
  } catch {
    throw new Error('No se pudo contactar con el servidor. Comprueba tu conexión e inténtalo de nuevo.');
  }
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return null;
  if (!(response.headers.get('content-type') || '').includes('application/json')) {
    throw new Error('El servidor no devolvió los datos esperados. Inténtalo de nuevo.');
  }
  return response.json();
};
