import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Sin .env ni proxy al backend general: solo habla con la API QA aislada.
export default defineConfig({
  plugins: [vue()],
  envDir: false,
  server: {
    proxy: {
      '/api': { target: 'http://127.0.0.1:8765', changeOrigin: true },
    },
  },
})
