"""Unidades de trabajo del preregistro público, incluida su conversión a cliente."""
from dataclasses import dataclass
from typing import ClassVar

from domain.models.resources import Resource
from domain.services.preregistration_rules import PreregistrationRules

REGISTRATION_RESOURCES = (Resource.PREREGISTROS, Resource.CLIENTES, Resource.MEMBRESIA,
                          Resource.USUARIO, Resource.PLANES_MEMBRESIA, Resource.PROMOCIONES)


@dataclass(frozen=True)
class PreparePreregistrationCommand:
    operation_kind: ClassVar[str] = 'command'
    resources: ClassVar[tuple] = REGISTRATION_RESOURCES
    payload: dict
    token: str
    now: str

    def run(self, rules):
        return PreregistrationRules(rules).prepare(self.payload, self.token, self.now)


@dataclass(frozen=True)
class PreregistrationQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple] = (Resource.PREREGISTROS,)
    token: str

    def run(self, rules):
        return PreregistrationRules(rules).get(self.token)


@dataclass(frozen=True)
class DuePreregistrationsQuery:
    operation_kind: ClassVar[str] = 'query'
    resources: ClassVar[tuple] = (Resource.PREREGISTROS,)
    now: str

    def run(self, rules):
        from datetime import datetime
        return [row for row in rules.context.state.get('preregistros', [])
                if row['estado'] == 'PENDIENTE' and datetime.fromisoformat(row['expira_en']) <= datetime.fromisoformat(self.now)][:50]


@dataclass(frozen=True)
class AttachPreregistrationCheckoutCommand:
    operation_kind: ClassVar[str] = 'command'
    resources: ClassVar[tuple] = (Resource.PREREGISTROS,)
    token: str
    attempt: int
    session_id: str
    checkout_url: str

    def run(self, rules):
        return PreregistrationRules(rules).attach(self.token, self.attempt, self.session_id, self.checkout_url)


@dataclass(frozen=True)
class ExpirePreregistrationCommand:
    operation_kind: ClassVar[str] = 'command'
    resources: ClassVar[tuple] = (Resource.PREREGISTROS, Resource.PROMOCIONES)
    token: str
    attempt: int
    session_id: str

    def run(self, rules):
        return PreregistrationRules(rules).expire(self.token, self.attempt, self.session_id)


@dataclass(frozen=True)
class ConvertPreregistrationCommand:
    operation_kind: ClassVar[str] = 'command'
    resources: ClassVar[tuple] = REGISTRATION_RESOURCES
    token: str
    attempt: int
    session_id: str
    amount: float

    def run(self, rules):
        return PreregistrationRules(rules).convert(self.token, self.attempt, self.session_id, self.amount)
