import assert from 'node:assert/strict';
import { isValidUser } from '../src/utils/authUtils.js';

assert.equal(isValidUser({ id_usuario: 'SGCLI002', correo: 'cliente2@example.com' }), true);
