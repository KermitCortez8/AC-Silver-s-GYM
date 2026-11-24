"""Abre Checkout Pro con una cuenta vendedora de prueba de Perú."""
from urllib.parse import urlsplit

import httpx

from application.errors import ConfiguracionPagoExternoError


class MercadoPagoCheckoutPrueba:
    def __init__(self, token: str):
        self.token = token

    def crear_enlace(self, plan: str, importe: float) -> str:
        if not self.token:
            raise ConfiguracionPagoExternoError('Falta configurar el Access Token de prueba de Mercado Pago.')

        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            cuenta = httpx.get('https://api.mercadopago.com/users/me', headers=headers, timeout=8)
            cuenta.raise_for_status()
            vendedor = cuenta.json()
            if vendedor.get('site_id') != 'MPE' or 'test_user' not in vendedor.get('tags', []):
                raise ConfiguracionPagoExternoError('Usa el Access Token de un vendedor de prueba de Mercado Pago Perú.')

            response = httpx.post(
                'https://api.mercadopago.com/checkout/preferences',
                headers=headers,
                json={'items': [{
                    'title': f'Membresía de prueba · {plan}',
                    'quantity': 1,
                    'currency_id': 'PEN',
                    'unit_price': importe,
                }]},
                timeout=8,
            )
            response.raise_for_status()
            preferencia = response.json()
            enlace = preferencia['init_point']
            parsed = urlsplit(enlace)
            if (preferencia['collector_id'] != vendedor['id'] or parsed.scheme != 'https'
                    or parsed.netloc != 'www.mercadopago.com.pe' or not parsed.path.startswith('/checkout/')
                    or '\\' in enlace):
                raise ValueError('Enlace de pruebas inválido')
        except (httpx.HTTPError, KeyError, ValueError, TypeError, AttributeError):
            raise ConfiguracionPagoExternoError(
                'Mercado Pago no generó un enlace de prueba. Revisa las credenciales de Checkout Pro.',
            ) from None
        return enlace
