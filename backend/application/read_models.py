"""Datos de lectura desacoplados del estado interno del repositorio."""
from dataclasses import dataclass


@dataclass(frozen=True)
class MembershipPaymentData:
    clients: list[dict]
    plans: list[dict]
    memberships: list[dict]


@dataclass(frozen=True)
class AttendanceHistoryData:
    records: list[dict]
    clients: list[dict]


@dataclass(frozen=True)
class AttendanceCriteria:
    client_id: int | None = None
    dni: str = ""
    since: str = ""
    until: str = ""
    service: str = ""
    status: str = ""
    kind: str = ""
    include_annulled: bool = True


@dataclass(frozen=True)
class PageRequest:
    page: int = 1
    page_size: int = 15

    def __post_init__(self):
        if self.page < 1 or not 1 <= self.page_size <= 100:
            raise ValueError("Paginación inválida")

    @property
    def offset(self):
        return (self.page - 1) * self.page_size


@dataclass(frozen=True)
class AttendancePage:
    records: list[dict]
    clients: list[dict]
    total: int
