// Ejecutar desde la raíz. La copia anterior es opcional y se guarda fuera del repo.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const root = path.resolve('frontend');
const require = createRequire(path.join(root, 'package.json'));
const { createServer } = await import(pathToFileURL(require.resolve('vite')).href);
const baseline = process.env.GYM_VIEWS_BASELINE_DIR;
const servers = [];
process.env.VITE_AUTH_API_BASE_URL = '/api';

for (const [port, original] of [[5174, false], ...(baseline ? [[5175, true]] : [])]) {
  const server = await createServer({
    root,
    configFile: path.join(root, 'vite.config.js'),
    plugins: original ? [{
      name: 'original-views-review',
      enforce: 'pre',
      load(id) {
        if (!id.includes('?') && id.startsWith(path.join(root, 'src/presentation/views/')) && id.endsWith('.vue')) {
          return fs.readFileSync(path.join(baseline, path.basename(id)), 'utf8');
        }
      },
    }] : [],
    server: { host: '127.0.0.1', port, strictPort: true },
  });
  await server.listen();
  servers.push(server);
  console.log(`${original ? 'Original' : 'Refactor'}: http://127.0.0.1:${port}`);
}

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, async () => {
    await Promise.all(servers.map((server) => server.close()));
    process.exit(0);
  });
}
