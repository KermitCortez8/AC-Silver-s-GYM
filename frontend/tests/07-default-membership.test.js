import assert from 'node:assert/strict';
import { createDefaultMembership } from '../src/infrastructure/utils/authUtils.js';

assert.equal(createDefaultMembership({ role: 'admin' }).plan, 'Acceso total');
