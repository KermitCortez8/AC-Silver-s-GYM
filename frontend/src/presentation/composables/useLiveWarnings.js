import { computed, reactive } from 'vue';

const FLASH_MS = 2500;

/**
 * Avisos por campo que siguen a lo que se escribe. Cada regla devuelve el aviso
 * para el valor actual ('' si es valido) y solo se muestra en campos ya tocados.
 * `flash` muestra un momento el aviso de una tecla bloqueada.
 */
export const useLiveWarnings = (rules) => {
  const touched = reactive({});
  const flashes = reactive({});
  const timers = {};

  const warnings = computed(() => Object.fromEntries(Object.keys(rules).map((key) => [
    key,
    flashes[key] || (touched[key] ? rules[key]() || '' : ''),
  ])));

  const clearFlash = (key) => {
    clearTimeout(timers[key]);
    flashes[key] = '';
  };
  const touch = (key) => {
    clearFlash(key);
    touched[key] = true;
  };
  const flash = (key, message) => {
    clearTimeout(timers[key]);
    flashes[key] = message;
    timers[key] = setTimeout(() => { flashes[key] = ''; }, FLASH_MS);
  };
  const touchAll = () => Object.keys(rules).forEach(touch);
  const reset = () => Object.keys(rules).forEach((key) => {
    clearFlash(key);
    touched[key] = false;
  });
  // Un campo tocado se marca segun su aviso; uno sin tocar, segun el ultimo envio.
  const isInvalid = (key, fallback = false) => Boolean(warnings.value[key] || (!touched[key] && fallback));

  return { warnings, touch, flash, touchAll, reset, isInvalid };
};
