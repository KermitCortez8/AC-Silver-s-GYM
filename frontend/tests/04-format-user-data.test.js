import assert from 'node:assert/strict';
import { formatUserData } from '../src/infrastructure/utils/authUtils.js';

const user = formatUserData({ id_usuario: 'SGCLI001', correo: 'cliente@example.com' });

assert.equal(user.id, 'SGCLI001');
assert.equal(user.email, 'cliente@example.com');
