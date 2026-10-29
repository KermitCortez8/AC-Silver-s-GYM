import { APP_CONFIG } from "../config/appConfig";
import { parseError, parseResponse } from "./apiResponse.js";
import { fetchWithTimeout } from "./httpTransport.js";

export const createApiClient = (config = APP_CONFIG) => {
  /**
   * Crea el registro correspondiente.
   */
  const buildUrl = (path) => {
    if (!config.authApiBaseUrl) {
      throw new Error("No hay backend configurado en VITE_AUTH_API_BASE_URL");
    }

    const normalizedPath = String(path || "").startsWith("/")
      ? path
      : `/${path}`;
    return `${config.authApiBaseUrl}${normalizedPath}`;
  };

  /**
   * Crea el registro correspondiente.
   */
  const buildHeaders = (token, headers = {}) => {
    const requestHeaders = {
      "Content-Type": "application/json",
      ...headers,
    };

    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`;
    }

    return requestHeaders;
  };

  const request = async (path, options = {}, token = "") => {
    const { errorMessage, ...fetchOptions } = options;
    const response = await fetchWithTimeout(buildUrl(path), {
      ...fetchOptions,
      headers: buildHeaders(token, fetchOptions.headers),
    }, config.requestTimeoutMs);

    if (!response.ok) {
      const error = await parseError(response);
      if (errorMessage) error.message = errorMessage;
      throw error;
    }

    if (
      response.status !== 204 &&
      !(response.headers.get("content-type") || "").includes("application/json")
    ) {
      throw new Error(
        "El servidor no devolvió los datos esperados. Inténtalo de nuevo o contacta con administración.",
      );
    }
    return parseResponse(response);
  };

  const apiGet = (path, token = "") => request(path, { method: "GET" }, token);
  const apiPost = (path, body, token = "") =>
    request(path, { method: "POST", body: JSON.stringify(body ?? {}) }, token);
  const apiPut = (path, body, token = "") =>
    request(path, { method: "PUT", body: JSON.stringify(body ?? {}) }, token);
  const apiDelete = (path, token = "") =>
    request(path, { method: "DELETE" }, token);

  // Compatibilidad con operaciones que necesitan inspeccionar el estado HTTP.
  const rawRequest = (url, options) => fetchWithTimeout(url, options, config.requestTimeoutMs);
  const authHeaders = (token = "") => buildHeaders(token);

  return {
    request,
    apiGet,
    apiPost,
    apiPut,
    apiDelete,
    rawRequest,
    authHeaders,
  };
};

export const {
  request,
  apiGet,
  apiPost,
  apiPut,
  apiDelete,
  rawRequest,
  authHeaders,
} = createApiClient();
