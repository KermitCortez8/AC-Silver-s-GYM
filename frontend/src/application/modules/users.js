/** Estado y operaciones del módulo users. */
import { normalizeUser } from '../../domain/utils/gymRules.js';
import { backendRequest } from '../services/backendGateway.js';

export const createUsersModule = (ctx) => {
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
      const normalized = normalizeUser(saved);
      const index = ctx.users.value.findIndex((entry) => String(entry.id_usuario) === String(normalized.id_usuario));
      if (index >= 0) {
        ctx.users.value[index] = normalized;
      } else {
        ctx.users.value.unshift(normalized);
      }
      ctx.persist();
      return normalized;
    }

    const nextId = userPayload.id_usuario || `SGUS${String(ctx.users.value.length + 1).padStart(3, '0')}`;
    const normalized = normalizeUser({ ...userPayload, id_usuario: nextId });
    const index = ctx.users.value.findIndex((entry) => String(entry.id_usuario) === String(normalized.id_usuario));
    if (index >= 0) {
      ctx.users.value[index] = normalized;
    } else {
      ctx.users.value.unshift(normalized);
    }
    ctx.persist();
    return normalized;
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
    ctx.persist();
  };

  const upsertUserToServer = async (payload) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const res = await backendRequest(`${ctx.apiBase}/usuarios`, { method: 'POST', headers: ctx._authHeaders(), body: JSON.stringify(payload) });
    if (!res.ok) throw new Error('Error al guardar usuario');
    return res.json();
  };

  const deleteUserFromServer = async (idUsuario) => {
    if (!ctx.apiBase) throw new Error('No hay backend configurado');
    const res = await backendRequest(`${ctx.apiBase}/usuarios/${encodeURIComponent(idUsuario)}`, { method: 'DELETE', headers: ctx._authHeaders() });
    if (!res.ok && res.status !== 204) throw new Error('Error al eliminar usuario');
    return true;
  };

  return { upsertUser, deleteUser, upsertUserToServer, deleteUserFromServer };
};
