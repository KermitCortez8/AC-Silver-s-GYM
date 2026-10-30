import { isAllowedDecimal, isAllowedInteger, isAllowedText } from '../../domain/utils/inputRules.js';

/**
 * Crea un manejador de `beforeinput` que bloquea al escribir lo que no cumple la regla.
 * `onReject` recibe el aviso para mostrarlo junto al campo.
 */
const guard = (isAllowed, message) => (onReject) => (event) => {
  if (event.data && !isAllowed(event.data)) {
    event.preventDefault();
    onReject?.(message);
  }
};

export const blockNonInteger = guard(isAllowedInteger, 'Solo números enteros positivos.');
export const blockNonDecimal = guard(isAllowedDecimal, 'Solo números y punto decimal.');
export const blockSpecialChars = guard(isAllowedText, 'Sin caracteres especiales: solo letras, números y espacios.');
