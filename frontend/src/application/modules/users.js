/** Estado y operaciones del módulo users. */
import { normalizeUser } from '../../domain/utils/gymRules.js';

/** usersRepository: save(payload, token) y remove(id, token) devuelven datos o lanzan un error. */
export const createUsersModule = (ctx, usersRepository) => {
  const mergeUser = (saved) => {
    const normalized = normalizeUser(saved);
    const index = ctx.users.value.findIndex((entry) => String(entry.id_usuario) === String(normalized.id_usuario));
    if (index >= 0) {
      ctx.users.value[index] = normalized;
    } else {
      ctx.users.value.unshift(normalized);
    }
    return normalized;
  };

  const upsertUser = async (payload) => {
    const existingUser = ctx.users.value.find((entry) => String(entry.id_usuario) === String(payload.id_usuario || '').trim());
    const userPayload = {
      ...(existingUser?.id_usuario ? { id_usuario: existingUser.id_usuario } : {}),
      nombre: String(payload.nombre || existingUser?.nombre || '').trim(),
      correo: String(payload.correo || payload.email || existingUser?.correo || '').trim(),
      telefono: String(payload.telefono || existingUser?.telefono || '').trim(),
      dni: String(payload.dni || existingUser?.dni || '').trim(),
      password: String(payload.password || payload.contrasena || '').trim(),
      rol: payload.rol || existingUser?.rol || 'staff',
    };

    if (ctx.apiBase) {
      if (payload.id_usuario) {
        userPayload.id_usuario = String(payload.id_usuario).trim();
      }

      const saved = await upsertUserToServer(userPayload);
      return mergeUser(saved);
    }

    const nextId = userPayload.id_usuario || `SGUS${String(ctx.users.value.length + 1).padStart(3, '0')}`;
    return mergeUser({ ...userPayload, id_usuario: nextId });
  };

  const deleteUser = async (idUsuario) => {
    const normalizedId = String(idUsuario || '').trim();
    if (!normalizedId) {
      throw new Error('Usuario no encontrado');
    }

    if (ctx.apiBase) {
      await deleteUserFromServer(normalizedId);
    }

    ctx.users.value = ctx.users.value.filter((user) => String(user.id_usuario) !== normalizedId);
  };

  const upsertUserToServer = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    return usersRepository.save(payload, ctx.authStore.token);
  };

  const deleteUserFromServer = async (idUsuario) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    return usersRepository.remove(idUsuario, ctx.authStore.token);
  };

  return { upsertUser, deleteUser, upsertUserToServer, deleteUserFromServer };
};
