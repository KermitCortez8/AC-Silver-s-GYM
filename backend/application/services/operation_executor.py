"""Puente tipado entre operaciones de aplicación y el puerto de persistencia."""
from typing import TypeVar
from application.operations.contracts import GymCommand, GymQuery
from application.ports.gym_repository import GymRepository
from domain.ports import PasswordHasher

T = TypeVar("T")


class OperationExecutor:
    def __init__(self, repository: GymRepository, passwords: PasswordHasher):
        self.repository, self.passwords = repository, passwords

    def query(self, query: GymQuery[T]) -> T:
        return self.repository.query(query, self.passwords)

    def execute(self, command: GymCommand[T]) -> T:
        return self.repository.execute(command, self.passwords)
