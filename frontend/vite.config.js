import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

const normalizeBackendTarget = (value) => {
  const target = String(value || 'http://localhost:8000').trim().replace(/\/$/, '')

  if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(target)) {
    return target.replace(/^https:/i, 'http:')
  }

  return target
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],
    server: {
      proxy: {
        '/api': {
          target: normalizeBackendTarget(env.VITE_BACKEND_URL),
          changeOrigin: true,
        },
      },
    },
  }
})
