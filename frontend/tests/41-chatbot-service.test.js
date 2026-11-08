import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createHttpChatService, ChatbotApiError } from '../src/infrastructure/services/httpChatService.js';

test('ChatbotApiError initializes with correct fields and status', () => {
  const err429 = new ChatbotApiError('Límite excedido', 429, {
    code: 'rate_limit_exceeded',
    retry_after_seconds: 45,
  });
  assert.equal(err429.status, 429);
  assert.equal(err429.code, 'rate_limit_exceeded');
  assert.equal(err429.retryAfterSeconds, 45);
  assert.equal(err429.message, 'Límite excedido');

  const err500 = new ChatbotApiError('Error interno', 500);
  assert.equal(err500.status, 500);
  assert.equal(err500.retryAfterSeconds, 0);
});

test('httpChatService sends request with correct headers, JWT token, and body payload', async () => {
  let capturedUrl = '';
  let capturedOptions = {};

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    capturedUrl = url;
    capturedOptions = options;
    return new Response(
      JSON.stringify({
        conversation_id: 'conv-test-123',
        blocks: [{ type: 'text', text: 'Respuesta de prueba' }],
        quick_replies: [{ label: 'Horarios', action: 'horarios' }],
        state: 'ok',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  };

  try {
    const service = createHttpChatService({ authApiBaseUrl: 'http://test-api:8000' });
    const result = await service.sendMessage({
      message: '¿Cuáles son los horarios?',
      conversationId: 'conv-test-123',
      token: 'jwt-token-fake-abc',
      clientContext: { current_path: '/horarios', device: 'desktop' },
    });

    assert.equal(capturedUrl, 'http://test-api:8000/api/chatbot/message');
    assert.equal(capturedOptions.method, 'POST');
    assert.equal(capturedOptions.headers['Content-Type'], 'application/json');
    assert.equal(capturedOptions.headers.Authorization, 'Bearer jwt-token-fake-abc');

    const body = JSON.parse(capturedOptions.body);
    assert.equal(body.message, '¿Cuáles son los horarios?');
    assert.equal(body.conversation_id, 'conv-test-123');
    assert.equal(body.client_context.current_path, '/horarios');

    assert.equal(result.conversation_id, 'conv-test-123');
    assert.equal(result.state, 'ok');
    assert.equal(result.blocks.length, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('httpChatService maps 429 rate limit errors to ChatbotApiError with retryAfterSeconds', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => {
    return new Response(
      JSON.stringify({
        detail: {
          code: 'rate_limit_exceeded',
          message: 'Has alcanzado el límite de mensajes permitidos.',
          retry_after_seconds: 60,
        },
      }),
      { status: 429, headers: { 'Content-Type': 'application/json' } }
    );
  };

  try {
    const service = createHttpChatService({ authApiBaseUrl: 'http://test-api:8000' });
    await assert.rejects(
      async () => {
        await service.sendMessage({ message: 'Ráfaga de spam' });
      },
      (err) => {
        assert(err instanceof ChatbotApiError);
        assert.equal(err.status, 429);
        assert.equal(err.code, 'rate_limit_exceeded');
        assert.equal(err.retryAfterSeconds, 60);
        assert.match(err.message, /límite de mensajes/);
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('httpChatService maps 401 session expired errors to ChatbotApiError', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => {
    return new Response(
      JSON.stringify({
        detail: {
          code: 'session_expired',
          message: 'Tu sesión ha expirado.',
        },
      }),
      { status: 401, headers: { 'Content-Type': 'application/json' } }
    );
  };

  try {
    const service = createHttpChatService({ authApiBaseUrl: 'http://test-api:8000' });
    await assert.rejects(
      async () => {
        await service.sendMessage({ message: 'Consulta con token vencido', token: 'expired-jwt' });
      },
      (err) => {
        assert(err instanceof ChatbotApiError);
        assert.equal(err.status, 401);
        assert.equal(err.code, 'session_expired');
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
