import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseQuantity, MAX_QUANTITY } from '../src/domain/utils/quantities.js';
import { feedbackClass } from '../src/presentation/utils/feedback.js';

test('quantities accept digits and respect stock and movement bounds', () => {
  for (const value of [0, '0', '012', 12, MAX_QUANTITY]) assert.equal(parseQuantity(value), Number(value));
  for (const value of ['', ' ', '-1', '+1', '1.1', '1e2', '2E3', '12abc', '2\n', true, null, undefined, Infinity, NaN, MAX_QUANTITY + 1]) {
    assert.throws(() => parseQuantity(value), Error, String(value));
  }
  assert.throws(() => parseQuantity(0, { min: 1 }));
  assert.equal(parseQuantity('1', { min: 1 }), 1);
});

test('notices and confirmations are blue and errors are red', () => {
  for (const tone of ['success', 'info', 'warn']) assert.equal(feedbackClass(tone), 'app-notice app-notice--info');
  assert.equal(feedbackClass('error'), 'app-notice app-notice--error');
});
