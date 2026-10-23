"""Consultas y comandos concretos; cada operación declara su unidad de datos."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents
from application.operations.contracts import Record, Identifier


@dataclass(frozen=True)
class GetUsuarioQuery:
    id_usuario: Identifier
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO,)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.accounts.get_usuario(self.id_usuario)


@dataclass(frozen=True)
class GetUsuarioByEmailQuery:
    email: str
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO,)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.accounts.get_usuario_by_email(self.email)


@dataclass(frozen=True)
class UsuariosQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.accounts.usuarios()


@dataclass(frozen=True)
class UsuariosNormalizedQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO,)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.accounts.usuarios_normalized()


@dataclass(frozen=True)
class UpsertUsuarioCommand:
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO,)

    def run(self, rules: DomainComponents) -> Record:
        return rules.accounts.upsert_usuario(self.payload)


@dataclass(frozen=True)
class DeleteUsuarioCommand:
    id_usuario: Identifier
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO,)

    def run(self, rules: DomainComponents) -> None:
        return rules.accounts.delete_usuario(self.id_usuario)


@dataclass(frozen=True)
class ClientesQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.accounts.clientes()


@dataclass(frozen=True)
class ClientesNormalizedQuery:
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA)

    def run(self, rules: DomainComponents) -> list[Record]:
        return rules.accounts.clientes_normalized()


@dataclass(frozen=True)
class UpsertClienteCommand:
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> Record:
        return rules.accounts.upsert_cliente(self.payload)


@dataclass(frozen=True)
class GetClienteQuery:
    id_cliente: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.accounts.get_cliente(self.id_cliente)


@dataclass(frozen=True)
class GetClienteByDniQuery:
    dni: str
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.accounts.get_cliente_by_dni(self.dni)


@dataclass(frozen=True)
class GetClienteByEmailQuery:
    email: str
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.accounts.get_cliente_by_email(self.email)


@dataclass(frozen=True)
class GetAccountByGoogleSubQuery:
    subject: str
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA)

    def run(self, rules: DomainComponents) -> tuple[str, Record] | None:
        return rules.accounts.get_account_by_google_sub(self.subject)


@dataclass(frozen=True)
class LinkGoogleAccountCommand:
    kind: str
    account_id: str
    subject: str
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> Record:
        return rules.accounts.link_google_account(self.kind, self.account_id, self.subject)


@dataclass(frozen=True)
class AuthenticateUsuarioPasswordQuery:
    correo: str
    password: str
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO,)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.accounts.authenticate_usuario_password(self.correo, self.password)


@dataclass(frozen=True)
class AuthenticateClientePasswordQuery:
    correo: str
    password: str
    resources: ClassVar[tuple[Resource, ...]] = (Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA)

    def run(self, rules: DomainComponents) -> Record | None:
        return rules.accounts.authenticate_cliente_password(self.correo, self.password)


@dataclass(frozen=True)
class DeleteClienteCommand:
    id_cliente: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> None:
        return rules.accounts.delete_cliente(self.id_cliente)


@dataclass(frozen=True)
class RegistrarClientePublicoCommand:
    payload: Record
    origen_registro: str = 'PUBLICO'
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> Record:
        return rules.memberships.registrar_cliente_publico(self.payload, origen_registro=self.origen_registro)


@dataclass(frozen=True)
class ConfirmarPagoClientePublicoCommand:
    id_cliente: int
    payload: Record
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> Record:
        return rules.memberships.confirmar_pago_cliente_publico(self.id_cliente, self.payload)


@dataclass(frozen=True)
class ConfirmarPagoManualClienteCommand:
    id_cliente: int
    resources: ClassVar[tuple[Resource, ...]] = (Resource.USUARIO, Resource.CLIENTES, Resource.MEMBRESIA, Resource.PLANES_MEMBRESIA, Resource.PROMOCIONES)

    def run(self, rules: DomainComponents) -> Record:
        return rules.memberships.confirmar_pago_manual_cliente(self.id_cliente)

