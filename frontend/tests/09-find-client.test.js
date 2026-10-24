import assert from 'node:assert/strict';
import { findClientForUser } from '../src/domain/utils/clientIdentity.js';

const members = [{ id_cliente: 7, email: 'otro@example.com' }];

assert.equal(findClientForUser({ id_cliente: 7 }, members), members[0]);
