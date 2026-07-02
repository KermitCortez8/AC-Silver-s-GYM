import assert from 'node:assert/strict';
import { decodeJWT } from '../src/utils/authUtils.js';

const encodedPayload = Buffer.from(JSON.stringify({ email: 'cliente@example.com' })).toString('base64url');

assert.deepEqual(decodeJWT(`header.${encodedPayload}.signature`), { email: 'cliente@example.com' });
