import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Demo local: solo la API pública del asistente, sin cargar archivos .env del frontend.
export default defineConfig({
  plugins: [vue()],
  envDir: false,
  server: {
    headers: {
      'Content-Security-Policy': "default-src 'self' data: blob:; connect-src 'self' ws://127.0.0.1:4173; img-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; frame-src 'none';",
    },
    proxy: {
      '/api': { target: 'http://127.0.0.1:8765', changeOrigin: true },
    },
  },
})
