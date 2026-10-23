"""Construcción de mensajes, independiente del transporte y del almacenamiento."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from email.utils import parseaddr
from html import escape
from datetime import datetime, time
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

LIMA = ZoneInfo("America/Lima")
DAYS = {"lunes": "Lunes", "martes": "Martes", "miercoles": "Miércoles", "jueves": "Jueves",
        "viernes": "Viernes", "sabado": "Sábado", "domingo": "Domingo"}
SERVICES = {"fitness": "Fitness", "musculacion": "Musculación", "cardio": "Cardio", "baile": "Baile"}

def _email(value: str) -> str:
    if "\r" in value or "\n" in value:
        raise ValueError("Dirección de correo inválida")
    address = parseaddr(value)[1]
    if not address or "@" not in address:
        raise ValueError("Falta una dirección de correo válida")
    return address

def email_sender(settings) -> tuple[str, str]:
    address = _email(settings.email_from.strip())
    name = settings.email_from_name.strip() or "Silver Gym Surco"
    if "\r" in name or "\n" in name:
        raise ValueError("Nombre del remitente inválido")
    return address, f"{name} <{address}>"

def membership_email(settings, event: str, saved: dict, plan: dict) -> dict:
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

def schedule_email(settings, data: dict) -> dict:
    event = data["event_type"]
    if event not in {"enrollment", "reminder"}:
        raise ValueError("Tipo de aviso de horario inválido")
    recipient = _email(str(data.get("correo") or ""))
    _, sender = email_sender(settings)
    base = settings.frontend_public_url.rstrip("/")
    if urlsplit(base).scheme not in {"http", "https"} or not urlsplit(base).netloc:
        raise ValueError("Configura FRONTEND_PUBLIC_URL para el enlace al horario")
    start = time.fromisoformat(data["hora_inicio"]).strftime("%H:%M")
    end = time.fromisoformat(data["hora_fin"]).strftime("%H:%M")
    service = SERVICES[data["servicio"]]
    day = DAYS[data["dia"]]
    name = str(data.get("nombre") or "Cliente")
    details = [("Clase", service), ("Día", day), ("Horario", f"{start} – {end}"), ("Zona horaria", "Perú (America/Lima)")]
    if event == "enrollment":
        title = "El administrador te inscribió en una clase"
        description = "Se agregó una clase a tu horario. Revisa los datos de tu matrícula:"
        details.append(("Frecuencia", f"Cada {day.lower()}, mientras tu matrícula y membresía estén vigentes"))
        subject = f"Inscripción confirmada: {service} · Silver Gym Surco"
    else:
        occurrence = datetime.fromisoformat(data["class_start"]).astimezone(LIMA)
        details.insert(2, ("Fecha", occurrence.strftime("%d/%m/%Y")))
        title = "Te esperamos en tu próxima clase"
        # No afirma «falta una hora»: un reintento de Resend puede llegar más tarde.
        description = "Te recordamos tu clase programada. Revisa la hora de inicio y prepárate para entrenar."
        subject = f"Recordatorio: {service} a las {start} · Silver Gym Surco"
    url = f"{base}/user/schedule"
    if event == "reminder":
        url += f"?fecha={occurrence.date().isoformat()}"
    rows = "".join(
        f'<tr><td style="padding:10px;border-bottom:1px solid #eee;color:#555">{escape(label)}</td>'
        f'<td style="padding:10px;border-bottom:1px solid #eee">{escape(value)}</td></tr>'
        for label, value in details
    )
    html = (
        '<!doctype html><html lang="es"><body style="margin:0;background:#f5f5f5;font-family:Arial,sans-serif;color:#171717">'
        '<main style="max-width:620px;margin:24px auto;padding:32px;background:#fff;border-radius:16px">'
        '<p style="color:#dc2626;font-weight:bold">Silver Gym Surco</p>'
        f'<h1 style="font-size:26px">{escape(title)}</h1><p>Hola, {escape(name)}.</p>'
        f'<p style="line-height:1.6">{escape(description)}</p><table style="width:100%;border-collapse:collapse">{rows}</table>'
        f'<p style="margin:28px 0"><a href="{escape(url, quote=True)}" style="background:#dc2626;color:#fff;padding:14px 24px;'
        'border-radius:8px;text-decoration:none">Ver mi horario</a></p>'
        '<p style="font-size:12px;color:#666">Si necesitas cambiar tu clase, comunícate con administración.</p></main></body></html>'
    )
    text = f"Silver Gym Surco\n{title}\n\nHola, {name}.\n{description}\n\n"
    text += "\n".join(f"{label}: {value}" for label, value in details)
    text += f"\n\nVer mi horario: {url}"
    return {"from": sender, "to": [recipient], "subject": subject, "html": html, "text": text}

