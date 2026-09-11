import {
  containsControls,
  type DeliveryContext,
  emailAddress,
  GmailSender,
  InvalidMail,
  type MailSettings,
  scheduleMail,
  type Sender,
  smtpError,
} from "./email.ts";

type Settings = MailSettings & { supabaseKey: string };
type Env = (name: string) => string | undefined;
export type Job = { event_key: string; claim_token: string; attempts: number };
type Outcome = { deliveryId?: string; error?: string; cancelled?: boolean };
export interface Repository {
  check(): Promise<void>;
  enqueue(): Promise<number>;
  claim(): Promise<Job | null>;
  context(job: Job): Promise<DeliveryContext | null>;
  finish(job: Job, outcome: Outcome): Promise<void>;
}

class ConfigurationError extends Error {}
const value = (env: Env, name: string) => (env(name) ?? "").trim();

export function readSettings(env: Env): Settings {
  const gmailEmail = value(env, "GMAIL_EMAIL");
  const gmailPassword = value(env, "GMAIL_APP_PASSWORD").replace(/\s/g, "");
  const senderName = value(env, "EMAIL_FROM_NAME") || "Silver Gym Surco";
  const frontendUrl = value(env, "FRONTEND_PUBLIC_URL").replace(/\/+$/, "");
  const supabaseUrl = value(env, "SUPABASE_URL").replace(/\/+$/, "");
  const supabaseKey = value(env, "SUPABASE_SERVICE_ROLE_KEY");
  try {
    emailAddress(gmailEmail);
  } catch {
    throw new ConfigurationError(
      "Configura GMAIL_EMAIL en Edge Functions > Secrets.",
    );
  }
  if (!/^[\x21-\x7e]{16}$/.test(gmailPassword)) {
    throw new ConfigurationError(
      "Configura GMAIL_APP_PASSWORD con los 16 caracteres de la contraseña de aplicación.",
    );
  }
  if (containsControls(senderName)) {
    throw new ConfigurationError("Revisa EMAIL_FROM_NAME.");
  }
  for (
    const [name, address] of [["FRONTEND_PUBLIC_URL", frontendUrl], [
      "SUPABASE_URL",
      supabaseUrl,
    ]]
  ) {
    try {
      const parsed = new URL(address);
      if (
        !["https:", "http:"].includes(parsed.protocol) || parsed.username ||
        parsed.password || parsed.hash || parsed.search
      ) throw new Error();
    } catch {
      throw new ConfigurationError(
        `Configura ${name} con la URL completa de la aplicación o proyecto.`,
      );
    }
  }
  if (!supabaseKey) {
    throw new ConfigurationError(
      "Falta SUPABASE_SERVICE_ROLE_KEY en la función.",
    );
  }
  return {
    gmailEmail,
    gmailPassword,
    senderName,
    frontendUrl,
    supabaseUrl,
    supabaseKey,
  };
}

export class SupabaseRepository implements Repository {
  constructor(
    private settings: Settings,
    private fetcher: typeof fetch = fetch,
  ) {}

  private async request(
    path: string,
    method: string,
    body?: unknown,
  ): Promise<unknown> {
    const response = await this.fetcher(
      `${this.settings.supabaseUrl}/rest/v1/${path}`,
      {
        method,
        headers: {
          apikey: this.settings.supabaseKey,
          Authorization: `Bearer ${this.settings.supabaseKey}`,
          "Content-Type": "application/json",
          Prefer: "return=representation",
        },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: AbortSignal.timeout(5000),
      },
    );
    // No devolver cuerpos de PostgREST: pueden incluir datos o credenciales.
    if (!response.ok) {
      await response.body?.cancel();
      throw new Error(
        "No se pudo consultar la cola. Revisa Supabase y la migración 006.",
      );
    }
    return await response.json();
  }

  private rpc(name: string, body: unknown = {}) {
    return this.request(`rpc/${name}`, "POST", body);
  }

  async check(): Promise<void> {
    await this.request(
      "schedule_email_notifications?select=event_key&limit=0",
      "GET",
    );
    // RPC de consulta con una clave inexistente: no reserva ni modifica avisos.
    await this.rpc("schedule_email_delivery_context", {
      p_event_key: `configuration-check/${crypto.randomUUID()}`,
      p_claim_token: crypto.randomUUID(),
    });
  }

  async enqueue(): Promise<number> {
    return Number(await this.rpc("enqueue_due_schedule_reminders"));
  }

  async claim(): Promise<Job | null> {
    const rows = await this.rpc("claim_schedule_email", {
      p_claim_token: crypto.randomUUID(),
      p_event_key: null,
    }) as Job[];
    return rows[0] ?? null;
  }

  async context(job: Job): Promise<DeliveryContext | null> {
    return await this.rpc("schedule_email_delivery_context", {
      p_event_key: job.event_key,
      p_claim_token: job.claim_token,
    }) as DeliveryContext | null;
  }

