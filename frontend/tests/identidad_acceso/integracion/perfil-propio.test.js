import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { createPinia } from 'pinia';
import { crearServidorSsr } from '../../soporte/servidor-ssr.js';

let server, installServices, useAuthStore;
before(async () => {
  server = await crearServidorSsr();
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ useAuthStore } = await server.ssrLoadModule('/src/application/stores/authStore.js'));
});
after(async () => { await server?.close(); });

const profile = {
  id_usuario: 'SGTRA001', role: 'trainer', name: 'Entrenador QA',
  email: 'entrenador@example.com', telefono: '987654321',
};
const edited = { ...profile, name: 'Entrenador actualizado' };

const createSession = async (http) => {
  const pinia = createPinia();
  let saved = {};
  installServices(pinia, {
    config: { app: { authApiBaseUrl: '/api' } },
    http,
    session: {
      getAuthSession: () => saved,
      clearAuthStorage: () => { saved = {}; },
      saveAuthSession: (user, token) => { saved = { user, token }; },
    },
  });
  const auth = useAuthStore(pinia);
  await auth.signIn('sesion-qa', profile);
  return { auth, getSaved: () => saved };
};

test('el perfil actualizado reemplaza la respuesta anterior sin cambiar de sesión', async () => {
  let finishCheck;
  const { auth, getSaved } = await createSession({
    apiGet: () => new Promise((resolve) => { finishCheck = resolve; }),
    request: async (path, options, token) => {
      assert.equal(path, '/auth/me');
      assert.equal(options.method, 'PATCH');
      assert.deepEqual(JSON.parse(options.body), { nombre: edited.name });
      assert.equal(token, 'sesion-qa');
      return edited;
    },
  });
  const revision = auth.sessionRevision;
  const checking = auth.initializeAuth({ force: true });
  await auth.updateProfile({ nombre: edited.name });
  finishCheck(profile);
  await checking;
  assert.equal(auth.user.name, edited.name);
  assert.equal(getSaved().user.name, edited.name);
  assert.equal(auth.token, 'sesion-qa');
  assert.equal(auth.sessionRevision, revision);
});

test('una respuesta de guardado anterior no modifica una sesión nueva', async () => {
  let savedProfile;
  const { auth, getSaved } = await createSession({
    request: () => new Promise((resolve) => { savedProfile = resolve; }),
  });
  const pending = auth.updateProfile({ nombre: edited.name });
  await auth.signIn('otra-sesion', { ...profile, id_usuario: 'SGTRA002', name: 'Otro entrenador' });
  savedProfile(edited);
  await assert.rejects(pending, /La sesión ha cambiado/);
  assert.equal(auth.user.id_usuario, 'SGTRA002');
  assert.equal(getSaved().token, 'otra-sesion');
});
