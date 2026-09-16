import assert from "node:assert/strict";
import {
  deliveryError,
  idempotencyKey,
  type MailSettings,
  ResendSender,
  scheduleMail,
} from "../functions/schedule-emails/email.ts";
import {
  createHandler,
  processBatch,
  readSettings,
  type Repository,
} from "../functions/schedule-emails/worker.ts";

const settings: MailSettings = {
  resendApiKey: "re_private",
  emailFrom: "onboarding@resend.dev",
  senderName: "Silver Gym Surco",
  frontendUrl: "https://gym.vercel.app",
  supabaseUrl: "https://gym.supabase.co",
};
const context = {
  event_type: "enrollment" as const,
  nombre: "Ana",
  correo: "client@example.com",
  servicio: "fitness",
  dia: "lunes",
  hora_inicio: "09:00",
  hora_fin: "10:00",
  class_start: null,
};

Deno.test("HTTPS entrega al destinatario original con clave estable por proyecto y evento", async () => {
  const calls: RequestInit[] = [];
  const fetcher: typeof fetch = (_url, init) => {
    assert.equal(_url, "https://api.resend.com/emails");
    calls.push(init!);
    return Promise.resolve(Response.json({ id: "resend-id" }));
  };
  const sender = new ResendSender(settings, fetcher);
  const mail = scheduleMail(settings, context);
  assert.equal(await sender.send(mail, "enrollment/12"), "resend-id");
  await sender.send(mail, "enrollment/12");
  const body = JSON.parse(calls[0].body as string);
  assert.deepEqual(body.to, [context.correo]);
  assert.equal(body.from, "Silver Gym Surco <onboarding@resend.dev>");
  assert.equal(
    new Headers(calls[0].headers).get("Idempotency-Key"),
    new Headers(calls[1].headers).get("Idempotency-Key"),
  );
  assert.notEqual(
    await idempotencyKey(settings, "enrollment/12"),
    await idempotencyKey(settings, "enrollment/13"),
  );
  assert.notEqual(
    await idempotencyKey(settings, "enrollment/12"),
    await idempotencyKey({
      ...settings,
      supabaseUrl: "https://other.supabase.co",
    }, "enrollment/12"),
  );
});

Deno.test("rechazos HTTP no exponen cuerpos ni credenciales", async () => {
  for (const status of [401, 403, 409, 422, 429, 500]) {
    const sender = new ResendSender(
      settings,
      () =>
        Promise.resolve(
          new Response("re_private client@example.com", { status }),
        ),
    );
    await assert.rejects(
      () => sender.send(scheduleMail(settings, context), "enrollment/12"),
      (error: unknown) => {
        assert.match(deliveryError(error), /Resend/);
        assert.doesNotMatch(
          deliveryError(error),
          /re_private|client@example.com/,
        );
        return true;
      },
    );
  }
});

Deno.test("respuesta sin id no se considera enviada", async () => {
  const sender = new ResendSender(
    settings,
    () => Promise.resolve(Response.json({})),
  );
  await assert.rejects(
    () => sender.send(scheduleMail(settings, context), "enrollment/12"),
    /no confirmó/,
  );
});

Deno.test("fallo de API mantiene aviso pendiente y detiene el lote", async () => {
  const outcomes: unknown[] = [];
  let claims = 0;
  const repo: Repository = {
    check: async () => {},
    enqueue: async () => 1,
    claim: async () => {
      claims++;
      return { event_key: "enrollment/12", claim_token: "token", attempts: 1 };
    },
    context: async () => context,
    finish: async (_job, outcome) => {
      outcomes.push(outcome);
    },
  };
  const sender = new ResendSender(
    settings,
    () => Promise.resolve(new Response("private", { status: 429 })),
  );
  const counts = await processBatch(settings, repo, sender);
  assert.equal(counts.sent, 0);
  assert.equal(counts.retried, 1);
  assert.equal(claims, 1);
  assert.match(JSON.stringify(outcomes), /límite/);
  assert.doesNotMatch(JSON.stringify(outcomes), /deliveryId|private/);
});

Deno.test("dry run no envía ni afirma comprobar entrega remota", async () => {
  const env: Record<string, string> = {
    RESEND_API_KEY: "re_private",
    EMAIL_FROM: settings.emailFrom,
    SUPABASE_URL: settings.supabaseUrl,
    SUPABASE_SERVICE_ROLE_KEY: "db-key",
    FRONTEND_PUBLIC_URL: settings.frontendUrl,
    SCHEDULE_CRON_SECRET: "x".repeat(48),
  };
  const repo: Repository = {
    check: async () => {},
    enqueue: async () => {
      throw new Error("No encolar en dry run");
    },
    claim: async () => {
      throw new Error("No reservar en dry run");
    },
    context: async () => null,
    finish: async () => {},
  };
  const handler = createHandler({
    env: (name) => env[name],
    repository: () => repo,
    sender: () =>
      new ResendSender(settings, () => {
        throw new Error("No hacer solicitudes a Resend");
      }),
  });
  const response = await handler(
    new Request("https://example.com", {
      method: "POST",
      headers: { Authorization: `Bearer ${env.SCHEDULE_CRON_SECRET}` },
      body: JSON.stringify({ dry_run: true }),
    }),
  );
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {
    ok: true,
    dry_run: true,
    database: "ok",
    resend: "configured_not_sent",
    sent: 0,
  });
  const denied = await handler(
    new Request("https://example.com", { method: "POST", body: "{}" }),
  );
  assert.equal(denied.status, 401);
});

Deno.test("configuración usa Resend y rechaza clave ausente", () => {
  const env: Record<string, string> = {
    RESEND_API_KEY: "re_private",
    SUPABASE_URL: settings.supabaseUrl,
    SUPABASE_SERVICE_ROLE_KEY: "db-key",
    FRONTEND_PUBLIC_URL: settings.frontendUrl,
  };
  assert.equal(
    readSettings((name) => env[name]).emailFrom,
    "onboarding@resend.dev",
  );
  delete env.RESEND_API_KEY;
  assert.throws(() => readSettings((name) => env[name]), /RESEND_API_KEY/);
});
