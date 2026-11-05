/**
 * Teclado de formularios al estilo Windows (lógica pura, sin DOM).
 *
 * - Tab / Shift+Tab: los gestiona el navegador (siguiente / anterior).
 * - Enter: pasa al siguiente campo; en el último campo guarda. Shift+Enter vuelve al anterior.
 * - Flecha abajo / arriba en campos de texto: siguiente / anterior campo.
 * - Ctrl+Enter: guarda desde cualquier campo (en un textarea, Enter inserta un salto de línea).
 * Devuelve 'next', 'prev', 'submit' o null (dejar el comportamiento nativo).
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
  const isTextInput = element === 'INPUT' && TEXT_TYPES.has(kind);
  if (key === 'ArrowDown' && isTextInput) return isLast ? null : 'next';
  if (key === 'ArrowUp' && isTextInput) return isFirst ? null : 'prev';
  return null;
};