  async finish(job: Job, outcome: Outcome): Promise<void> {
    const now = new Date();
    let values: Record<string, unknown>;
    if (outcome.cancelled) {
      values = {
        status: "cancelled",
        last_error: "La matrícula, el horario o la fecha ya no corresponden.",
      };
    } else if (outcome.deliveryId) {
      values = {
        status: "sent",
        delivery_id: outcome.deliveryId,
        sent_at: now.toISOString(),
        last_error: null,
      };
    } else {
      const delay = Math.min(
        900,
        30 * 2 ** Math.min(Math.max(job.attempts - 1, 0), 5),
      );
      values = {
        status: "pending",
        last_error: outcome.error,
        available_at: new Date(now.getTime() + delay * 1000).toISOString(),
      };
    }
    const query = new URLSearchParams({
      event_key: `eq.${job.event_key}`,
      claim_token: `eq.${job.claim_token}`,
      status: "eq.processing",
    });
    const rows = await this.request(
      `schedule_email_notifications?${query}`,
      "PATCH",
      {
        ...values,
        claim_token: null,
        locked_until: null,
      },
    ) as unknown[];
    if (!rows.length) {
      throw new Error("No se pudo confirmar el resultado del aviso.");
    }
  }
}

export async function processBatch(
  settings: MailSettings,
  repository: Repository,
  sender: Sender,
  clock: () => number = () => performance.now(),
) {
  // Termina cada invocación; Cron ejecuta la siguiente. El resto queda en la cola.
  const deadline = clock() + 40000;
  const counts = {
    enqueued: await repository.enqueue(),
    sent: 0,
    cancelled: 0,
    retried: 0,
  };
  for (let processed = 0; processed < 40 && clock() < deadline; processed++) {
    const job = await repository.claim();
    if (!job) break;
    const data = await repository.context(job);
    if (!data) {
      await repository.finish(job, { cancelled: true });
      counts.cancelled++;
      continue;
    }
    let deliveryId: string;
    try {
      deliveryId = await sender.send(
        scheduleMail(settings, data),
        job.event_key,
      );
    } catch (error) {
      const invalid = error instanceof InvalidMail;
      await repository.finish(job, {
        error: invalid ? error.message : smtpError(error),
      });
      counts.retried++;
      // Un fallo de Gmail no debe multiplicarse por todos los clientes del lote.
      if (!invalid) break;
      continue;
    }
    // Si falla guardar después de SMTP, conservar la reserva. No reenviar aquí.
    await repository.finish(job, { deliveryId });
    counts.sent++;
  }
  return counts;
}

async function authorized(request: Request, secret: string): Promise<boolean> {
  const header = request.headers.get("Authorization") ?? "";
  if (!header.startsWith("Bearer ") || header.length > 512) return false;
  const encoder = new TextEncoder();
  const [actual, expected] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(header.slice(7))),
    crypto.subtle.digest("SHA-256", encoder.encode(secret)),
  ]);
  const left = new Uint8Array(actual);
  const right = new Uint8Array(expected);
  let difference = 0;
  for (let i = 0; i < left.length; i++) difference |= left[i] ^ right[i];
  return difference === 0;
}

type Dependencies = {
  env?: Env;
  repository?: (settings: Settings) => Repository;
  sender?: (settings: Settings) => Sender;
};

export function createHandler(dependencies: Dependencies = {}) {
  const env = dependencies.env ?? ((name) => Deno.env.get(name));
  return async (request: Request): Promise<Response> => {
    const respond = (body: unknown, status = 200) =>
      Response.json(body, {
        status,
        headers: { "Cache-Control": "no-store" },
      });
    if (request.method !== "POST") return respond({ error: "Usa POST." }, 405);
    const secret = value(env, "SCHEDULE_CRON_SECRET");
    if (!/^[A-Za-z0-9_-]{32,256}$/.test(secret)) {
      return respond({
        error: "Configura SCHEDULE_CRON_SECRET en Edge Functions > Secrets.",
      }, 503);
    }
    if (!await authorized(request, secret)) {
      return respond({ error: "No autorizado." }, 401);
    }
    let body: { dry_run?: boolean };
    try {
      const text = await request.text();
      if (text.length > 1024) throw new Error();
      body = text ? JSON.parse(text) : {};
      if (
        !body || Array.isArray(body) || typeof body !== "object" ||
        Object.keys(body).some((key) => key !== "dry_run") ||
        (body.dry_run !== undefined && typeof body.dry_run !== "boolean")
      ) throw new Error();
    } catch {
      return respond({ error: 'Usa {} o {"dry_run":true}.' }, 400);
    }
    try {
      const settings = readSettings(env);
      const repository = dependencies.repository?.(settings) ??
        new SupabaseRepository(settings);
      const sender = dependencies.sender?.(settings) ??
        new GmailSender(settings);
      if (body.dry_run) {
        await repository.check();
        try {
          await sender.verify();
        } catch (error) {
          return respond({ error: smtpError(error), dry_run: true }, 503);
        }
        return respond({
          ok: true,
          dry_run: true,
          database: "ok",
          gmail: "ok",
          sent: 0,
        });
      }
      const counts = await processBatch(settings, repository, sender);
      // Solo contadores: nunca correos, nombres, contraseñas ni cuerpos SMTP.
      console.info("schedule-emails", counts);
      return respond({ ok: true, ...counts });
    } catch (error) {
      if (error instanceof ConfigurationError) {
        return respond({ error: error.message }, 503);
      }
      console.error(
        "schedule-emails: fallo de procesamiento; revisa la cola y las migraciones.",
      );
      return respond({
        error:
          "No se pudo procesar la cola. Revisa Supabase y la migración 006.",
      }, 503);
    }
  };
}
