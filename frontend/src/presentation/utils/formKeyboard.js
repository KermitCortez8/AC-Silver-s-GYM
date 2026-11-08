import { resolveFormKey } from '../../domain/utils/keyboardNav.js';

const FIELD_SELECTOR = [
  'input:not([disabled]):not([readonly]):not([type="hidden"]):not([type="file"]):not([type="button"]):not([type="submit"]):not([type="reset"])',
  'select:not([disabled])',
  'textarea:not([disabled]):not([readonly])',
].join(', ');

const isVisible = (element) => element.offsetParent !== null || element.getClientRects().length > 0;

/** Campos navegables del formulario, en orden visual; un solo representante por grupo de radios. */
export const listFields = (root) => {
  const seenRadios = new Set();
  return [...root.querySelectorAll(FIELD_SELECTOR)].filter((element) => {
    if (!isVisible(element)) return false;
    if (element.type !== 'radio') return true;
    if (seenRadios.has(element.name)) return false;
    seenRadios.add(element.name);
    return true;
  });
};

/**
 * Abre un desplegable con Espacio. Con la lista abierta, las flechas eligen la opción
 * (hasta que se cierre por cambio, pérdida de foco o clic).
 */
const openPicker = (select, event) => {
  if (typeof select.showPicker !== 'function') return false;
  try {
    select.showPicker();
  } catch {
    return false;
  }
  event.preventDefault();
  select.dataset.pickerOpen = '1';
  const events = ['change', 'blur', 'mousedown'];
  const clear = () => {
    delete select.dataset.pickerOpen;
    events.forEach((name) => select.removeEventListener(name, clear));
  };
  events.forEach((name) => select.addEventListener(name, clear));
  return true;
};

/** Espacio abre cualquier desplegable de la pantalla (filtros, listas). Devuelve true si lo atendió. */
export const openSelectOnSpace = (event) => {
  const target = event.target;
  if (!target || target.tagName !== 'SELECT' || event.defaultPrevented) return false;
  if (event.key !== ' ' || event.ctrlKey || event.shiftKey || event.altKey || event.metaKey) return false;
  if (target.dataset.pickerOpen === '1') return false;
  return openPicker(target, event);
};

/**
 * Aplica el teclado estilo Windows dentro de `root`. Devuelve true si atendió la tecla.
 * `submit` se llama cuando la tecla pide guardar.
 */
export const handleFormKeydown = (event, root, { submit } = {}) => {
  if (!root || event.defaultPrevented) return false;
  const target = event.target;
  const fields = listFields(root);
  let index = fields.indexOf(target);
  if (index < 0 && target?.type === 'radio') {
    index = fields.findIndex((field) => field.type === 'radio' && field.name === target.name);
  }
  if (index < 0) return false;

  const action = resolveFormKey({
    key: event.key,
    shiftKey: event.shiftKey,
    ctrlKey: event.ctrlKey,
    altKey: event.altKey,
    metaKey: event.metaKey,
    isComposing: event.isComposing,
    tag: target.tagName,
    type: target.type,
    isFirst: index === 0,
    isLast: index === fields.length - 1,
    // En un textarea solo se sale con flechas si el cursor está al inicio o al final del texto.
    caretAtStart: target.tagName !== 'TEXTAREA' || (target.selectionStart === 0 && target.selectionEnd === 0),
    caretAtEnd: target.tagName !== 'TEXTAREA' || (target.selectionStart === target.value.length && target.selectionEnd === target.value.length),
    pickerOpen: target.dataset?.pickerOpen === '1',
  });
  if (!action) return false;

  if (action === 'open') return openPicker(target, event);
  event.preventDefault();
  if (action === 'submit') {
    submit?.();
    return true;
  }
  const next = fields[index + (action === 'next' ? 1 : -1)];
  if (next) {
    next.focus();
    // Como al tabular en Windows: el contenido del campo queda seleccionado.
    try { next.select?.(); } catch { /* algunos tipos no admiten select() */ }
  }
  return true;
};
