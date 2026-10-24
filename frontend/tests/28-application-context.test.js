import assert from "node:assert/strict";
import { before, after, test } from "node:test";
import { createPinia, setActivePinia } from "pinia";
import { createServer } from "vite";
import { fileURLToPath } from "node:url";

let server,
  installServices,
  getApplicationServices,
  configureApplicationServices;
let createBackendGateway, useAppResources, useAuthStore, useGymStore;

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL("..", import.meta.url)),
    configFile: false,
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  });
  ({ installServices } = await server.ssrLoadModule("/src/bootstrap.js"));
  ({ getApplicationServices, configureApplicationServices } =
    await server.ssrLoadModule("/src/application/ports/services.js"));
  ({ createBackendGateway } = await server.ssrLoadModule(
    "/src/application/services/backendGateway.js",
  ));
  ({ useAppResources } = await server.ssrLoadModule(
    "/src/application/services/appResources.js",
  ));
  ({ useAuthStore } = await server.ssrLoadModule(
    "/src/application/stores/authStore.js",
  ));
  ({ useGymStore } = await server.ssrLoadModule(
    "/src/application/stores/gymStore.js",
  ));
});
after(async () => {
  await server?.close();
});

const application = (name, http = {}) => {
  const pinia = createPinia();
  const config = { app: { authApiBaseUrl: `/${name}`, appName: name } };
  const services = installServices(pinia, {
    config,
    http: { apiGet: async () => name, ...http },
    auth: { disableGoogleAutoSelect: () => {} },
    session: { clearAuthStorage: () => {}, getAuthSession: () => ({}), saveAuthSession: () => {} },
  });
  setActivePinia(pinia);
  return {
    pinia,
    services,
    config,
    gateway: createBackendGateway(),
    resources: useAppResources(),
  };
};

test("configuring another application cannot redirect existing consumers or mutate their configuration", async () => {
  const first = application("first");
  const second = application("second");
  first.config.app.appName = "mutated externally";
  assert.equal(first.resources.APP_CONFIG.appName, "first");
  assert.equal(second.resources.APP_CONFIG.appName, "second");
  assert.equal(await first.gateway.apiGet("/demo"), "first");
  assert.equal(await second.gateway.apiGet("/demo"), "second");
  assert.equal(getApplicationServices(first.pinia), first.services);
  assert.throws(
    () => configureApplicationServices(second.services, first.pinia),
    /ya están instalados/,
  );
});

test("pending requests follow their own application session even after another session changes", async () => {
  let resolve;
  const first = application("first", {
    apiGet: () =>
      new Promise((done) => {
        resolve = done;
      }),
  });
  const firstAuth = useAuthStore(first.pinia);
  const second = application("second");
  // El propietario explícito prevalece aunque otra aplicación esté activa.
  const gateway = createBackendGateway(first.services);
  const pending = gateway.apiGet("/demo");
  await useAuthStore(second.pinia).signOut();
  resolve("first response");
  assert.equal(await pending, "first response");
  const obsolete = gateway.apiGet("/demo");
  const rejection = assert.rejects(obsolete, /sesión ha cambiado/);
  await firstAuth.signOut();
  resolve("obsolete response");
  await rejection;
});

test("two gym stores synchronize through their own transports after both applications are installed", async () => {
  const calls = [];
  const transport = (name) => ({
    apiGet: async (path) => {
      calls.push([name, path]);
      return [{ id_pm: 1, nombre_plan: name, duracion: "30 dias", precio: 79 }];
    },
  });
  const first = application("first", transport("first"));
  const firstAuth = useAuthStore(first.pinia);
  firstAuth.token = "first-token";
  firstAuth.userRole = "admin";
  const firstGym = useGymStore(first.pinia);
  const second = application("second", transport("second"));
  const secondAuth = useAuthStore(second.pinia);
  secondAuth.token = "second-token";
  secondAuth.userRole = "admin";
  const secondGym = useGymStore(second.pinia);
  await Promise.all([
    firstGym.fetchFromBackend({ section: "plans" }),
    secondGym.fetchFromBackend({ section: "plans" }),
  ]);
  assert.equal(firstGym.planCatalog[0].name, "first");
  assert.equal(secondGym.planCatalog[0].name, "second");
  assert.deepEqual(calls.sort(), [
    ["first", "/planes-membresia"],
    ["second", "/planes-membresia"],
  ]);
});
