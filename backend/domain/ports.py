"""Capacidades externas que necesitan las reglas, sin conocer sus proveedores."""
from typing import Protocol


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, encoded: str) -> bool: ...
