import assert from 'node:assert/strict';
import { normalizeDni, normalizeEmail } from '../src/utils/clientIdentity.js';

assert.equal(normalizeEmail(' Cliente@Example.COM '), 'cliente@example.com');
assert.equal(normalizeDni('12.345-678'), '12345678');
