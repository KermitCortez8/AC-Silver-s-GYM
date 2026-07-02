import assert from 'node:assert/strict';
import { isValidEmail } from '../src/utils/authUtils.js';

assert.equal(isValidEmail('cliente.example.com'), false);
