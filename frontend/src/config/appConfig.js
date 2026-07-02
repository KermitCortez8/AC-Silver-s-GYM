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
  authApiBaseUrl: normalizeBaseUrl(env.VITE_AUTH_API_BASE_URL || '/api'),
  supabaseUrl: env.VITE_SUPABASE_URL || 'https://egakogbdxywyzshdetzh.supabase.co',
  supabaseAnonKey:
    env.VITE_SUPABASE_ANON_KEY ||
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVnYWtvZ2JkeHl3eXpzaGRldHpoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0OTg2NzksImV4cCI6MjA5MzA3NDY3OX0.nVX3Y8RUCDtKSNfOqEOjxZaIsFvQXof1KyG-7tB4gxM',
};
