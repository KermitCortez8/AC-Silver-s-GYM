/**
 * Teclado de formularios al estilo Windows (lógica pura, sin DOM).
 *
 * - Tab / Shift+Tab: los gestiona el navegador (siguiente / anterior).
 * - Enter: pasa al siguiente campo; en el último campo guarda. Shift+Enter vuelve al anterior.
 * - Flecha abajo / arriba: siguiente / anterior campo, también desde desplegables, opciones y casillas.
 *   En un textarea solo salen del campo cuando el cursor está al final (abajo) o al inicio (arriba).
 *   Las flechas izquierda/derecha se quedan para mover el cursor o cambiar la opción elegida.
 * - Espacio sobre un desplegable lo abre; con la lista abierta, las flechas eligen la opción.
 * - Ctrl+Enter: guarda desde cualquier campo (en un textarea, Enter inserta un salto de línea).
 * Devuelve 'next', 'prev', 'submit', 'open' o null (dejar el comportamiento nativo).
 */
const TEXT_TYPES = new Set(['', 'text', 'search', 'tel', 'email', 'url', 'password']);
const BUTTON_TYPES = new Set(['button', 'submit', 'reset', 'image']);

export const resolveFormKey = ({
  key,
  shiftKey = false,
  ctrlKey = false,
  altKey = false,
  metaKey = false,
  isComposing = false,
  tag = '',
  type = '',
  isFirst = false,
  isLast = false,
  caretAtStart = true,
  caretAtEnd = true,
  pickerOpen = false,
}) => {
  if (isComposing || altKey || metaKey) return null;
  const element = String(tag).toUpperCase();
  const kind = String(type || '').toLowerCase();

  if (key === 'Enter') {
    if (ctrlKey) return 'submit';
    if (element === 'BUTTON' || element === 'A' || element === 'TEXTAREA') return null;
    if (element === 'INPUT' && BUTTON_TYPES.has(kind)) return null;
    if (shiftKey) return isFirst ? null : 'prev';
    return isLast ? 'submit' : 'next';
  }

  if (ctrlKey || shiftKey) return null;

  if (key === ' ' && element === 'SELECT') return pickerOpen ? null : 'open';

  if (key !== 'ArrowDown' && key !== 'ArrowUp') return null;
  const forward = key === 'ArrowDown';
  let canLeave = false;
  if (element === 'INPUT') canLeave = TEXT_TYPES.has(kind) || kind === 'radio' || kind === 'checkbox';
  else if (element === 'SELECT') canLeave = !pickerOpen;
  else if (element === 'TEXTAREA') canLeave = forward ? caretAtEnd : caretAtStart;
  if (!canLeave) return null;
  if (forward) return isLast ? null : 'next';
  return isFirst ? null : 'prev';
};
