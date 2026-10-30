import assert from 'node:assert/strict';
import { test } from 'node:test';
import { reactive } from 'vue';
import { emailError, validateAccountForm, amountError, durationError, promotionErrors } from '../src/domain/utils/formValidation.js';
import { useFormValidation } from '../src/presentation/composables/useFormValidation.js';
import { parseError } from '../src/infrastructure/services/apiResponse.js';

for (const email of ['ana@gmail.com', 'ana@hotmail.com', 'ana@example.com', 'ana@outlook.com', 'ana@company.com', 'ana@sub.gmail.com', 'ana@gmail.com.evil.com', '  Ana+gym@GMAIL.COM  ']) {
  test(`account email accepts ${email}`, () => assert.equal(emailError(email), ''));
}
for (const email of ['', 'ana', '@gmail.com', 'ana@@gmail.com', 'a..b@gmail.com', '.ana@gmail.com', 'ana.@gmail.com', 'ana b@gmail.com', 'ana@gmail', 'ana@-gmail.com', 'ana@gmail.com\nmail@hotmail.com']) {
  test(`malformed account email is rejected: ${JSON.stringify(email)}`, () => assert.match(emailError(email), /correo válido|obligatorio/));
}
for (const email of ['ana@gmail.co', 'ana@example.org', 'ana@example.com.pe']) {
  test(`unapproved domain is rejected: ${email}`, () => assert.equal(emailError(email), 'Solo se permiten correos que terminen en .com.'));
}

test('public registration explains every invalid field and clears errors after correction', async () => {
  const form = reactive({ nombre: ' ', correo: 'a@b.org', dni: '12abc456', telefono: '987 65432', password: '12345' });
  const validation = useFormValidation(form, value => validateAccountForm(value, { requirePhone: true }));
  assert.equal(validation.validateForm(), false);
  assert.deepEqual(Object.keys(validation.fieldErrors), ['nombre', 'correo', 'dni', 'telefono', 'password']);
  Object.assign(form, { nombre: 'Ana', correo: 'ana@hotmail.com', dni: '01234567', telefono: '987654321', password: 'secreto123' });
  await validation.revalidateField('correo');
  assert.equal(validation.fieldErrors.correo, '');
  assert.equal(validation.validateForm(), true);
  assert.deepEqual({ ...validation.fieldErrors }, {});
});

test('editing permits an unchanged password but rejects short replacements and invalid optional identity fields', () => {
  const form = { nombre: 'Ana', correo: 'ana@gmail.com', dni: '', telefono: '', password: '' };
  const options = { requirePassword: false, requireDni: false };
  assert.deepEqual(validateAccountForm(form, options), {});
  assert.ok(validateAccountForm({ ...form, password: '123' }, options).password);
  assert.ok(validateAccountForm({ ...form, dni: '1' }, options).dni);
  assert.ok(validateAccountForm({ ...form, telefono: '1234abc' }, options).telefono);
});

test('verified Google accounts still require valid identity fields and an approved email domain', () => {
  const errors = validateAccountForm({ nombre: 'Ana', correo: 'ana@company.org', dni: '', telefono: '' }, { google: true, requirePhone: true });
  assert.deepEqual(Object.keys(errors), ['correo', 'dni', 'telefono']);
});

test('prices, plan durations and promotion constraints have specific Spanish messages', () => {
  for (const amount of ['', -1, 'abc', Infinity, NaN, '1.234']) assert.ok(amountError(amount));
  for (const amount of [0, '79.50', 100]) assert.equal(amountError(amount), '');
  for (const duration of ['', '0 dias', '-1 mes', 'mensual', '1.5 años']) assert.ok(durationError(duration));
  for (const duration of ['30 días', '1 mes', '3 meses', '1 año']) assert.equal(durationError(duration), '');
  const errors = promotionErrors({ name: '', discountType: 'percent', discountValue: 101, startsAt: '2026-12-10', validUntil: '2026-12-01', appliesTo: [], limite_cupos: 1.5 });
  assert.deepEqual(Object.keys(errors), ['name', 'discountValue', 'validUntil', 'appliesTo', 'limite_cupos']);
});

test('API validation issues become Spanish inline errors without changing HTTP status', async () => {
  const error = await parseError(new Response(JSON.stringify({ detail: [
    { loc: ['body', 'correo'], type: 'value_error', msg: 'Value error, Solo se permiten correos que terminen en .com.' },
    { loc: ['body', 'cantidad'], type: 'int_parsing', msg: 'Input should be a valid integer' },
    { loc: ['body', 'nombre'], type: 'missing', msg: 'Field required' },
  ] }), { status: 422, headers: { 'content-type': 'application/json' } }));
  assert.equal(error.status, 422);
  assert.equal(error.fieldErrors.correo, 'Solo se permiten correos que terminen en .com.');
  assert.equal(error.fieldErrors.cantidad, 'Ingresa un número entero válido.');
  assert.equal(error.fieldErrors.nombre, 'Este campo es obligatorio.');
  assert.doesNotMatch(error.message, /Value error|Field required|Input should/);
});
