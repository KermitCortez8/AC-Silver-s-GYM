import assert from 'node:assert/strict';
import { isValidEmail } from '../src/infrastructure/utils/authUtils.js';

assert.equal(isValidEmail('cliente@example.com'), true);
