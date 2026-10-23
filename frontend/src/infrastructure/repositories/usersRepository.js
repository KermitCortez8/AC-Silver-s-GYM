/** Traduce las operaciones de usuarios al contrato HTTP del backend. */
export const createUsersRepository = ({ request }) => ({
  save: (payload, token) => request('/usuarios', {
    method: 'POST',
    body: JSON.stringify(payload),
    errorMessage: 'Error al guardar usuario',
  }, token),

  remove: async (idUsuario, token) => {
    await request(`/usuarios/${encodeURIComponent(idUsuario)}`, {
      method: 'DELETE',
      errorMessage: 'Error al eliminar usuario',
    }, token);
    return true;
  },
});
