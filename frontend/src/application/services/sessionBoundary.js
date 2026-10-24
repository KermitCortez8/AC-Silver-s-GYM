/** Impide publicar una respuesta que pertenece a una sesión sustituida. */
import { getActivePinia } from 'pinia';
import { useSessionStore } from '../stores/sessionStore.js';

export const captureSession = (pinia = getActivePinia()) => {
  const session = pinia ? useSessionStore(pinia) : null;
  const revision = session?.revision;
  return () => {
    if (session && session.revision !== revision) {
      throw new Error('La sesión ha cambiado.');
    }
  };
};

export const inCurrentSession = async (operation, pinia = getActivePinia()) => {
  const assertCurrent = captureSession(pinia);
  const result = await operation();
  assertCurrent();
  return result;
};

/** Conserva el límite de sesión también con repositorios simulados o sin HTTP. */
export const bindSessionRepository = (repository = {}, token = () => '', pinia = getActivePinia()) => Object.fromEntries(
  Object.entries(repository).map(([name, operation]) => [name,
    (...args) => inCurrentSession(() => operation(...args, token()), pinia),
  ]),
);
