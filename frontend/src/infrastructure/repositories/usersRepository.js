/** Traduce las operaciones de usuarios al contrato HTTP del backend. */
export const createUsersRepository = ({ request }) => ({
  save: (payload, token) => request('/usuarios', {
    method: 'POST',
    body: JSON.stringify(payload),
  }, token),

  remove: async (idUsuario, token) => {
    await request(`/usuarios/${encodeURIComponent(idUsuario)}`, {
      method: 'DELETE',
    }, token);
    return true;
  },
});
