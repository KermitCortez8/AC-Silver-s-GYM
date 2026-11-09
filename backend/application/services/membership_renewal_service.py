"""Enlaces personales de recompra sin depender de una sesión de cliente vigente."""
from datetime import date, datetime, timedelta
import hashlib
import hmac
from zoneinfo import ZoneInfo

from domain.services.membership_lifecycle import membership_renewable, RENEWAL_LEAD_DAYS, RENEWAL_WINDOW_MESSAGE

from application.operations.memberships import RenewMembershipCommand, SaveRenewalSessionCommand, RenewMembershipCashCommand


def lima_today():
    return datetime.now(ZoneInfo('America/Lima')).date()


def renewal_token(settings, membership):
    secret = settings.auth_secret_key
    if not secret:
        raise RuntimeError('Configura AUTH_SECRET_KEY para los enlaces de renovación')
    identity = f"{membership['id_cliente']}:{membership['id_membresia']}:{membership['fecha_fin']}"
    signature = hmac.new(secret.encode(), f'renewal:v1:{identity}'.encode(), hashlib.sha256).hexdigest()
    return f"{membership['id_cliente']}.{membership['id_membresia']}.{signature}"


class MembershipRenewalService:
    def __init__(self, gym, settings, gateway):
        self.gym, self.settings, self.gateway = gym, settings, gateway

    def resolve(self, token):
        try:
            client_id, membership_id, _signature = token.split('.')
            membership = self.gym.membership(int(client_id), int(membership_id))
            if not membership or not hmac.compare_digest(token, renewal_token(self.settings, membership)):
                raise ValueError()
            end = date.fromisoformat(membership['fecha_fin'][:10])
            if not end - timedelta(days=RENEWAL_LEAD_DAYS) <= lima_today() <= end + timedelta(days=30):
                raise ValueError()
            if not membership_renewable(membership, lima_today().isoformat()):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            raise ValueError('El enlace de renovación no es válido o venció. Contacta con administración.') from None
        return membership

    def details(self, token):
        return self.details_for(self.resolve(token))

    def details_for(self, source):
        rows = self.gym.membresias_por_cliente(source['id_cliente'])
        newer = [m for m in rows if int(m['id_membresia']) > int(source['id_membresia'])]
        pending = max((m for m in newer if m.get('estado_pago') != 'PAGADO'),
                      key=lambda m: int(m['id_membresia']), default=None)
        completed = any(m.get('estado_pago') == 'PAGADO' for m in newer)
        purchase = max((m for m in newer if m.get('estado_pago') == 'PAGADO'),
                       key=lambda m: int(m['id_membresia']), default=None) or pending
        plan = self.gym.get_plan_membresia(int((purchase or source)['id_pm']))
        if not plan:
            raise ValueError('Este plan ya no está disponible. Contacta con administración.')
        amount = purchase['monto_pago'] if purchase else plan['precio']
        return {'plan': plan['nombre_plan'], 'descripcion': plan.get('descripcion', ''),
                'duracion': plan.get('duracion', ''), 'fecha_fin': source['fecha_fin'],
                'monto_pago': amount, 'moneda': 'PEN', 'renovada': completed,
                'id_membresia_origen': source['id_membresia'], 'renovacion_pendiente': bool(pending),
                'promocion': 'Según compra registrada' if purchase and purchase.get('id_promocion') else 'Sin promoción',
                'activacion': 'Tu renovación se activa automáticamente cuando se confirma el pago. Si tu membresía sigue vigente, el nuevo período empieza al día siguiente de su vencimiento.'}

    def admin_source(self, client_id, source_id=None):
        client = self.gym.get_cliente(client_id)
        if not client:
            raise ValueError('Cliente no encontrado')
        candidates = [m for m in self.gym.membresias_por_cliente(client_id)
                      if m.get('estado_pago') == 'PAGADO' and m.get('estado') in {'ACTIVO', 'VENCIDA'}
                      and m.get('fecha_inicio') and m.get('fecha_fin')]
        source = max(candidates, key=lambda m: int(m['id_membresia']), default=None)
        if not source:
            raise ValueError('La primera membresía debe pagarse y activarse antes de renovar')
        if source_id is not None and int(source['id_membresia']) != int(source_id):
            raise ValueError('La membresía del cliente cambió. Actualiza los detalles antes de renovar.')
        if not membership_renewable(source, lima_today().isoformat()):
            raise ValueError(RENEWAL_WINDOW_MESSAGE)
        return source

    def admin_details(self, client_id):
        return self.details_for(self.admin_source(client_id))

    def admin_cash(self, client_id, source_id, expected_amount):
        self.admin_source(client_id, source_id)
        return self.gym.executor.execute(RenewMembershipCashCommand(client_id, source_id, expected_amount))

    def checkout(self, token, expected_amount):
        return self.checkout_for(self.resolve(token), expected_amount, token=token)

    def admin_checkout(self, client_id, source_id, expected_amount):
        return self.checkout_for(self.admin_source(client_id, source_id), expected_amount, admin=True)

    def checkout_for(self, source, expected_amount, *, token='', admin=False):
        self.gateway.validate_configuration()
        membership = self.gym.executor.execute(RenewMembershipCommand(
            int(source['id_cliente']), int(source['id_membresia']), expected_amount))
        client = self.gym.get_cliente(int(source['id_cliente']))
        plan = self.gym.get_plan_membresia(int(membership['id_pm']))
        previous = str(membership.get('referencia_pago') or '')
        if previous:
            from application.services.membership_checkout_service import _value
            checkout = self.gateway.get_checkout_session(previous)
            if _value(checkout, 'payment_status') == 'paid' or _value(checkout, 'status') == 'complete':
                raise ValueError('La operación requiere confirmar su pago. Consulta con administración antes de pagar nuevamente.')
            if _value(checkout, 'status') == 'open' and _value(checkout, 'url'):
                return {'configured': True, 'session_id': previous, 'checkout_url': _value(checkout, 'url')}
            if _value(checkout, 'status') != 'expired':
                raise ValueError('No se pudo verificar el intento anterior. Intenta nuevamente más tarde.')
        payment = self.gateway.create_membership_checkout({'cliente': client, 'membresia': membership, 'plan': plan,
            'renewal_token': token, 'checkout_attempt': previous}, **({'admin': True} if admin else {}))
        self.gym.executor.execute(SaveRenewalSessionCommand(
            int(source['id_cliente']), int(membership['id_membresia']), payment['session_id']))
        return payment
