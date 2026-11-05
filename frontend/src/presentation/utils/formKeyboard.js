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
  });
  if (!action) return false;

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
