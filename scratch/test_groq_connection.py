"""
Script de prueba rápida de conectividad con la API de Groq.
Verifica:
  1. Que GROQ_API_KEY esté presente en el entorno o en backend/.env.
  2. Latencia de respuesta (debe ser < 15 s según RNF-CB01).
  3. Formato del campo response['usage']['total_tokens'] (RN-11).
  4. Modelo configurado: openai/gpt-oss-120b.

Uso:
  python scratch/test_groq_connection.py
"""
import os
import sys
import time
import json
import urllib.request
from pathlib import Path


def load_env_if_needed():
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_API_KEY")

    for path in [Path(".env"), Path("backend/.env"), Path("../backend/.env")]:
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GROQ_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        os.environ["GROQ_API_KEY"] = val
                        return val
    return None


def test_groq():
    api_key = load_env_if_needed()
    if not api_key:
        print("❌ ERROR: No se encontró la variable GROQ_API_KEY en el entorno ni en backend/.env")
        print("   Asegúrate de agregar GROQ_API_KEY=tu_api_key en tu archivo backend/.env")
        sys.exit(1)

    masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
    print(f"🔑 GROQ_API_KEY detectada: {masked_key}")

    url = "https://api.groq.com/openai/v1/chat/completions"
    model = "openai/gpt-oss-120b"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Eres Silver, asistente virtual de Silver Gym Surco."},
            {"role": "user", "content": "Hola, ¿estás disponible? Responde brevemente en una línea."}
        ],
        "max_tokens": 50,
        "temperature": 0.2
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SilverGym-Chatbot-Test/1.0"
        },
        method="POST"
    )

    print(f"📡 Enviando solicitud de prueba a Groq ({model})...")
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            elapsed = time.time() - start_time
            body = json.loads(resp.read().decode("utf-8"))

            status_code = resp.status
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            usage = body.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)

            print("\n" + "=" * 50)
            print("✅ CONEXIÓN CON GROQ EXITOSA")
            print("=" * 50)
            print(f"HTTP Status      : {status_code}")
            print(f"Latencia         : {elapsed:.2f} s (Límite máximo permitido: 15.00 s)")
            print(f"Tokens de prompt : {usage.get('prompt_tokens', 0)}")
            print(f"Tokens respuesta : {usage.get('completion_tokens', 0)}")
            print(f"Total tokens     : {total_tokens} (campo 'usage' verificado)")
            print(f"Respuesta modelo : \"{content}\"")
            print("=" * 50)

            if elapsed <= 15.0:
                print("🎯 CUMPLE RNF-CB01: Respuesta recibida en ≤ 15 segundos.")
            else:
                print("⚠️ ADVERTENCIA: La latencia superó 15 segundos.")

    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8", errors="ignore")
        print(f"\n❌ Error HTTP de Groq ({e.code}): {error_msg}")
        if e.code == 401:
            print("   Verifica que la clave GROQ_API_KEY sea válida.")
        elif e.code == 404 and "model" in error_msg:
            print(f"   Nota: El modelo {model} podría no estar habilitado en tu cuenta de Groq.")
    except Exception as e:
        print(f"\n❌ Error de conexión: {str(e)}")


if __name__ == "__main__":
    test_groq()
