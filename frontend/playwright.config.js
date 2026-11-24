import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e/simuladas',
  fullyParallel: false,
  outputDir: './.artifacts/playwright/simuladas/resultados',
  reporter: [['list'], ['html', { open: 'never', outputFolder: './.artifacts/playwright/simuladas/informe' }]],
  use: { baseURL: 'http://127.0.0.1:4173', trace: 'on-first-retry' },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4173 --strictPort',
    url: 'http://127.0.0.1:4173/',
    reuseExistingServer: false,
  },
});
