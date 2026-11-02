import { FORM_LIMITS } from './formLimits.js';
import { amountError, durationError, requiredTextError } from './formValidation.js';

const durations = [1, 7, 15, 30, 60, 90, 180, 365].map(days => ({
  value: `${days} ${days === 1 ? 'día' : 'días'}`,
  label: `${days} ${days === 1 ? 'día' : 'días'}`,
}));

/** Conserva la duración contratada al editar, aunque no sea una de las habituales. */
export const planDurationOptions = (registeredDuration = '') => {
  const value = String(registeredDuration ?? '').trim();
  return value && !durations.some(option => option.value === value)
    ? [{ value, label: `${value} (duración actual)` }, ...durations]
    : durations;
};

export const membershipPlanErrors = form => Object.fromEntries(Object.entries({
  name: requiredTextError(form.name, 'El nombre del plan', FORM_LIMITS.shortText),
  duration: durationError(form.duration) ? 'Selecciona una duración válida.' : '',
  price: amountError(form.price),
}).filter(([, message]) => message));
