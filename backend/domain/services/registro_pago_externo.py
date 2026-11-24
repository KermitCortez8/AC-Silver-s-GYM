"""Reglas de importe y comprobante para cobros revisados por recepción."""
import re

from domain.money import cents

MEDIOS_EXTERNOS = {'yape_plin', 'mercado_pago'}


def validar_importe_enlace(payload, monto):
    if payload.get('medio_pago') == 'mercado_pago' and cents(monto) not in payload['importes_mercado_pago']:
        raise ValueError('No hay un enlace de Mercado Pago para este importe. Elige otro medio o consulta con recepción.')


def referencia_externa(estado, medio, comprobante, esperado, recibido, id_membresia=None):
    if cents(recibido) <= 0 or cents(esperado) != cents(recibido):
        raise ValueError('El monto recibido debe coincidir con el importe de la membresía.')
    numero = comprobante.strip().upper().replace(' ', '').replace('-', '')
    if not re.fullmatch(r'[A-Z0-9]{5,64}', numero):
        raise ValueError('Ingresa el número completo de la operación, de 5 a 64 letras o dígitos.')
    referencia = f'{medio}:{numero}'
    if any(m.get('referencia_pago') == referencia and m.get('id_membresia') != id_membresia
           for m in estado.get('membresia', [])):
        raise ValueError('Esta operación ya fue registrada en otra membresía.')
    return referencia
