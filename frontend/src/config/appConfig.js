const env = import.meta.env;

export const APP_CONFIG = {
  appName: env.VITE_APP_NAME || "AC Silver's GYM",
  googleClientId:
    env.VITE_GOOGLE_CLIENT_ID || '439271295964-0jkl1secjabmmor8k0qr5sai48bkicj2.apps.googleusercontent.com',
  authApiBaseUrl: (env.VITE_AUTH_API_BASE_URL || '').replace(/\/$/, ''),
  authMode: env.VITE_AUTH_MODE || (env.VITE_AUTH_API_BASE_URL ? 'backend' : 'direct'),
  enableDemoLogin: env.VITE_ENABLE_DEMO_LOGIN !== 'false',
  supportEmail: env.VITE_SUPPORT_EMAIL || 'soporte@acsilversgym.com',
};
