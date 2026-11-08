"""
Script de prueba de envío de alerta de presupuesto con Resend.
Verifica:
  1. Que RESEND_API_KEY esté presente en el entorno o en backend/.env.
  2. Que el remitente y destinatario configurados puedan enviar/recibir correos.
  3. Formato del correo de alerta por umbral del 80% (HU-CB15, [?-P2 DECIDIDO]).

Uso:
  python scratch/test_resend_email.py
"""
import os
import sys
import json
import urllib.request
from pathlib import Path


def load_env():
    for path in [Path(".env"), Path("backend/.env"), Path("../backend/.env")]:
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def test_resend():
    load_env()
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("❌ ERROR: No se encontró la variable RESEND_API_KEY en el entorno ni en backend/.env")
        print("   Asegúrate de agregar RESEND_API_KEY=re_... en tu archivo backend/.env")
        sys.exit(1)

    masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
    print(f"🔑 RESEND_API_KEY detectada: {masked_key}")

    # Remitente verificado en Resend (por defecto en pruebas suele ser onboarding@resend.dev)
    from_email = os.getenv("CHATBOT_ALERT_EMAIL_FROM") or os.getenv("EMAIL_FROM") or "onboarding@resend.dev"
    # Destinatario
    to_email = os.getenv("CHATBOT_ALERT_EMAIL_TO") or "delivered@resend.dev"

    print(f"📤 Remitente configurado : {from_email}")
    print(f"📥 Destinatario prueba  : {to_email}")

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": "[TEST] Alerta de Consumo Chatbot - Silver Gym Surco (Umbral 80%)",
        "html": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
            <h2 style="color: #D83A00; margin-top: 0;">⚠️ Alerta de Consumo de Tokens - Chatbot</h2>
            <p>Este es un correo de prueba de conectividad con la API de <strong>Resend</strong> para el sistema de control del Chatbot.</p>
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #D83A00; margin: 15px 0;">
                <p style="margin: 0;"><strong>Umbral alcanzado:</strong> 80% del presupuesto diario interno (144.000 / 180.000 tokens).</p>
                <p style="margin: 5px 0 0 0;"><strong>Fecha y hora:</strong> Registro de prueba automático.</p>
            </div>
            <p style="color: #666; font-size: 13px;">Silver Gym Surco · Sistema Web SWGACSGYM</p>
        </div>
        """
    }

    url = "https://api.resend.com/emails"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    print("📡 Enviando correo de prueba a través de Resend...")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            print("\n" + "=" * 50)
            print("✅ CORREO ENVIADO CON ÉXITO VÍA RESEND")
            print("=" * 50)
            print(f"HTTP Status : {resp.status}")
            print(f"Email ID    : {body.get('id', 'N/A')}")
            print("=" * 50)
            print(f"Revisa tu bandeja de entrada en: {to_email}")
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8", errors="ignore")
        print(f"\n❌ Error HTTP de Resend ({e.code}): {error_msg}")
        if e.code == 403:
            print("   Nota: Si usas 'onboarding@resend.dev', solo puedes enviar correos a la dirección de tu propia cuenta en Resend.")
    except Exception as e:
        print(f"\n❌ Error de conexión: {str(e)}")


if __name__ == "__main__":
    test_resend()
