const env = import.meta.env;

const normalizeBaseUrl = (value) => {
  const base = String(value || '').trim().replace(/\/$/, '');

  if (!base) {
    return '';
  }

  if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(base)) {
    return base.replace(/^https:/i, 'http:');
  }

  return base;
};

export const APP_CONFIG = {
  appName: env.VITE_APP_NAME || "AC Silver's GYM",
  googleClientId:
    env.VITE_GOOGLE_CLIENT_ID || '439271295964-0jkl1secjabmmor8k0qr5sai48bkicj2.apps.googleusercontent.com',
  authApiBaseUrl: normalizeBaseUrl(env.VITE_AUTH_API_BASE_URL || '/api'),
  authMode: env.VITE_AUTH_MODE || 'supabase',
  supabaseUrl: env.VITE_SUPABASE_URL || 'https://egakogbdxywyzshdetzh.supabase.co',
  supabaseAnonKey: env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_vnZHsG2cZmcVEmKCOPxpdw_4T0dMUQP',
  enableDemoLogin: env.VITE_ENABLE_DEMO_LOGIN !== 'false',
  supportEmail: env.VITE_SUPPORT_EMAIL || 'soporte@acsilversgym.com',
};
