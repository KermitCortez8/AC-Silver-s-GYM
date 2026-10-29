/** Reglas de autenticación sin acceso a almacenamiento ni red. */
import { emailError } from './formValidation.js';

export const isValidEmail = (email) => {
  return !emailError(email, { account: false });
};

export const getUserRole = (email) => {
  // Los emails que terminan en @urp.edu.pe son admins
  if (!email) {
    return 'user';
  }

  return email.endsWith('@urp.edu.pe') ? 'admin' : 'user';
};

export const formatUserData = (googleUserData) => {
  const normalizedEmail = googleUserData.email || googleUserData.correo || '';
  const normalizedId = googleUserData.id_usuario || googleUserData.id || googleUserData.sub || normalizedEmail;
  return {
    id: normalizedId,
    id_usuario: googleUserData.id_usuario || normalizedId,
    id_cliente: googleUserData.id_cliente || null,
    email: normalizedEmail,
    correo: normalizedEmail,
    telefono: googleUserData.telefono || '',
    dni: googleUserData.dni || '',
    name: googleUserData.name || '',
    picture: googleUserData.picture || '',
    givenName: googleUserData.given_name || '',
    familyName: googleUserData.family_name || '',
    role: googleUserData.role || 'user',
    loginTime: new Date().toISOString(),
  };
};

export const isValidUser = (user) => {
  const userEmail = user?.email || user?.correo;
  return (
    user &&
    typeof user === 'object' &&
    (user.id || user.id_usuario) &&
    userEmail &&
    isValidEmail(userEmail)
  );
};

export const decodeJWT = (token) => {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Token inválido');
    }

    let decoded = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padding = decoded.length % 4;
    if (padding) {
      decoded += '='.repeat(4 - padding);
    }

    const decoded_bytes = atob(decoded);
    return JSON.parse(decoded_bytes);
  } catch (error) {
    console.error('Error al decodificar token:', error);
    return null;
  }
};

export const createDefaultMembership = (user) => ({
  membershipStatus: user?.role === 'admin' ? 'Administrador' : 'EN_TRAMITE',
  plan: user?.role === 'admin' ? 'Acceso total' : 'Mensual',
  validity: user?.role === 'admin' ? 'Sin vencimiento' : '30 días',
});
