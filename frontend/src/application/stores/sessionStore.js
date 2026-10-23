/** Generación de sesión compartida sin depender de autenticación ni de HTTP. */
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useSessionStore = defineStore('session-lifecycle', () => {
  const revision = ref(0);
  const invalidate = () => { revision.value += 1; };
  return { revision, invalidate };
});
