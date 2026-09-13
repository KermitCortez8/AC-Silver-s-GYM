/**
 * Gestiona esta acción de la vista.
 */
export const parseResponse = async (response) => {
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }

  return response.text();
};

/**
 * Gestiona esta acción de la vista.
 */
export const parseError = async (response) => {
  if (response.status === 504) {
    return new Error('El servidor tardó demasiado en responder (504). Inténtalo de nuevo en unos momentos.');
  }
  if (response.status === 502) {
    return new Error(`El servicio no está disponible temporalmente (${response.status}). Inténtalo de nuevo en unos momentos.`);
  }

  try {
    const body = await parseResponse(response);
    if (body && typeof body === 'object' && 'detail' in body) {
      if (body.detail && typeof body.detail === 'object' && body.detail.message) {
        const error = new Error(body.detail.message);
        error.code = body.detail.code;
        return error;
      }
      return new Error(String(body.detail));
    }

    if (typeof body === 'string' && body.trim()
      && !(response.headers.get('content-type') || '').includes('text/html')
      && !/<[a-z!][^>]*>/i.test(body)) {
      return new Error(body);
    }
  } catch (error) {
    // Caer al mensaje genérico.
  }

  return new Error(`Error HTTP ${response.status}`);
};
