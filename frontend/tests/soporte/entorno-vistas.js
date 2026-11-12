import { before, after } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createSSRApp, h } from 'vue';
import { renderToString } from 'vue/server-renderer';
import { createPinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';

let server, installServices, useGymStore, useRestTimer;

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL('../..', import.meta.url)),
    configFile: false,
    plugins: [vue()],
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  });
  ({ installServices } = await server.ssrLoadModule('/src/bootstrap.js'));
  ({ useGymStore } = await server.ssrLoadModule(
    '/src/application/stores/gymStore.js',
  ));
  ({ useRestTimer } = await server.ssrLoadModule(
    '/src/presentation/composables/trainer/useRestTimer.js',
  ));
});

after(async () => {
  await server?.close();
});

const view = async (filename, { attendance = {}, prepare } = {}) => {
  const { default: View } = await server.ssrLoadModule(
    `/src/presentation/views/${filename}.vue`,
  );
  const pinia = createPinia();
  installServices(pinia, { attendance });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: View }],
  });
  await router.push('/');
  const instances = [];
  let setup;
  const app = createSSRApp({ render: () => h(View) });
  app.use(pinia).use(router);
  app.mixin({
    created() {
      instances.push(this.$);
      if (this.$.type === View) {
        setup = this.$.setupState;
        prepare?.(setup, useGymStore(pinia));
      }
    },
  });
  const context = {};
  const html = await renderToString(app, context);
  return {
    setup,
    gym: useGymStore(pinia),
    html,
    dialogs: Object.values(context.teleports || {}).join(''),
    child: (name) =>
      instances.find((instance) => instance.type.__name === name)?.setupState,
    dispose: () => instances.forEach((instance) => instance.scope.stop()),
  };
};

const client = (dni) => ({
  fecha: '2026-10-24',
  cliente: { nombre: 'Ana', dni, estado: 'ACTIVO' },
  membresia: { fecha_fin: '2026-11-24' },
  horarios: [],
  general: { puede_entrar: true },
});

const summary = {
  fecha: '2026-10-24',
  entradas: 2,
  salidas: 1,
  dentro: 1,
  capacidad: 20,
  disponibles: 19,
  pendientes: [],
};

const enrollment = {
  id_matricula: 7,
  id_rutina: 1,
  servicio: 'fitness',
  estado: 'ACTIVA',
  dia: 'sabado',
  hora_inicio: '10:00',
  hora_fin: '11:00',
  rutina_nombre: 'Fuerza',
};

const routines = [
  {
    id_rutina: 1,
    servicio: 'fitness',
    nombre_rutina: 'Fuerza',
    ejercicios: [
      {
        id_ejercicio: 1,
        nombre_ejercicio: 'Sentadilla',
        series: 3,
        peso_sugerido_kg: 0,
      },
    ],
  },
  { id_rutina: 2, servicio: 'fitness', nombre_rutina: 'Resistencia' },
  { id_rutina: 3, servicio: 'baile', nombre_rutina: 'Salsa' },
];

export { server, useRestTimer, view, client, summary, enrollment, routines };
