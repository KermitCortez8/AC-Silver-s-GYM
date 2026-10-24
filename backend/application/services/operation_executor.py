"""Puente tipado entre operaciones de aplicación y el puerto de persistencia."""
from typing import TypeVar
from application.operations.contracts import GymCommand, GymQuery
from application.ports.gym_repository import GymRepository
from domain.ports import PasswordHasher
from domain.models.resources import Resource

T = TypeVar("T")


class OperationExecutor:
    def __init__(self, repository: GymRepository, passwords: PasswordHasher):
        self.repository, self.passwords = repository, passwords

    def query(self, query: GymQuery[T]) -> T:
        self._validate(query, "query")
        return self.repository.query(query, self.passwords)

    def execute(self, command: GymCommand[T]) -> T:
        self._validate(command, "command")
        return self.repository.execute(command, self.passwords)

    @staticmethod
    def _validate(operation, kind):
        if (getattr(operation, "operation_kind", None) != kind
                or not isinstance(getattr(operation, "resources", None), tuple)
                or not all(isinstance(resource, Resource) for resource in operation.resources)
                or not callable(getattr(operation, "run", None))):
            raise ValueError("La operación no cumple el contrato de " + kind)
