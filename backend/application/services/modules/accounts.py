"""Operaciones de aplicación del módulo accounts."""
from __future__ import annotations

from typing import Any


class AccountsOperations:
    def get_usuario(self, id_usuario: Any) -> dict[str, Any] | None:
        return self._execute("get_usuario", False, id_usuario)

    def get_usuario_by_email(self, email: str) -> dict[str, Any] | None:
        return self._execute("get_usuario_by_email", False, email)

    def usuarios(self) -> list[dict[str, Any]]:
        return self._execute("usuarios", False)

    def usuarios_normalized(self) -> list[dict[str, Any]]:
        return self._execute("usuarios_normalized", False)

    def upsert_usuario(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("upsert_usuario", True, payload)

    def delete_usuario(self, id_usuario: Any) -> None:
        return self._execute("delete_usuario", True, id_usuario)

    def clientes(self) -> list[dict[str, Any]]:
        return self._execute("clientes", False)

    def clientes_normalized(self) -> list[dict[str, Any]]:
        return self._execute("clientes_normalized", False)

    def upsert_cliente(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("upsert_cliente", True, payload)

    def get_cliente(self, id_cliente: int) -> dict[str, Any] | None:
        return self._execute("get_cliente", False, id_cliente)

    def get_cliente_by_dni(self, dni: str) -> dict[str, Any] | None:
        return self._execute("get_cliente_by_dni", False, dni)

    def get_cliente_by_email(self, email: str) -> dict[str, Any] | None:
        return self._execute("get_cliente_by_email", False, email)

    def get_account_by_google_sub(self, subject: str) -> tuple[str, dict[str, Any]] | None:
        return self._execute("get_account_by_google_sub", False, subject)

    def link_google_account(self, kind: str, account_id: str, subject: str) -> dict[str, Any]:
        return self._execute("link_google_account", True, kind, account_id, subject)

    def authenticate_usuario_password(self, correo: str, password: str) -> dict[str, Any] | None:
        return self._execute("authenticate_usuario_password", False, correo, password)

    def authenticate_cliente_password(self, correo: str, password: str) -> dict[str, Any] | None:
        return self._execute("authenticate_cliente_password", False, correo, password)

    def delete_cliente(self, id_cliente: int) -> None:
        return self._execute("delete_cliente", True, id_cliente)

    def registrar_cliente_publico(self, payload: dict[str, Any], *, origen_registro: str='PUBLICO') -> dict[str, Any]:
        return self._execute("registrar_cliente_publico", True, payload, origen_registro=origen_registro)

    def confirmar_pago_cliente_publico(self, id_cliente: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._execute("confirmar_pago_cliente_publico", True, id_cliente, payload)

    def confirmar_pago_manual_cliente(self, id_cliente: int) -> dict[str, Any]:
        return self._execute("confirmar_pago_manual_cliente", True, id_cliente)
