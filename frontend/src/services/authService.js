import { APP_CONFIG } from '../config/appConfig';
import { decodeJWT, formatUserData, isValidUser } from '../utils/authUtils';
import { apiPost } from './apiClient';
import { supabase, useSupabaseAuth } from './supabaseClient';

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
  if (useSupabaseAuth) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: String(correo || '').trim(),
      password,
    });

    if (error) {
      throw new Error(error.message || 'Correo o contrasena incorrectos');
    }

    return createSupabaseAuthResult(data.session, data.user);
  }

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

export const createSupabaseAuthResult = (session, authUser) => {
  const supabaseUser = authUser || session?.user;

  if (!session?.access_token || !supabaseUser?.email) {
    throw new Error('Supabase no devolvio una sesion valida');
  }

  const metadata = supabaseUser.user_metadata || {};
  const user = formatUserData({
    id: supabaseUser.id,
    sub: supabaseUser.id,
    email: supabaseUser.email,
    name: metadata.name || metadata.nombre || supabaseUser.email,
    telefono: metadata.telefono || '',
    dni: metadata.dni || '',
    role: metadata.role || undefined,
    picture: metadata.avatar_url || '',
  });

  return {
    user,
    token: session.access_token,
    expiresIn: session.expires_in || 60 * 60,
    source: 'supabase',
  };
};

export const getSupabaseSessionCredentials = async () => {
  if (!useSupabaseAuth) {
    return null;
  }

  const { data, error } = await supabase.auth.getSession();

  if (error || !data?.session) {
    return null;
  }

  return createSupabaseAuthResult(data.session);
};

export const registerWithSupabase = async ({ correo, password, nombre, telefono, dni }) => {
  if (!useSupabaseAuth) {
    return null;
  }

  const { data, error } = await supabase.auth.signUp({
    email: String(correo || '').trim(),
    password,
    options: {
      data: {
        name: nombre,
        nombre,
        telefono,
        dni,
        role: 'user',
      },
    },
  });

  if (error) {
    throw new Error(error.message || 'No se pudo crear la cuenta en Supabase');
  }

  return {
    needsEmailConfirmation: Boolean(data.user && !data.session),
    credentials: data.session ? createSupabaseAuthResult(data.session, data.user) : null,
  };
};

export const signOutFromSupabase = async () => {
  if (!useSupabaseAuth) {
    return;
  }

  await supabase.auth.signOut();
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
