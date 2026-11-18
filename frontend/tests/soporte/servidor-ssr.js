import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';

export const crearServidorSsr = ({ componentesVue = false } = {}) => createServer({
  root: fileURLToPath(new URL('../..', import.meta.url)),
  configFile: false,
  plugins: componentesVue ? [vue()] : [],
  // Estas suites cargan módulos SSR. El optimizador del cliente escribiría
  // la misma caché de Vite desde varios procesos de node --test.
  optimizeDeps: { noDiscovery: true },
  server: { middlewareMode: true, hmr: false, ws: false, watch: null },
});
