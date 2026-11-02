/** Conserva los ceros iniciales y limpia la entrada antes de que v-model la reciba. */
const handlers = new WeakMap();

export const vDigits = {
  beforeMount(element) {
    const handleInput = () => {
      element.value = element.value.replace(/\D/g, '').slice(0, element.maxLength);
    };
    handlers.set(element, handleInput);
    element.addEventListener('input', handleInput, true);
  },
  unmounted(element) {
    element.removeEventListener('input', handlers.get(element), true);
    handlers.delete(element);
  },
  getSSRProps: () => ({}),
};
