// SMTP con TLS desde el inicio: Supabase bloquea 25/587; Gmail admite 465.
// Versión fijada de la misma librería utilizada por el ejemplo SMTP de Supabase.
// @ts-types="npm:@types/nodemailer@8.0.1"
import nodemailer from "npm:nodemailer@9.1.1";

export type MailSettings = {
  gmailEmail: string;
  gmailPassword: string;
  senderName: string;
  frontendUrl: string;
  supabaseUrl: string;
};

export type DeliveryContext = {
  nombre: string;
  correo: string;
  servicio: string;
  dia: string;
  hora_inicio: string;
  hora_fin: string;
  class_start: string | null;
  event_type: "enrollment" | "reminder";
};

export type Mail = { to: string; subject: string; text: string; html: string };
export interface Sender {
  send(mail: Mail, eventKey: string): Promise<string>;
  verify(): Promise<void>;
}

export class InvalidMail extends Error {}

export function containsControls(value: string): boolean {
  return Array.from(value).some((char) =>
    char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127
  );
}

export function emailAddress(value: string): string {
  const address = value.trim();
  if (
    containsControls(address) ||
    !/^[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+$/.test(address)
  ) {
    throw new InvalidMail("Revisa el correo del cliente o del remitente.");
  }
  return address;
}

const days: Record<string, string> = {
  lunes: "Lunes",
  martes: "Martes",
  miercoles: "Miércoles",
  jueves: "Jueves",
  viernes: "Viernes",
  sabado: "Sábado",
  domingo: "Domingo",
};
const services: Record<string, string> = {
  fitness: "Fitness",
  musculacion: "Musculación",
  cardio: "Cardio",
  baile: "Baile",
};
const escape = (value: string) =>
  value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]!));

function hour(value: string): string {
  if (!/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d(?:\.\d+)?)?$/.test(value)) {
    throw new InvalidMail("Revisa las horas de la clase.");
  }
  return value.slice(0, 5);
}

export function scheduleMail(
  settings: MailSettings,
  data: DeliveryContext,
): Mail {
  const to = emailAddress(String(data.correo ?? ""));
  const day = days[data.dia];
  const service = services[data.servicio];
  if (
    !day || !service || !["enrollment", "reminder"].includes(data.event_type)
  ) {
    throw new InvalidMail("Revisa el día, servicio y tipo de aviso.");
  }
  const start = hour(data.hora_inicio);
  const end = hour(data.hora_fin);
  const name = String(data.nombre || "Cliente");
  const details = [["Clase", service], ["Día", day], [
    "Horario",
    `${start} – ${end}`,
  ], ["Zona horaria", "Perú (America/Lima)"]];
  let title: string;
  let description: string;
  let subject: string;
  if (data.event_type === "enrollment") {
    title = "El administrador te inscribió en una clase";
    description =
      "Se agregó una clase a tu horario. Revisa los datos de tu matrícula:";
    details.push([
      "Frecuencia",
      `Cada ${day.toLowerCase()}, mientras tu matrícula y membresía estén vigentes`,
    ]);
    subject = `Inscripción confirmada: ${service} · Silver Gym Surco`;
  } else {
    const occurrence = new Date(data.class_start ?? "");
    if (!Number.isFinite(occurrence.getTime())) {
      throw new InvalidMail("Revisa la fecha de la clase.");
    }
    details.splice(2, 0, [
      "Fecha",
      new Intl.DateTimeFormat("es-PE", {
        timeZone: "America/Lima",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      }).format(occurrence),
    ]);
    title = "Te esperamos en tu próxima clase";
    // Los reintentos pueden llegar después de la hora programada de envío.
    description =
      "Te recordamos tu clase programada. Revisa la hora de inicio y prepárate para entrenar.";
    subject = `Recordatorio: ${service} a las ${start} · Silver Gym Surco`;
  }
  const url = `${settings.frontendUrl}/user/schedule`;
  const rows = details.map(([label, value]) =>
    `<tr><td style="padding:10px;border-bottom:1px solid #eee;color:#555">${
      escape(label)
    }</td>` +
    `<td style="padding:10px;border-bottom:1px solid #eee">${
      escape(value)
    }</td></tr>`
  ).join("");
  const html =
    '<!doctype html><html lang="es"><body style="margin:0;background:#f5f5f5;font-family:Arial,sans-serif;color:#171717">' +
    '<main style="max-width:620px;margin:24px auto;padding:32px;background:#fff;border-radius:16px">' +
    '<p style="color:#dc2626;font-weight:bold">Silver Gym Surco</p>' +
    `<h1 style="font-size:26px">${escape(title)}</h1><p>Hola, ${
      escape(name)
    }.</p>` +
    `<p style="line-height:1.6">${
      escape(description)
    }</p><table style="width:100%;border-collapse:collapse">${rows}</table>` +
    `<p style="margin:28px 0"><a href="${
      escape(url)
    }" style="background:#dc2626;color:#fff;padding:14px 24px;` +
    'border-radius:8px;text-decoration:none">Ver mi horario</a></p>' +
    '<p style="font-size:12px;color:#666">Si necesitas cambiar tu clase, comunícate con administración.</p></main></body></html>';
  const text =
    `Silver Gym Surco\n${title}\n\nHola, ${name}.\n${description}\n\n` +
    details.map(([label, value]) => `${label}: ${value}`).join("\n") +
    `\n\nVer mi horario: ${url}`;
  return { to, subject, text, html };
}

