"""Prepara el QR o enlace de un alta cuyo cobro verifica recepción."""
import json
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from application.errors import ConfiguracionPagoExternoError
from application.operations.registro_pagos_externos import (
    ConfirmarMembresiaPagoExternoCommand, ConfirmarSolicitudPagoExternoCommand, SolicitudesPagoExternoQuery,
)
from application.services.public_preregistration_service import public_request
from domain.money import cents
from domain.services.registro_pago_externo import MEDIOS_EXTERNOS

DOMINIOS_MERCADO_PAGO = {'mpago.la', 'link.mercadopago.com.pe', 'www.mercadopago.com.pe', 'mercadopago.com.pe'}


class RegistroPagosExternos:
    def __init__(self, clients, settings, notify):
        self.clients, self.settings, self.notify = clients, settings, notify

    def instrucciones(self, medio):
        if medio == 'yape_plin':
            url = self.settings.pagos_yape_qr_url
            parsed = urlsplit(url)
            if '\\' in url or not ((parsed.scheme == 'https' and parsed.hostname and not parsed.username)
                                   or (url.startswith('/') and not url.startswith('//'))):
                raise ConfiguracionPagoExternoError('Recepción aún debe configurar el QR de Yape y Plin.')
            return {'qr_url': url}
        try:
            enlaces = json.loads(self.settings.pagos_mercado_pago_enlaces or '{}')
            importes = {}
            for monto, url in enlaces.items():
                parsed = urlsplit(url)
                valor = Decimal(monto)
                centavos = cents(valor)
                if (centavos <= 0 or valor != Decimal(centavos) / 100 or centavos in importes
                        or parsed.scheme != 'https' or parsed.hostname not in DOMINIOS_MERCADO_PAGO
                        or parsed.username or '\\' in url):
                    raise ValueError('Enlace o importe inválido')
                importes[centavos] = url
        except (InvalidOperation, TypeError, ValueError, AttributeError, OverflowError) as error:
            raise ConfiguracionPagoExternoError('Recepción debe revisar la configuración de los enlaces de Mercado Pago.') from error
        if not importes:
            raise ConfiguracionPagoExternoError('Recepción aún debe configurar los enlaces de Mercado Pago.')
        return {'enlaces': importes}

    def pago(self, medio, monto, instrucciones):
        if medio == 'yape_plin':
            destino = instrucciones
        else:
            link = instrucciones['enlaces'].get(cents(monto))
            if not link:
                raise ValueError('No hay un enlace de Mercado Pago para este importe. Consulta con recepción.')
            destino = {'enlace': link}
        return {'revision_pendiente': True, 'medio_pago': medio, 'amount': monto, **destino}

    def registrar(self, payload, *, admin=False):
        medio = payload['medio_pago']
        instrucciones = self.instrucciones(medio)
        payload = {**payload, 'importes_mercado_pago': instrucciones.get('enlaces', {}).keys()}
        if admin:
            registro = self.clients.register_admin_client(payload)
            return {**registro, 'payment': self.pago(medio, registro['membresia']['monto_pago'], instrucciones)}
        solicitud = self.clients.prepare_public_registration(payload)['preregistro']
        return {'preregistro': public_request(solicitud),
                'payment': self.pago(medio, solicitud['monto_pago'], instrucciones)}

    def retomar(self, id_cliente):
        membresia = self.clients.get_admin_payment_registration(id_cliente)['membresia']
        medio = membresia.get('metodo_pago')
        if medio not in MEDIOS_EXTERNOS:
            raise ValueError('La membresía no tiene un pago por QR ni por enlace de Mercado Pago.')
        return self.pago(medio, membresia['monto_pago'], self.instrucciones(medio))

    def solicitudes(self):
        return self.clients.gym.executor.query(SolicitudesPagoExternoQuery())

    def confirmar(self, datos, *, token=None, id_cliente=None):
        if token:
            operacion = ConfirmarSolicitudPagoExternoCommand(token, **datos)
        else:
            operacion = ConfirmarMembresiaPagoExternoCommand(id_cliente, **datos)
        resultado = self.clients.gym.executor.execute(operacion)
        notificacion = self.notify(self.settings, self.clients, resultado, 'payment')
        return {'id_cliente': resultado['cliente']['id_cliente'], 'notification': notificacion}
