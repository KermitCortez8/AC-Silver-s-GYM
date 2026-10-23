"""Invariantes de entrada reutilizables, sin dependencias de HTTP o persistencia."""
from datetime import date, time
from decimal import Decimal, InvalidOperation
import re


def required_text(value, label="Nombre"):
    value = str(value or "").strip()
    if not value:
        raise ValueError(f"{label} es obligatorio")
    return value


def email_address(value):
    value = str(value or "").strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValueError("Correo inválido")
    return value


def nonnegative(value, label="Valor"):
    try:
        amount = Decimal(str(value))
    except (ValueError, InvalidOperation):
        raise ValueError(f"{label} debe ser un número válido") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{label} no puede ser negativo ni infinito")
    return value


def civil_date(value):
    text = str(value or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise ValueError("Fecha inválida; usa AAAA-MM-DD")
    try:
        date.fromisoformat(text)
    except ValueError:
        raise ValueError("Fecha inválida; usa AAAA-MM-DD") from None
    return text


def clock_time(value):
    text = str(value or "").strip()
    if not re.fullmatch(r"\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?", text):
        raise ValueError("Hora inválida; usa HH:MM o HH:MM:SS")
    try:
        time.fromisoformat(text)
    except ValueError:
        raise ValueError("Hora inválida; usa HH:MM o HH:MM:SS") from None
    return text


def date_range(start, end):
    if start:
        civil_date(start)
    if end:
        civil_date(end)
    if start and end and start > end:
        raise ValueError("La fecha de fin debe ser igual o posterior a la de inicio")


def time_range(start, end):
    if start and end and time.fromisoformat(clock_time(start)) >= time.fromisoformat(clock_time(end)):
        raise ValueError("La hora de fin debe ser posterior a la de inicio")