export async function messageId(
  settings: MailSettings,
  eventKey: string,
): Promise<string> {
  // Mismo identificador que el emisor Python si coinciden proyecto y evento.
  const input = new TextEncoder().encode(`${settings.supabaseUrl}|${eventKey}`);
  const hash = new Uint8Array(await crypto.subtle.digest("SHA-256", input));
  const digest = Array.from(hash, (byte) => byte.toString(16).padStart(2, "0"))
    .join("");
  return `<membership-${digest}@${settings.gmailEmail.split("@")[1]}>`;
}

export function smtpError(error: unknown): string {
  const code = (error as { code?: string } | null)?.code;
  if (code === "EAUTH") {
    return "Gmail rechazó el acceso. Revisa GMAIL_EMAIL y la contraseña de aplicación.";
  }
  if (code === "EENVELOPE") {
    return "Gmail rechazó el destinatario. Revisa el correo del cliente.";
  }
  return "No se pudo confirmar el envío con Gmail; se reintentará automáticamente.";
}

export class GmailSender implements Sender {
  constructor(private settings: MailSettings) {}

  private transport() {
    return nodemailer.createTransport({
      host: "smtp.gmail.com",
      port: 465,
      secure: true,
      auth: {
        user: this.settings.gmailEmail,
        pass: this.settings.gmailPassword,
      },
      connectionTimeout: 7000,
      greetingTimeout: 7000,
      socketTimeout: 10000,
      dnsTimeout: 5000,
      logger: false,
      debug: false,
      disableFileAccess: true,
      disableUrlAccess: true,
      tls: { minVersion: "TLSv1.2", rejectUnauthorized: true },
    });
  }

  async verify(): Promise<void> {
    const transport = this.transport();
    try {
      await transport.verify(); // Autentica; no ejecuta MAIL/RCPT/DATA.
    } finally {
      transport.close();
    }
  }

  async send(mail: Mail, eventKey: string): Promise<string> {
    const transport = this.transport();
    const id = await messageId(this.settings, eventKey);
    try {
      const result = await transport.sendMail({
        ...mail,
        from: {
          name: this.settings.senderName,
          address: this.settings.gmailEmail,
        },
        to: emailAddress(mail.to),
        messageId: id,
        envelope: {
          from: this.settings.gmailEmail,
          to: [emailAddress(mail.to)],
        },
      });
      if (result.rejected?.length || !result.accepted?.length) {
        throw Object.assign(new Error("Destinatario rechazado"), {
          code: "EENVELOPE",
        });
      }
      return id;
    } finally {
      transport.close();
    }
  }
}
