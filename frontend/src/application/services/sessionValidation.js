// La sesión se valida en el servidor; solo se reutiliza una respuesta reciente
// para el mismo token. Los errores nunca se guardan como resultados válidos.
export const createSessionValidator = (loadUser, { maxAge = 30_000, now = Date.now } = {}) => {
  let current = null;

  return {
    clear() { current = null; },
    validate(token, { force = false } = {}) {
      if (current?.token === token) {
        if (current.pending) return current.pending;
        if (!force && now() - current.checkedAt < maxAge) return Promise.resolve(current.user);
      }
      const entry = { token, checkedAt: -Infinity, pending: null, user: null };
      current = entry;
      entry.pending = Promise.resolve().then(() => loadUser(token)).then((user) => {
        entry.user = user;
        entry.checkedAt = now();
        return user;
      }).finally(() => { entry.pending = null; });
      return entry.pending;
    },
  };
};
