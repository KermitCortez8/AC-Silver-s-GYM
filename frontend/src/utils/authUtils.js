/**
 * Auth Utilities
 * Funciones auxiliares para autenticación
 */

const AUTH_USER_KEY = 'gym_auth_user';
const AUTH_TOKEN_KEY = 'gym_auth_token';
const TOKEN_EXPIRY_KEY = 'gym_auth_token_expiry';

const safeParse = (value) => {
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value);
  } catch (error) {
    return null;
  }
};

/**
 * Validar formato de email
 */
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Obtener rol del usuario basado en email
 */
export const getUserRole = (email) => {
  // Los emails que terminan en @urp.edu.pe son admins
  if (!email) {
    return 'user';
  }

  return email.endsWith('@urp.edu.pe') ? 'admin' : 'user';
};

/**
 * Formatear datos del usuario
 */
export const formatUserData = (googleUserData) => {
  return {
    id: googleUserData.sub || googleUserData.id,
    email: googleUserData.email || '',
    name: googleUserData.name || '',
    picture: googleUserData.picture || '',
    givenName: googleUserData.given_name || '',
    familyName: googleUserData.family_name || '',
    role: getUserRole(googleUserData.email),
    loginTime: new Date().toISOString(),
  };
};

/**
 * Validar estructura del usuario
 */
export const isValidUser = (user) => {
  return (
    user &&
    typeof user === 'object' &&
    user.id &&
    user.email &&
    isValidEmail(user.email)
  );
};

/**
 * Guardar sesión autenticada en localStorage
 */
export const saveAuthSession = (user, token, expiresIn) => {
  try {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
    localStorage.setItem(AUTH_TOKEN_KEY, token || '');
    
    if (typeof expiresIn === 'number' && expiresIn > 0) {
      const expiryTime = Date.now() + expiresIn * 1000;
      localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
    }
  } catch (error) {
    console.error('Error al guardar sesión:', error);
  }
};

/**
 * Recuperar sesión desde localStorage
 */
export const getAuthSession = () => {
  try {
    const user = localStorage.getItem(AUTH_USER_KEY);
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    const expiryTime = localStorage.getItem(TOKEN_EXPIRY_KEY);

    // Verificar si el token ha expirado
    if (expiryTime && Date.now() > parseInt(expiryTime, 10)) {
      clearAuthStorage();
      return { user: null, token: null };
    }

    return {
      user: safeParse(user),
      token: token || null,
    };
  } catch (error) {
    console.error('Error al recuperar sesión:', error);
    return { user: null, token: null };
  }
};

/**
 * Limpiar almacenamiento de autenticación
 */
export const clearAuthStorage = () => {
  try {
    localStorage.removeItem(AUTH_USER_KEY);
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  } catch (error) {
    console.error('Error al limpiar almacenamiento:', error);
  }
};

/**
 * Decodificar JWT
 */
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
  membershipStatus: user?.role === 'admin' ? 'Administrador' : 'Activa',
  plan: user?.role === 'admin' ? 'Acceso total' : 'Mensual',
  validity: user?.role === 'admin' ? 'Sin vencimiento' : '30 días',
});
