"""Orquesta Stripe sin publicar datos privados de las solicitudes temporales."""
from application.operations.preregistrations import (
    AttachPreregistrationCheckoutCommand, DuePreregistrationsQuery, ExpirePreregistrationCommand,
)
from domain.services.preregistration_rules import utc_now
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def value(item, key, default=None):
    return item.get(key, default) if isinstance(item, dict) else getattr(item, key, default)


def public_request(row):
    return {key: row[key] for key in ('token', 'estado', 'expira_en', 'monto_pago')}


class PublicPreregistrationService:
    def __init__(self, clients, gateway, settings):
        self.clients, self.gateway = clients, gateway
        self.executor = clients.gym.executor
        self.expected_live = str(getattr(settings, 'stripe_mode', 'test')).lower() == 'live'
        self.frontend_url = str(getattr(settings, 'frontend_public_url', '') or '').rstrip('/')

    def checkout(self, row):
        if row['checkout_session_id']:
            return {'configured': True, 'session_id': row['checkout_session_id'],
                    'checkout_url': row['checkout_url'], 'amount': row['monto_pago'], 'currency': 'PEN'}
        if datetime.fromisoformat(utc_now()) >= datetime.fromisoformat(row['creado_en']) + timedelta(hours=24):
            recovered = self.gateway.find_preregistration_checkout(row)
            if not recovered:
                return None
            payment = dict(configured=True, session_id=value(recovered, 'id'),
                           checkout_url=value(recovered, 'url') or '', amount=row['monto_pago'], currency='PEN')
        else:
            payment = self.gateway.create_preregistration_checkout(row)
        self.executor.execute(AttachPreregistrationCheckoutCommand(
            row['token'], int(row['intento']), payment['session_id'], payment['checkout_url']))
        return payment

    def register(self, payload, confirm):
        result = self.clients.prepare_public_registration(payload)
        if 'preregistro' not in result:
            # No rompe el retorno de checkouts públicos anteriores a la migración.
            try:
                payment = self.gateway.create_membership_checkout(result)
            except RuntimeError:
                payment = {'configured': True, 'message': 'No se pudo abrir Stripe. Puedes reintentar con los mismos datos.'}
            return {**result, 'payment': payment}
        row = result['preregistro']
        try:
            # La clave de idempotencia recupera la misma sesión incluso si se perdió
            # la respuesta anterior, antes de que pudiéramos guardar su identificador.
            payment = self.checkout(row)
            if payment is None:
                self.executor.execute(ExpirePreregistrationCommand(row['token'], int(row['intento']), ''))
                row = self.clients.prepare_public_registration(payload)['preregistro']
                payment = self.checkout(row)
            row = {**row, 'checkout_session_id': payment['session_id']}
            checkout = self.gateway.get_checkout_session(payment['session_id'])
            if value(checkout, 'status') == 'expired' and value(checkout, 'payment_status') == 'unpaid':
                self.expire_verified(row, checkout)
                row = self.clients.prepare_public_registration(payload)['preregistro']
                payment = self.checkout(row)
            elif value(checkout, 'status') == 'complete' and value(checkout, 'payment_status') == 'paid':
                confirm(payment['session_id'])
                row = {**row, 'estado': 'CONVERTIDO'}
                from urllib.parse import quote
                payment = {**payment, 'checkout_url': f"{self.frontend_url}/registro/pago/p-{row['token']}?result=success&session_id={quote(payment['session_id'], safe='')}"}
        except RuntimeError:
            payment = {'configured': True, 'message': 'Tu solicitud está guardada temporalmente. Reintenta con los mismos datos para abrir Stripe.'}
        return {'preregistro': public_request(row), 'payment': payment}

    def expire_verified(self, row, checkout):
        metadata = value(checkout, 'metadata', {}) or {}
        if bool(value(checkout, 'livemode', False)) != self.expected_live:
            raise ValueError('La sesión de Stripe no corresponde al modo configurado')
        if str(value(metadata, 'attempt')) != str(row['intento']) or row['estado'] == 'CONVERTIDO':
            return
        if (value(checkout, 'id') != row['checkout_session_id']
                or value(checkout, 'client_reference_id') != f"preregistration:{row['token']}"
                or value(metadata, 'purpose') != 'membership_preregistration'
                or value(metadata, 'preregistration_token') != row['token']
                or str(value(metadata, 'attempt')) != str(row['intento'])):
            raise ValueError('La sesión no corresponde al preregistro')
        if value(checkout, 'status') != 'expired' or value(checkout, 'payment_status') != 'unpaid':
            return
        self.executor.execute(ExpirePreregistrationCommand(row['token'], int(row['intento']), row['checkout_session_id']))

    def archive_due(self, confirm, now=None):
        """Caduca en Stripe antes de archivar; conserva pagos en proceso y fallos inciertos."""
        due = self.executor.query(DuePreregistrationsQuery(now or utc_now()))
        processed = 0
        for row in due:
            try:
                if not row['checkout_session_id']:
                    payment = self.checkout(row)
                    if payment is None:
                        self.executor.execute(ExpirePreregistrationCommand(row['token'], int(row['intento']), ''))
                        processed += 1
                        continue
                    row = {**row, 'checkout_session_id': payment['session_id']}
                checkout = self.gateway.expire_checkout_session(row['checkout_session_id'])
                if value(checkout, 'payment_status') == 'paid':
                    confirm(row['checkout_session_id'])
                else:
                    self.expire_verified(row, checkout)
                processed += 1
            except (RuntimeError, ValueError) as error:
                # Se conserva para reconciliación posterior; nunca se interpreta
                # una caída de Stripe como prueba de ausencia de pago.
                logger.warning('Solicitud pendiente de reconciliación (%s)', type(error).__name__)
                continue
        return processed
