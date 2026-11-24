"""Registro atómico de comprobantes que recepción verificó en el proveedor."""
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from application.operations.preregistrations import REGISTRATION_RESOURCES
from domain.errors import EntityNotFound
from domain.models.resources import Resource
from domain.services.preregistration_rules import PreregistrationRules
from domain.services.registro_pago_externo import MEDIOS_EXTERNOS, referencia_externa


@dataclass(frozen=True)
class SolicitudesPagoExternoQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple] = (Resource.PREREGISTROS,)

    def run(self, rules):
        campos = ('token', 'nombre', 'dni', 'monto_pago', 'medio_pago')
        solicitudes = [row for row in rules.context.state.get('preregistros', [])
                       if row.get('medio_pago') in MEDIOS_EXTERNOS and row['estado'] != 'CONVERTIDO']
        return [{campo: row[campo] for campo in campos}
                for row in sorted(solicitudes, key=lambda row: row['creado_en'], reverse=True)]


@dataclass(frozen=True)
class ConfirmarSolicitudPagoExternoCommand:
    operation_kind: ClassVar[str] = 'command'
    resources: ClassVar[tuple] = REGISTRATION_RESOURCES
    token: str
    operacion: str
    monto_recibido: Decimal

    def run(self, rules):
        preregistros = PreregistrationRules(rules)
        row = preregistros.get(self.token)
        medio = row.get('medio_pago')
        if medio not in MEDIOS_EXTERNOS:
            raise ValueError('La solicitud requiere confirmación de Stripe.')
        referencia = referencia_externa(rules.context.state, medio, self.operacion, row['monto_pago'],
                                        self.monto_recibido, row.get('id_membresia'))
        return preregistros.convert(self.token, int(row['intento']), referencia, self.monto_recibido, medio)


@dataclass(frozen=True)
class ConfirmarMembresiaPagoExternoCommand:
    operation_kind: ClassVar[str] = 'command'
    resources: ClassVar[tuple] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA)
    id_cliente: int
    id_membresia: int
    operacion: str
    monto_recibido: Decimal

    def run(self, rules):
        membresia = next((m for m in rules.memberships.membresias_por_cliente(self.id_cliente)
                          if m['id_membresia'] == self.id_membresia), None)
        if not membresia:
            raise EntityNotFound('Membresía no encontrada')
        medio = membresia.get('metodo_pago')
        if medio not in MEDIOS_EXTERNOS:
            raise ValueError('La membresía no tiene un pago externo pendiente.')
        referencia = referencia_externa(rules.context.state, medio, self.operacion, membresia['monto_pago'],
                                        self.monto_recibido, self.id_membresia)
        return rules.memberships.confirmar_pago_cliente_publico(self.id_cliente, {
            'id_membresia': self.id_membresia, 'monto_pago': self.monto_recibido,
            'metodo_pago': medio, 'referencia_pago': referencia,
        })
