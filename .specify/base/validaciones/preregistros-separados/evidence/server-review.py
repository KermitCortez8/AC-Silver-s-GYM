"""API aislada para la revisión visual. Solo memoria, pagos y correos simulados."""
from pathlib import Path
import json
import sys
from types import SimpleNamespace
from urllib.parse import quote
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'backend'))
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from application.services.clients_service import ClientsService
from application.services.client_payments_service import ClientPaymentsService
from application.services.gym_service import GymService
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from presentation.dependencies import get_client_payments_service, get_clients_service, require_admin_or_staff
from presentation.error_handlers import install_error_handlers
from presentation.routes.clients_routes import router
from tests.test_priority_fixes import Passwords
from tests.test_public_preregistrations import Gateway

FRONTEND = 'http://127.0.0.1:5174'


class LocalGateway(Gateway):
    def create_preregistration_checkout(self, row):
        result = super().create_preregistration_checkout(row)
        result['checkout_url'] = f"http://127.0.0.1:8001/checkout/{result['session_id']}"
        self.sessions[result['session_id']]['url'] = result['checkout_url']
        return result

    def construct_webhook_event(self, payload, signature):
        return super().construct_webhook_event(json.loads(payload) if isinstance(payload, bytes) else payload, signature)


gym = GymService(MemoryGymRepository(), Passwords())
clients, gateway = ClientsService(gym), LocalGateway()
payments = ClientPaymentsService(clients, gym,
    SimpleNamespace(has_supabase_credentials=True, stripe_mode='test', frontend_public_url=FRONTEND),
    gateway_factory=lambda _: gateway, notify=Mock(return_value={'status': 'simulada'}))
app = FastAPI()
install_error_handlers(app)
app.include_router(router, prefix='/api')
app.dependency_overrides[get_client_payments_service] = lambda: payments
app.dependency_overrides[get_clients_service] = lambda: clients
app.dependency_overrides[require_admin_or_staff] = lambda: SimpleNamespace(role='admin')


@app.get('/api/planes-membresia')
def plans():
    return gym.planes_membresia()


@app.get('/api/promociones/vigentes-publico')
@app.get('/api/promociones')
def promotions():
    return gym.promociones_vigentes_publicas()


@app.get('/api/auth/me')
def profile():
    return dict(id='SGADM001', name='Personal local', email='local@example.test', role='admin')


@app.get('/control/counts')
def counts():
    return dict(clients=len(gym.clientes_normalized()), memberships=len(gym.membresias()),
                pending=sum(r['estado'] == 'PENDIENTE' for r in gym.repository.state['preregistros']),
                expired=sum(r['estado'] == 'EXPIRADO' for r in gym.repository.state['preregistros']),
                sessions=len(gateway.sessions))


@app.post('/control/reset')
def reset():
    gym.repository.state = MemoryGymRepository().state
    gateway.sessions.clear()
    gateway.created.clear()
    gateway.fail_create = gateway.fail_retrieve = False
    return {'ok': True}


@app.post('/control/fail/{flag}')
def fail(flag: int):
    gateway.fail_create = bool(flag)
    return {'ok': True}


@app.post('/control/archive')
def archive():
    return {'processed': payments.archive_due_preregistrations('2099-01-01T00:00:00+00:00')}


@app.get('/checkout/{sid}', response_class=HTMLResponse)
def checkout(sid: str):
    return f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Checkout simulado local</title>
        <h1>Pago simulado de prueba</h1><p>No contacta Stripe ni realiza cobros.</p>
        <form method="post" action="/control/paid/{sid}"><button>Simular pago aprobado</button></form>
        <a href="/control/cancel/{sid}">Abandonar pago</a></html>'''


@app.post('/control/paid/{sid}')
def approve(sid: str):
    checkout = gateway.sessions[sid]
    checkout.update(status='complete', payment_status='paid')
    # El webhook crea al cliente antes de que el navegador regrese al gimnasio.
    payments.process_webhook({'type': 'checkout.session.completed', 'data': {'object': checkout}}, 'firma-local')
    token = checkout['metadata']['preregistration_token']
    return RedirectResponse(f'{FRONTEND}/registro/pago/p-{token}?result=success&session_id={quote(sid)}', status_code=303)


@app.get('/control/cancel/{sid}')
def cancel(sid: str):
    token = gateway.sessions[sid]['metadata']['preregistration_token']
    return RedirectResponse(f'{FRONTEND}/registro/pago/p-{token}?result=failure', status_code=303)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8001)
