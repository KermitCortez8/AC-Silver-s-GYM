import assert from 'node:assert/strict';
import { getUserRole } from '../src/infrastructure/utils/authUtils.js';

assert.equal(getUserRole('admin@urp.edu.pe'), 'admin');
