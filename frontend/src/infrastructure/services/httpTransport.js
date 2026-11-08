// Apply the same connection/timeout behavior to JSON requests and file uploads.
// Writes are never retried automatically: a lost response may follow a successful save.
export const fetchWithTimeout = async (url, options = {}, timeoutMs = 30_000) => {
  const controller = new AbortController();
  const externalSignal = options.signal;
  let timedOut = false;
  const abort = () => controller.abort(externalSignal?.reason);
  if (externalSignal?.aborted) abort();
  else externalSignal?.addEventListener('abort', abort, { once: true });
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    // Chromium puede exponer un stream vacío incluso para un 204. Esos estados
    // no admiten cuerpo: reconstruirlos con un ArrayBuffer genera un TypeError.
    if ([204, 205, 304].includes(response.status)
      || String(options.method || 'GET').toUpperCase() === 'HEAD') return response;
    if (!response.body) return response;

    // These clients consume complete JSON/text responses. Keep the deadline and
    // caller cancellation active until the body has arrived, then expose an
    // unread response so existing status checks and parsers keep working.
    const body = await response.arrayBuffer();
    return Object.defineProperties(new Response(body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    }), {
      url: { value: response.url },
      redirected: { value: response.redirected },
      type: { value: response.type },
    });
  } catch {
    const isWrite = !['GET', 'HEAD'].includes(String(options.method || 'GET').toUpperCase());
    const error = new Error(timedOut
      ? (isWrite
        ? 'La solicitud tardó demasiado. No se pudo confirmar el guardado; actualiza los datos antes de repetir la operación.'
        : 'El servidor tardó demasiado en responder. Inténtalo de nuevo en unos momentos.')
      : externalSignal?.aborted
        ? 'La solicitud fue cancelada.'
        : isWrite
          ? 'No se pudo confirmar la operación. Comprueba tu conexión y actualiza los datos antes de repetirla.'
          : 'No se pudo contactar con el servidor. Comprueba tu conexión e inténtalo de nuevo.');
    error.code = timedOut ? 'request_timeout' : externalSignal?.aborted ? 'request_cancelled' : 'network_error';
    error.outcomeUnknown = isWrite && !externalSignal?.aborted;
    throw error;
  } finally {
    clearTimeout(timeout);
    externalSignal?.removeEventListener('abort', abort);
  }
};
