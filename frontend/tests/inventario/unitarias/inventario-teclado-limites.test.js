import assert from 'node:assert/strict';
import { test } from 'node:test';
import { resolveFormKey } from '../../../src/domain/utils/keyboardNav.js';
import { clampText, cleanInteger, cleanText, INVENTORY_NAME_MAX_LENGTH, isAllowedInteger, NOTES_MAX_LENGTH, SEARCH_MAX_LENGTH } from '../../../src/domain/utils/inputRules.js';

const text = (extra = {}) => ({ tag: 'INPUT', type: 'text', isFirst: false, isLast: false, ...extra });

test('límites de Inventario: 40 en búsqueda y nombres, 100 en observaciones', () => {
  assert.equal(SEARCH_MAX_LENGTH, 40);
  assert.equal(INVENTORY_NAME_MAX_LENGTH, 40);
  assert.equal(NOTES_MAX_LENGTH, 100);
});

test('un nombre de artículo se corta a 40 caracteres', () => {
  const { value, truncated } = cleanText('A'.repeat(55), INVENTORY_NAME_MAX_LENGTH);
  assert.equal(value.length, 40);
  assert.equal(truncated, true);
});

test('las observaciones se cortan a 100, conservan puntuación y quitan caracteres de control', () => {
  const largo = clampText(`Revisar, urgente. ${'x'.repeat(200)}`);
  assert.equal(largo.value.length, 100);
  assert.equal(largo.truncated, true);
  assert.equal(clampText('Cinta rota, cambiar.').value, 'Cinta rota, cambiar.');
  assert.equal(clampText('a\u0000b\u0007c').value, 'abc');
  assert.equal(clampText('línea 1\nlínea 2').value, 'línea 1\nlínea 2');
  assert.equal(clampText(null).value, '');
});

test('Enter pasa al siguiente campo y en el último guarda', () => {
  assert.equal(resolveFormKey({ key: 'Enter', ...text() }), 'next');
  assert.equal(resolveFormKey({ key: 'Enter', ...text({ isLast: true }) }), 'submit');
  assert.equal(resolveFormKey({ key: 'Enter', tag: 'SELECT', type: 'select-one' }), 'next');
});

test('Shift+Enter vuelve al campo anterior, salvo en el primero', () => {
  assert.equal(resolveFormKey({ key: 'Enter', shiftKey: true, ...text() }), 'prev');
  assert.equal(resolveFormKey({ key: 'Enter', shiftKey: true, ...text({ isFirst: true }) }), null);
});

test('en un textarea Enter inserta salto de línea y Ctrl+Enter guarda', () => {
  assert.equal(resolveFormKey({ key: 'Enter', tag: 'TEXTAREA', type: 'textarea' }), null);
  assert.equal(resolveFormKey({ key: 'Enter', ctrlKey: true, tag: 'TEXTAREA', type: 'textarea' }), 'submit');
  assert.equal(resolveFormKey({ key: 'Enter', ctrlKey: true, ...text() }), 'submit');
});

test('los botones y enlaces conservan su Enter nativo', () => {
  assert.equal(resolveFormKey({ key: 'Enter', tag: 'BUTTON', type: 'button' }), null);
  assert.equal(resolveFormKey({ key: 'Enter', tag: 'INPUT', type: 'submit' }), null);
  assert.equal(resolveFormKey({ key: 'Enter', tag: 'A', type: '' }), null);
});

test('las flechas arriba y abajo recorren campos de texto', () => {
  assert.equal(resolveFormKey({ key: 'ArrowDown', ...text() }), 'next');
  assert.equal(resolveFormKey({ key: 'ArrowUp', ...text() }), 'prev');
  assert.equal(resolveFormKey({ key: 'ArrowDown', ...text({ isLast: true }) }), null);
  assert.equal(resolveFormKey({ key: 'ArrowUp', ...text({ isFirst: true }) }), null);
});

test('las flechas recorren desplegables, opciones y casillas', () => {
  for (const [tag, type] of [['SELECT', 'select-one'], ['INPUT', 'radio'], ['INPUT', 'checkbox']]) {
    assert.equal(resolveFormKey({ key: 'ArrowDown', tag, type }), 'next', `${tag}/${type}`);
    assert.equal(resolveFormKey({ key: 'ArrowUp', tag, type }), 'prev', `${tag}/${type}`);
  }
});

test('con la lista de un desplegable abierta, las flechas eligen la opción', () => {
  assert.equal(resolveFormKey({ key: 'ArrowDown', tag: 'SELECT', type: 'select-one', pickerOpen: true }), null);
  assert.equal(resolveFormKey({ key: 'ArrowUp', tag: 'SELECT', type: 'select-one', pickerOpen: true }), null);
});

test('Espacio abre un desplegable cerrado y no hace nada especial si ya está abierto', () => {
  assert.equal(resolveFormKey({ key: ' ', tag: 'SELECT', type: 'select-one' }), 'open');
  assert.equal(resolveFormKey({ key: ' ', tag: 'SELECT', type: 'select-one', pickerOpen: true }), null);
  assert.equal(resolveFormKey({ key: ' ', ...text() }), null);
});

test('en un textarea las flechas solo salen del campo con el cursor al final o al inicio', () => {
  const area = { tag: 'TEXTAREA', type: 'textarea' };
  assert.equal(resolveFormKey({ key: 'ArrowDown', ...area, caretAtEnd: false }), null);
  assert.equal(resolveFormKey({ key: 'ArrowDown', ...area, caretAtEnd: true }), 'next');
  assert.equal(resolveFormKey({ key: 'ArrowUp', ...area, caretAtStart: false }), null);
  assert.equal(resolveFormKey({ key: 'ArrowUp', ...area, caretAtStart: true }), 'prev');
});

test('las fechas conservan sus flechas para cambiar día, mes y año', () => {
  assert.equal(resolveFormKey({ key: 'ArrowDown', tag: 'INPUT', type: 'date' }), null);
  assert.equal(resolveFormKey({ key: 'ArrowUp', tag: 'INPUT', type: 'date' }), null);
});

test('izquierda y derecha no se interceptan: mueven el cursor o cambian la opción', () => {
  for (const [tag, type] of [['INPUT', 'text'], ['INPUT', 'radio'], ['TEXTAREA', 'textarea']]) {
    assert.equal(resolveFormKey({ key: 'ArrowLeft', tag, type }), null);
    assert.equal(resolveFormKey({ key: 'ArrowRight', tag, type }), null);
  }
});

test('los campos numéricos solo aceptan dígitos', () => {
  assert.equal(isAllowedInteger('7'), true);
  for (const texto of ['a', 'e', '-', '+', '.', ',', ' ']) assert.equal(isAllowedInteger(texto), false, texto);
  assert.equal(cleanInteger('12abc-3.4e5'), '12345');
});

test('no interfiere con la composición de texto (IME) ni con Alt/Meta', () => {
  assert.equal(resolveFormKey({ key: 'Enter', isComposing: true, ...text() }), null);
  assert.equal(resolveFormKey({ key: 'Enter', altKey: true, ...text() }), null);
  assert.equal(resolveFormKey({ key: 'ArrowDown', metaKey: true, ...text() }), null);
});
