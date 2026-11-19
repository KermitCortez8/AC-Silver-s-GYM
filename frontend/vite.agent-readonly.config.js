import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// Demo local: carga la configuración pública del frontend y limita la API a la app de solo lectura.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  let storageOrigin = ''
  try {
    const origin = new URL(env.VITE_SUPABASE_URL).origin
    if (/^https:\/\/[a-z0-9-]+\.supabase\.co$/i.test(origin)) storageOrigin = origin
  } catch { /* Sin almacenamiento público configurado. */ }

  return {
    plugins: [vue()],
    server: {
      headers: {
        'Content-Security-Policy': `default-src 'self' data: blob:; connect-src 'self' ws://127.0.0.1:4173; img-src 'self' data: blob: ${storageOrigin}; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; frame-src 'none';`,
      },
      proxy: {
        '/api': { target: 'http://127.0.0.1:8765', changeOrigin: true },
      },
    },
  }
})
