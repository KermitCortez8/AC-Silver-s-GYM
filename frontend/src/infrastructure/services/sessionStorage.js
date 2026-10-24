import { decodeJWT } from '../../domain/utils/authRules.js';

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

export const saveAuthSession = (user, token, expiresIn) => {
  try {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
    localStorage.setItem(AUTH_TOKEN_KEY, token || '');
    
    if (typeof expiresIn === 'number' && expiresIn > 0) {
      const expiryTime = Date.now() + expiresIn * 1000;
      localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
    } else if (token) {
      const payload = decodeJWT(token);
      if (Number.isFinite(payload?.exp)) {
        localStorage.setItem(TOKEN_EXPIRY_KEY, String(payload.exp * 1000));
      } else {
        localStorage.removeItem(TOKEN_EXPIRY_KEY);
      }
    }
  } catch (error) {
    console.error('Error al guardar sesión:', error);
  }
};

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

export const clearAuthStorage = () => {
  try {
    localStorage.removeItem(AUTH_USER_KEY);
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  } catch (error) {
    console.error('Error al limpiar almacenamiento:', error);
  }
};
