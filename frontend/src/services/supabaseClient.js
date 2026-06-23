import { createClient } from '@supabase/supabase-js';
import { APP_CONFIG } from '../config/appConfig';

export const isSupabaseEnabled = Boolean(APP_CONFIG.supabaseUrl && APP_CONFIG.supabaseAnonKey);
export const useSupabaseAuth = isSupabaseEnabled && APP_CONFIG.authMode === 'supabase';

export const supabase = isSupabaseEnabled
  ? createClient(APP_CONFIG.supabaseUrl, APP_CONFIG.supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    })
  : null;
