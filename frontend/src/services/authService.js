import { APP_CONFIG } from '../config/appConfig';
import { decodeJWT, formatUserData, isValidUser } from '../utils/authUtils';
import { apiPost } from './apiClient';

let googleScriptPromise = null;

const getExpirySeconds = (payload) => {
  if (!payload?.exp) {
    return 60 * 60;
  }

  const expiresIn = Math.floor(Number(payload.exp) - Date.now() / 1000);
  return Math.max(expiresIn, 60);
};

export const loadGoogleIdentityScript = () => {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Google Identity Services requiere navegador'));
  }

  if (window.google?.accounts?.id) {
    return Promise.resolve(window.google);
  }

  if (googleScriptPromise) {
    return googleScriptPromise;
  }

  googleScriptPromise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector('script[data-google-identity="true"]');

    if (existingScript) {
      existingScript.addEventListener('load', () => resolve(window.google));
      existingScript.addEventListener('error', () => reject(new Error('No se pudo cargar Google Identity Services')));
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.dataset.googleIdentity = 'true';
    script.onload = () => resolve(window.google);
    script.onerror = () => reject(new Error('No se pudo cargar Google Identity Services'));
    document.head.appendChild(script);
  });

  return googleScriptPromise;
};

export const authenticateWithGoogleCredential = async (credential) => {
  if (!credential) {
    throw new Error('No se recibió credencial de Google');
  }

  const decoded = decodeJWT(credential);
  if (!decoded || !decoded.email) {
    throw new Error('No se pudo decodificar la credencial de Google');
  }

  const user = formatUserData(decoded);

  if (!isValidUser(user)) {
    throw new Error('Datos de usuario inválidos');
  }

  const expiresIn = getExpirySeconds(decoded);

  if (APP_CONFIG.authApiBaseUrl) {
    const result = await apiPost('/auth/google', {
      credential,
      profile: user,
    });

    return {
      user: result.user || user,
      token: result.token || credential,
      expiresIn: result.expiresIn || expiresIn,
      source: 'backend',
    };
  }

  return {
    user,
    token: credential,
    expiresIn,
    source: 'google',
  };
};

export const authenticateWithPassword = async ({ correo, password }) => {
  const result = await apiPost('/auth/password', {
    correo,
    password,
  });

  return {
    user: result.user,
    token: result.token,
    expiresIn: result.expiresIn || 60 * 60,
    source: 'backend',
  };
};

export const createDemoCredentials = (role = 'user') => {
  const normalizedRole = role === 'admin' ? 'admin' : 'user';
  const domain = normalizedRole === 'admin' ? '@urp.edu.pe' : '@ejemplo.com';

  const profile = {
    sub: `demo-${normalizedRole}-001`,
    email: normalizedRole === 'admin' ? 'admin@urp.edu.pe' : 'usuario@ejemplo.com',
    name: normalizedRole === 'admin' ? 'Admin del Sistema' : 'Usuario de Prueba',
    picture: '',
    given_name: normalizedRole === 'admin' ? 'Admin' : 'Usuario',
    family_name: normalizedRole === 'admin' ? 'Sistema' : 'Prueba',
  };

  const token = btoa(JSON.stringify(profile)).replace(/=/g, '');

  return {
    user: formatUserData(profile),
    token,
    expiresIn: 60 * 60,
    source: 'demo',
  };
};
