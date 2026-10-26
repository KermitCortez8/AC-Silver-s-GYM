"""Operaciones de aplicación del módulo accounts."""
from __future__ import annotations

from typing import Any
from application.operations.accounts import (
    GetUsuarioQuery, GetUsuarioByEmailQuery, UsuariosQuery, UsuariosNormalizedQuery, UpsertUsuarioCommand, DeleteUsuarioCommand, ClientesQuery, ClientesNormalizedQuery, UpsertClienteCommand, GetClienteQuery, GetClienteByDniQuery, GetClienteByEmailQuery, GetAccountByGoogleSubQuery, LinkGoogleAccountCommand, AuthenticateUsuarioPasswordQuery, AuthenticateClientePasswordQuery, DeleteClienteCommand, RegistrarClientePublicoCommand, ConfirmarPagoClientePublicoCommand, ConfirmarPagoManualClienteCommand
)


class AccountsOperations:
    def __init__(self, executor):
        self.executor = executor

    def get_usuario(self, id_usuario: Any) -> dict[str, Any] | None:
        return self.executor.query(GetUsuarioQuery(id_usuario))

    def get_usuario_by_email(self, email: str) -> dict[str, Any] | None:
        return self.executor.query(GetUsuarioByEmailQuery(email))

    def usuarios(self) -> list[dict[str, Any]]:
        return self.executor.query(UsuariosQuery())

    def usuarios_normalized(self) -> list[dict[str, Any]]:
        return self.executor.query(UsuariosNormalizedQuery())

    def upsert_usuario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(UpsertUsuarioCommand(payload))

    def delete_usuario(self, id_usuario: Any) -> None:
        return self.executor.execute(DeleteUsuarioCommand(id_usuario))

    def clientes(self) -> list[dict[str, Any]]:
        return self.executor.query(ClientesQuery())

    def clientes_normalized(self) -> list[dict[str, Any]]:
        return self.executor.query(ClientesNormalizedQuery())

    def upsert_cliente(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(UpsertClienteCommand(payload))

    def get_cliente(self, id_cliente: int) -> dict[str, Any] | None:
        return self.executor.query(GetClienteQuery(id_cliente))

    def get_cliente_by_dni(self, dni: str) -> dict[str, Any] | None:
        return self.executor.query(GetClienteByDniQuery(dni))

    def get_cliente_by_email(self, email: str) -> dict[str, Any] | None:
        return self.executor.query(GetClienteByEmailQuery(email))

    def get_account_by_google_sub(self, subject: str) -> tuple[str, dict[str, Any]] | None:
        return self.executor.query(GetAccountByGoogleSubQuery(subject))

    def link_google_account(self, kind: str, account_id: str, subject: str) -> dict[str, Any]:
        return self.executor.execute(LinkGoogleAccountCommand(kind, account_id, subject))

    def authenticate_usuario_password(self, correo: str, password: str) -> dict[str, Any] | None:
        return self.executor.query(AuthenticateUsuarioPasswordQuery(correo, password))

    def authenticate_cliente_password(self, correo: str, password: str) -> dict[str, Any] | None:
        return self.executor.query(AuthenticateClientePasswordQuery(correo, password))

    def delete_cliente(self, id_cliente: int) -> None:
        return self.executor.execute(DeleteClienteCommand(id_cliente))

    def registrar_cliente_publico(self, payload: dict[str, Any], *, origen_registro: str='PUBLICO') -> dict[str, Any]:
        return self.executor.execute(RegistrarClientePublicoCommand(payload, origen_registro=origen_registro))

    def confirmar_pago_cliente_publico(self, id_cliente: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.executor.execute(ConfirmarPagoClientePublicoCommand(id_cliente, payload))

    def confirmar_pago_manual_cliente(self, id_cliente: int) -> dict[str, Any]:
        return self.executor.execute(ConfirmarPagoManualClienteCommand(id_cliente))
