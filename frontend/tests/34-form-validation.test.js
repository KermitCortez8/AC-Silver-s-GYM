import assert from 'node:assert/strict';
import { test } from 'node:test';
import { reactive } from 'vue';
import { emailError, validateAccountForm, amountError, durationError, promotionErrors, quantityError, requiredTextError } from '../src/domain/utils/formValidation.js';
import { useFormValidation } from '../src/presentation/composables/useFormValidation.js';
import { useLiveWarnings } from '../src/presentation/composables/useLiveWarnings.js';
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

test('a checked field shows or clears its error with each change, not only after blur', async () => {
  const form = reactive({ nombre: 'Ana', correo: 'ana@gmail.com', dni: '01234567', telefono: '', password: 'secreto123' });
  const validation = useFormValidation(form, value => validateAccountForm(value));
  validation.validateField('correo');
  form.correo = 'ana@';
  await validation.revalidateField('correo');
  assert.match(validation.fieldErrors.correo, /correo válido/);
  form.correo = 'ana@hotmail.com';
  await validation.revalidateField('correo');
  assert.equal(validation.fieldErrors.correo, '');
  await validation.revalidateField('nombre');
  assert.equal(validation.fieldErrors.nombre, undefined, 'Un campo sin revisar no muestra avisos al escribir');
});

test('live warnings follow the current value and only show on touched fields', () => {
  const form = reactive({ nombre: '', cantidad: '' });
  const live = useLiveWarnings({
    nombre: () => requiredTextError(form.nombre),
    cantidad: () => quantityError(form.cantidad, { label: 'La cantidad', min: 1 }),
  });
  assert.equal(live.warnings.value.nombre, '');
  assert.equal(live.isInvalid('nombre', true), true, 'Sin tocar, respeta el resultado del ultimo envio');
  live.touch('nombre');
  assert.equal(live.warnings.value.nombre, 'El nombre es obligatorio.');
  form.nombre = 'Apache';
  assert.equal(live.warnings.value.nombre, '');
  assert.equal(live.isInvalid('nombre', true), false);
  live.flash('nombre', 'Sin caracteres especiales');
  assert.equal(live.warnings.value.nombre, 'Sin caracteres especiales');
  live.touch('nombre');
  assert.equal(live.warnings.value.nombre, '', 'Una tecla valida quita el aviso de la bloqueada');
  live.touchAll();
  assert.equal(live.warnings.value.cantidad, 'La cantidad es obligatoria.');
  form.cantidad = '0';
  assert.match(live.warnings.value.cantidad, /entre 1 y/);
  live.reset();
  assert.equal(live.warnings.value.cantidad, '');
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
    { loc: ['body', 'correo'], type: 'value_error', msg: 'Value error, Solo se permiten correos @gmail.com o @hotmail.com.' },
    { loc: ['body', 'cantidad'], type: 'int_parsing', msg: 'Input should be a valid integer' },
    { loc: ['body', 'nombre'], type: 'missing', msg: 'Field required' },
  ] }), { status: 422, headers: { 'content-type': 'application/json' } }));
  assert.equal(error.status, 422);
  assert.equal(error.fieldErrors.correo, 'Solo se permiten correos @gmail.com o @hotmail.com.');
  assert.equal(error.fieldErrors.cantidad, 'Ingresa un número entero válido.');
  assert.equal(error.fieldErrors.nombre, 'Este campo es obligatorio.');
  assert.doesNotMatch(error.message, /Value error|Field required|Input should/);
});


test('los límites de cuentas y promociones aceptan el máximo y rechazan un carácter adicional', () => {
  const base = { nombre: 'Á'.repeat(50), correo: 'ana@example.com', dni: '01234567', telefono: '012345678', password: 'secreto' };
  assert.deepEqual(validateAccountForm(base), {});
  assert.ok(validateAccountForm({ ...base, nombre: 'Á'.repeat(51) }).nombre);
  const email = length => 'a'.repeat(length - 12) + '@example.com';
  assert.equal(emailError(email(50)), '');
  assert.ok(emailError(email(51)));
  for (const telefono of ['1234567', '12345678', '1234567890']) {
    assert.ok(validateAccountForm({ ...base, telefono }).telefono);
  }
  const promotion = { name: 'P'.repeat(50), discountValue: 10, discountType: 'percent', appliesTo: [1] };
  assert.deepEqual(promotionErrors(promotion), {});
  assert.ok(promotionErrors({ ...promotion, name: 'P'.repeat(51) }).name);
});
