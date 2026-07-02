import assert from 'node:assert/strict';
import { getUserRole } from '../src/utils/authUtils.js';

assert.equal(getUserRole('admin@urp.edu.pe'), 'admin');
