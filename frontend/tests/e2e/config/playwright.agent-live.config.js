import { defineConfig, devices } from '@playwright/test'
import { fileURLToPath } from 'node:url'

const frontend = fileURLToPath(new URL('../../../', import.meta.url))
const backend = fileURLToPath(new URL('../../../../backend/', import.meta.url))
const python = process.platform === 'win32' ? '.venv\\Scripts\\python.exe' : '.venv/bin/python'

// Opt-in: solo la app de lectura y el catálogo público real de Supabase.
export default defineConfig({
  testDir: '../catalogo',
  fullyParallel: false,
  workers: 1,
  outputDir: '../../../.artifacts/playwright/catalogo/resultados',
  reporter: [['list'], ['html', { open: 'never', outputFolder: '../../../.artifacts/playwright/catalogo/informe' }]],
  use: { baseURL: 'http://127.0.0.1:4173', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `${python} -B -m uvicorn app.agent_readonly_app:app --host 127.0.0.1 --port 8765`,
      cwd: backend,
      url: 'http://127.0.0.1:8765/openapi.json',
      reuseExistingServer: false,
    },
    {
      command: 'npm run dev -- --config tests/e2e/config/vite.agent-readonly.config.js --host 127.0.0.1 --port 4173 --strictPort',
      cwd: frontend,
      url: 'http://127.0.0.1:4173/',
      reuseExistingServer: false,
    },
  ],
})
