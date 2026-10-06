// Comparte consultas y guarda únicamente respuestas correctas para la misma sesión.
export const createResourceCache = ({
  maxAge = 30_000,
  now = () => Date.now(),
} = {}) => {
  let currentScope = '';
  const entries = new Map();
  return {
    load(scope, key, fetchResource, { force = false } = {}) {
      if (scope !== currentScope) {
        currentScope = scope;
        entries.clear();
      }
      const previous = entries.get(key);
      if (previous?.pending) {
        if (!force) return previous.pending;
        // Consultar después de una carga anterior evita sobrescribir un cambio guardado.
        return previous.pending
          .catch(() => {})
          .then(() => {
            if (scope !== currentScope)
              throw new Error('La sesión ha cambiado.');
            return this.load(scope, key, fetchResource, { force: true });
          });
      }
      if (!force && previous && now() - previous.updatedAt < maxAge)
        return Promise.resolve();
      const entry = { pending: null, updatedAt: -Infinity };
      entries.set(key, entry);
      entry.pending = Promise.resolve()
        .then(fetchResource)
        .then(() => {
          entry.updatedAt = now();
        })
        .finally(() => {
          entry.pending = null;
        });
      return entry.pending;
    },
  };
};
