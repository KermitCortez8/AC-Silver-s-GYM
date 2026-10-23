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
