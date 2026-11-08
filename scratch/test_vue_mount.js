import { createServer } from 'vite';
import { fileURLToPath } from 'node:url';

async function testMount() {
  try {
    const server = await createServer({
      root: fileURLToPath(new URL('../frontend', import.meta.url)),
      configFile: false,
      server: { middlewareMode: true, hmr: false, ws: false, watch: null },
    });

    console.log('Loading /src/presentation/App.vue...');
    const appModule = await server.ssrLoadModule('/src/presentation/App.vue');
    console.log('App.vue loaded successfully:', Object.keys(appModule));

    console.log('Loading /src/presentation/components/chatbot/ChatLauncher.vue...');
    await server.ssrLoadModule('/src/presentation/components/chatbot/ChatLauncher.vue');
    console.log('ChatLauncher loaded');

    console.log('Loading /src/presentation/components/chatbot/ChatWindow.vue...');
    await server.ssrLoadModule('/src/presentation/components/chatbot/ChatWindow.vue');
    console.log('ChatWindow loaded');

    await server.close();
    console.log('ALL MODULES LOADED WITHOUT ERROR!');
  } catch (err) {
    console.error('ERROR LOADING MODULES:', err);
  }
}

testMount();
