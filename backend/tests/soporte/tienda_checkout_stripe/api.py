"""API QA para el checkout de tienda con Stripe sandbox y persistencia en memoria."""
from pathlib import Path
import json
import os
import queue
import re
import subprocess
import sys
from threading import Thread
import secrets
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from infrastructure.config import Settings, get_settings

stripe_settings = get_settings()
if stripe_settings.stripe_mode != "test" or not stripe_settings.stripe_secret_key.startswith("sk_test_"):
    raise SystemExit("Configuración de Stripe de prueba requerida")
os.environ["AUTH_SECRET_KEY"] = "local-tc195-synthetic-only-session-0123456789abcdef"
for key in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "RESEND_API_KEY", "GMAIL_APP_PASSWORD", "GOOGLE_CLIENT_ID"):
    os.environ[key] = ""
get_settings.cache_clear()
cli = Path(os.environ["GYM_TEST_STRIPE_CLI"])
forwarder = subprocess.Popen(
    [str(cli), "listen", "--events", "checkout.session.completed,checkout.session.expired",
     "--forward-to", "http://127.0.0.1:8013/api/pagos/stripe/webhook"],
    env={**os.environ, "STRIPE_API_KEY": stripe_settings.stripe_secret_key},
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
    errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
secrets_found = queue.Queue()

def collect():
    found = False
    for line in forwarder.stdout:
        match = re.search(r"\bwhsec_[A-Za-z0-9]+\b", line)
        if match and not found:
            secrets_found.put(match.group(0))
            found = True
    if not found:
        secrets_found.put(None)

Thread(target=collect, daemon=True).start()
try:
    signing_secret = secrets_found.get(timeout=40)
    if not signing_secret:
        raise SystemExit("No se pudo iniciar el reenvío de webhooks con Stripe CLI")
    from fastapi import FastAPI, Header, HTTPException, Request, Response
    from infrastructure.services.local_gym_service import LocalGymService
    from presentation import dependencies as deps
    from presentation.error_handlers import install_error_handlers
    from presentation.routes import auth_routes, clients_routes, memberships_routes, store_routes
    import uvicorn

    qa = Settings(stripe_mode="test", stripe_secret_key=stripe_settings.stripe_secret_key,
                  stripe_webhook_secret=signing_secret, frontend_public_url="http://127.0.0.1:5194",
                  auth_secret_key=os.environ["AUTH_SECRET_KEY"])
    gym = LocalGymService()
    customer_email = f"tc195-qa-{uuid4().hex[:10]}@example.com"
    password = "TC195-Synthetic-Only-2026!"
    gym.state["usuario"] = [gym._normalize_usuario_record({
        "id_usuario": "SGADM001", "nombre": "Admin TC195 QA", "rol": "admin", "correo": "admin@example.com",
        "estado": "ACTIVO", "dni": "99999999", "password_hash": gym.passwords.hash(password),
    })]
    gym.state["clientes"] = [gym._normalize_cliente_record({
        "id_cliente": 1, "id_usuario": "SGCLI001", "nombre": "Cliente caso 195 QA", "dni": "11111111",
        "correo": customer_email, "estado": "ACTIVO", "password_hash": gym.passwords.hash(password),
    }, 1)]
    gym.state["membresia"] = [{
        "id_membresia": 1, "id_cliente": 1, "estado": "ACTIVO", "estado_pago": "PAGADO",
        "fecha_inicio": "2026-01-01", "fecha_fin": "2099-12-31",
    }]
    for resource in ("inventario", "inventario_unidades", "mov_inv", "productos_tienda", "pedidos_tienda"):
        gym.state[resource] = []
    product = gym.upsert_producto_tienda({
        "nombre_producto": f"Botella TC195 QA {uuid4().hex[:6]}", "precio_venta": 15,
        "categoria": "Bebidas", "cantidad_stock": 5,
    })
    events = []
    app = FastAPI(title="SG-RF23-IT01 · Checkout de tienda con Stripe")
    install_error_handlers(app)
    app.dependency_overrides[deps.get_settings] = lambda: qa
    app.dependency_overrides[deps.get_gym_service] = lambda: gym
    for module in (auth_routes, clients_routes, memberships_routes, store_routes):
        app.include_router(module.router, prefix="/api")

    @app.middleware("http")
    async def scoped_webhooks(request: Request, call_next):
        if request.url.path != "/api/pagos/stripe/webhook":
            return await call_next(request)
        incoming = json.loads(await request.body())
        session = incoming.get("data", {}).get("object", {})
        ids = {row.get("referencia_pago") for row in gym.pedidos_tienda() if row.get("referencia_pago")}
        if session.get("id") not in ids or session.get("livemode") is not False:
            return Response(status_code=204)
        response = await call_next(request)
        if response.status_code == 200:
            events.append(incoming["type"])
        return response

    @app.get("/__qa/tc195")
    def state(x_qa_key: str = Header(default="")):
        if not secrets.compare_digest(x_qa_key, os.environ["GYM_TEST_STRIPE_SHUTDOWN_KEY"]):
            raise HTTPException(status_code=403)
        return {
            "qa": True, "customer": customer_email, "product": product["id_producto"],
            "name": product["nombre_producto"], "stock": gym.get_producto_tienda(product["id_producto"])["cantidad_stock"],
            "orders": [{"id": r["id_pedido"], "order": r["estado_pedido"], "payment": r["estado_pago"],
                        "total": r["total"]} for r in gym.pedidos_tienda()],
            "events": events.copy(),
        }

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8013, access_log=False, log_level="error"))

    @app.post("/__qa/shutdown")
    def shutdown(x_qa_key: str = Header(default="")):
        if not secrets.compare_digest(x_qa_key, os.environ["GYM_TEST_STRIPE_SHUTDOWN_KEY"]):
            raise HTTPException(status_code=403)
        server.should_exit = True
        return {"status": "closing"}

    print("Escucha Stripe y repositorio aislado listos.", flush=True)
    server.run()
finally:
    forwarder.terminate()
    try:
        forwarder.wait(timeout=5)
    except subprocess.TimeoutExpired:
        forwarder.kill()
