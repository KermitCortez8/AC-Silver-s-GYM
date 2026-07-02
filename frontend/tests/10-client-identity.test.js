import assert from 'node:assert/strict';
import {
  attendanceBelongsToClient,
  buildClientIdentityFromUser,
  resolveClientIdForUser,
  weekdayFromISO,
} from '../src/utils/clientIdentity.js';

const members = [{ id_cliente: 12, id: 'SGCLI012', email: 'cliente@example.com' }];
const user = { id: 'SGCLI012', email: 'cliente@example.com' };
const identity = buildClientIdentityFromUser(user, members);

assert.equal(resolveClientIdForUser(user, members), 12);
assert.equal(identity.id_cliente, 12);
assert.equal(attendanceBelongsToClient({ memberCode: 'SGCLI012' }, identity), true);
assert.equal(weekdayFromISO('2026-07-02'), 'jueves');
