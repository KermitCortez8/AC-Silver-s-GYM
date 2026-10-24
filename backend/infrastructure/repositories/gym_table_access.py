"""Consultas de tablas y comprobación explícita del esquema remoto."""
from dataclasses import dataclass, field
from typing import Any
from application.errors import SchemaNotReady
from infrastructure.http_transport import database_code
from infrastructure.repositories.schema_policy import missing_column, prepare_write
from infrastructure.repositories.gym_tables import PAYMENT_COLUMNS, STORE_PAYMENT_COLUMNS


@dataclass
class TableMetadata:
    columns: dict[str, set[str]] = field(default_factory=dict)
    missing_tables: set[str] = field(default_factory=set)


class GymTableAccess:

    def __init__(self, database, metadata):
        self.database, self.metadata = database, metadata

    def validate_payment_schema(self) -> None:
        try:
            self.database.validate_columns("MEMBRESIA", PAYMENT_COLUMNS)
        except RuntimeError as error:
            if missing_column(error):
                raise SchemaNotReady("001_add_membership_payment_fields.sql") from error
            raise

    def validate_store_payment_schema(self) -> None:
        """Falla al arrancar si falta la migración 009, en vez de perder datos en silencio."""
        try:
            self.database.validate_columns("VENTAS", STORE_PAYMENT_COLUMNS)
        except RuntimeError as error:
            if missing_column(error):
                raise SchemaNotReady("009_add_store_order_payment_fields.sql") from error
            raise

    def remember_columns(self, table: str, rows: list[dict[str, Any]]) -> None:
        if rows:
            self.metadata.columns[table] = set(rows[0].keys())
        self.metadata.missing_tables.discard(table)

    def select_required(self, table: str, order: str | None = None) -> list[dict[str, Any]]:
        rows = self.database.select_all(table, order=order or "1")
        self.remember_columns(table, rows)
        return rows

    def select_optional(self, table: str, order: str | None = None) -> list[dict[str, Any]]:
        try:
            rows = self.database.select_all(table, order=order or "1")
            self.remember_columns(table, rows)
            return rows
        except RuntimeError as error:
            if database_code(error) in {"PGRST205", "42P01"}:
                self.metadata.missing_tables.add(table)
                return []
            raise

    def prepare_write(self, table: str, body: dict[str, Any]) -> dict[str, Any]:
        return prepare_write(table, body, self.metadata.columns, lambda table, columns: self.database.validate_columns(table, columns))

    def validate_admin_registration_schema(self) -> None:
        self.prepare_write("CLIENTES", {"origen_registro": "ADMIN"})
