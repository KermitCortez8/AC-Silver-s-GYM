import { defineConfig } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../../../', import.meta.url));
process.env.GYM_QA_KEY ||= randomUUID();
process.env.GYM_BROWSER_REPORT_DIR ||= path.join(root, '.artifacts/browser');

export default defineConfig({
  testDir: './casos',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  timeout: 45000,
  expect: { timeout: 10000 },
  outputDir: path.join(process.env.GYM_BROWSER_REPORT_DIR, 'playwright'),
  reporter: [['list'], ['./reporter.mjs']],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    browserName: 'chromium',
    viewport: { width: 1440, height: 1000 },
    locale: 'es-PE',
    timezoneId: 'America/Lima',
    serviceWorkers: 'block',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'python -B tests/soporte/browser_server.py',
      cwd: path.join(root, 'backend'),
      url: 'http://127.0.0.1:8011/__qa/health',
      env: { GYM_BROWSER_TESTS: '1', GYM_QA_KEY: process.env.GYM_QA_KEY },
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: 'node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 4173 --strictPort',
      cwd: path.join(root, 'frontend'),
      url: 'http://127.0.0.1:4173/login',
      env: {
        VITE_BACKEND_URL: 'http://127.0.0.1:8011', VITE_AUTH_API_BASE_URL: '/api',
        VITE_GOOGLE_CLIENT_ID: 'qa-browser.apps.googleusercontent.com',
        VITE_SUPABASE_URL: '', VITE_SUPABASE_ANON_KEY: '',
      },
      reuseExistingServer: false,
      timeout: 60000,
    },
  ],
});
