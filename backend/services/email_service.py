"""Plantillas y envío de correos mediante la API HTTPS de Resend."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from email.utils import parseaddr
from html import escape
from hashlib import sha256
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

from config import Settings


def _email(value: str) -> str:
    if "\r" in value or "\n" in value:
        raise ValueError("Dirección de correo inválida")
    address = parseaddr(value)[1]
    if not address or "@" not in address:
        raise ValueError("Falta una dirección de correo válida")
    return address


def email_sender(settings: Settings) -> tuple[str, str]:
    address = _email(settings.email_from.strip())
    name = settings.email_from_name.strip() or "Silver Gym Surco"
    if "\r" in name or "\n" in name:
        raise ValueError("Nombre del remitente inválido")
    return address, f"{name} <{address}>"


def membership_email(settings: Settings, event: str, saved: dict, plan: dict) -> dict:
    client, membership = saved["cliente"], saved["membresia"]
    recipient = _email(str(client.get("correo") or client.get("email") or ""))
    _, sender = email_sender(settings)
    if event not in {"payment", "activation"}:
        raise ValueError("Tipo de notificación inválido")
    if str(membership.get("estado_pago") or "").upper() != "PAGADO":
        raise ValueError("El correo requiere un pago confirmado")
    if event == "activation" and (
        str(membership.get("estado") or "").upper() not in {"ACTIVO", "ACTIVA"}
        or str(client.get("estado") or "").upper() not in {"ACTIVO", "ACTIVA"}
    ):
        raise ValueError("La cuenta todavía no está activa")
    base_url = settings.frontend_public_url.rstrip("/")
    if urlsplit(base_url).scheme not in {"https", "http"} or not urlsplit(base_url).netloc:
        raise ValueError("Configura FRONTEND_PUBLIC_URL para el enlace de acceso")
    try:
        amount = Decimal(str(membership.get("monto_pago") or 0))
        if not amount.is_finite() or amount <= 0:
            raise ValueError("El importe de la membresía no es válido")
    except InvalidOperation as error:
        raise ValueError("El importe de la membresía no es válido") from error

    name = str(client.get("nombre") or "Cliente")
    code = str(client.get("id_usuario") or f"SGCLI{int(client['id_cliente']):03d}")
    details = [
        ("Cliente", name), ("Código de cliente", code),
        ("Membresía", str(plan.get("nombre_plan") or client.get("plan") or "")),
        ("Duración del plan", str(plan.get("duracion") or "Según el plan adquirido")),
        ("Importe pagado", f"S/ {amount:.2f} PEN"),
        ("Método de pago", str(membership.get("metodo_pago") or "Stripe")),
        ("Promoción", str(client.get("promocion") or "Sin promoción")),
        ("Fecha del pago", str(membership.get("fecha_pago") or "")),
        ("Referencia de pago", str(membership.get("referencia_pago") or "")),
    ]
    if event == "payment":
        title = "Pago de membresía confirmado"
        description = (
            "Recibimos el pago de tu preinscripción. Tu cuenta requiere la activación del administrador "
            "para poder ingresar. Recibirás otro correo cuando tu membresía esté activa."
        )
        details.append(("Estado", "Pago confirmado; requiere activación administrativa"))
    else:
        title = "Tu membresía está activa"
        description = "El administrador activó tu membresía. Ya puedes ingresar con el método con el que te registraste."
        details.extend([
            ("Inicio de vigencia", str(membership.get("fecha_inicio") or "")),
            ("Fin de vigencia", str(membership.get("fecha_fin") or "")),
            ("Estado", "Activa"),
        ])
    rows = "".join(
        f'<tr><td style="padding:10px;border-bottom:1px solid #eee;color:#555">{escape(label)}</td>'
        f'<td style="padding:10px;border-bottom:1px solid #eee">{escape(value)}</td></tr>'
        for label, value in details
    )
    login_url = f"{base_url}/login"
    action = (
        f'<p style="margin:28px 0"><a href="{escape(login_url, quote=True)}" '
        'style="background:#dc2626;color:#fff;padding:14px 24px;border-radius:8px;text-decoration:none">Ingresar a mi cuenta</a></p>'
        if event == "activation" else ""
    )
    html = (
        '<!doctype html><html lang="es"><body style="margin:0;background:#f5f5f5;font-family:Arial,sans-serif;color:#171717">'
        '<main style="max-width:620px;margin:24px auto;padding:32px;background:#fff;border-radius:16px">'
        '<p style="color:#dc2626;font-weight:bold">Silver Gym Surco</p>'
        f'<h1 style="font-size:26px">{escape(title)}</h1><p>Hola, {escape(name)}.</p>'
        f'<p style="line-height:1.6">{escape(description)}</p><table style="width:100%;border-collapse:collapse">{rows}</table>'
        f'{action}<p style="font-size:12px;color:#666">Este correo es una confirmación de tu membresía.</p></main></body></html>'
    )
    text = f"Silver Gym Surco\n{title}\n\nHola, {name}.\n{description}\n\n"
    text += "\n".join(f"{label}: {value}" for label, value in details)
    if event == "activation":
        text += f"\n\nIngresar a mi cuenta: {login_url}"
    return {"from": sender, "to": [recipient], "subject": f"{title} · Silver Gym Surco", "html": html, "text": text}


class ResendEmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, payload: dict, event_key: str) -> str:
        if not self.settings.has_email_credentials:
            raise RuntimeError("Configura RESEND_API_KEY y EMAIL_FROM para enviar correos.")
        try:
            _, sender = email_sender(self.settings)
            recipients = payload.get("to")
            if not isinstance(recipients, list) or len(recipients) != 1:
                raise ValueError("La notificación debe tener un único destinatario")
            # Actualiza también el remitente de mensajes encolados antes de migrar de Gmail.
            body = {
                "from": sender,
                "to": [_email(str(recipients[0]))],
                "subject": str(payload["subject"]),
                "html": str(payload["html"]),
                "text": str(payload["text"]),
            }
            # Misma clave en Python y Supabase: un proyecto y evento identifican el envío.
            digest = sha256(f"{self.settings.supabase_url.rstrip('/')}|{event_key}".encode()).hexdigest()
            request = Request(
                "https://api.resend.com/emails",
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.settings.resend_api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "AC-Silvers-GYM/1.1",
                    "Idempotency-Key": f"gym-{digest}",
                },
                method="POST",
            )
            with urlopen(request, timeout=15) as response:
                result = json.load(response)
            delivery_id = result.get("id") if isinstance(result, dict) else None
            if not isinstance(delivery_id, str) or not delivery_id.strip():
                raise RuntimeError("Resend no confirmó el envío; se reintentará.")
            return delivery_id
        except HTTPError as error:
            # Nunca persistir el cuerpo del proveedor: puede contener direcciones o credenciales.
            messages = {
                401: "Resend rechazó la clave. Revisa RESEND_API_KEY.",
                403: "Resend rechazó el envío. Revisa el remitente y el destinatario permitido para pruebas.",
                409: "Resend detectó un conflicto de envío. Conserva el contenido y remitente del evento al reintentar.",
                422: "Resend rechazó los datos. Revisa EMAIL_FROM y el correo del cliente.",
                429: "Se alcanzó el límite de Resend; el correo queda pendiente de reintento.",
            }
            raise RuntimeError(messages.get(error.code, "Resend no está disponible; se reintentará.")) from error
        except OSError as error:
            raise RuntimeError("No se pudo confirmar el envío con Resend; se reintentará.") from error
        except (ValueError, KeyError) as error:
            raise RuntimeError("Revisa la configuración de Resend y los datos del correo.") from error
