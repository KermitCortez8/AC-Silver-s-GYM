"""Contratos de ejecución sin callbacks sobre un diccionario global."""
from __future__ import annotations
from typing import ClassVar, Protocol, TypeVar, TypeAlias
from domain.models.resources import Resource
from domain.services.domain_components import DomainComponents

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
Record: TypeAlias = dict[str, JsonValue]
Identifier: TypeAlias = str | int
T_co = TypeVar("T_co", covariant=True)


class GymQuery(Protocol[T_co]):
    resources: ClassVar[tuple[Resource, ...]]
    def run(self, rules: DomainComponents) -> T_co: ...


class GymCommand(Protocol[T_co]):
    resources: ClassVar[tuple[Resource, ...]]
    def run(self, rules: DomainComponents) -> T_co: ...
