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
    if not value:
        raise ValueError("El correo es obligatorio.")
    parts = value.split("@")
    local, domain = parts[0], parts[1] if len(parts) == 2 else ""
    if (len(parts) != 2 or len(value) > 254 or len(local) > 64
            or not re.fullmatch(r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*", local, re.I)
            or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+", domain, re.I)):
        raise ValueError("Ingresa un correo válido, por ejemplo nombre@gmail.com.")
    return value.lower()


def account_email(value):
    email = email_address(value)
    if email.rsplit("@", 1)[1] not in {"gmail.com", "hotmail.com"}:
        raise ValueError("Solo se permiten correos @gmail.com o @hotmail.com.")
    return email


def dni_number(value, required=False):
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError("El DNI es obligatorio.")
        return ""
    if not re.fullmatch(r"[0-9]{8}", text):
        raise ValueError("El DNI debe tener exactamente 8 dígitos.")
    return text


def phone_number(value, required=False):
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError("El teléfono es obligatorio.")
        return ""
    if not re.fullmatch(r"[0-9]{7,9}", text):
        raise ValueError("El teléfono debe tener entre 7 y 9 dígitos, sin espacios ni letras.")
    return text


def nonnegative(value, label="Valor"):
    try:
        amount = Decimal(str(value))
    except (ValueError, InvalidOperation):
        raise ValueError(f"{label} debe ser un número válido") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{label} no puede ser negativo ni infinito")
    return value


def integer_quantity(value, label="Cantidad", minimum=0):
    """Reject lossy coercions, signs and exponents before changing stock."""
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
        raise ValueError(f"{label} debe contener solo dígitos enteros")
    quantity = int(value)
    if not minimum <= quantity <= 2147483647:
        raise ValueError(f"{label} debe estar entre {minimum} y 2147483647")
    return quantity


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


def identifier(value, *, client=False):
    if value is None:
        return value
    if isinstance(value, bool):
        raise ValueError("El identificador debe ser positivo")
    text = str(value).strip()
    if not text:
        raise ValueError("El identificador no puede estar vacío")
    if not client and (code := re.fullmatch(r"(?:SG[A-Z]{2,3}|USSG)(\d+)", text, re.IGNORECASE)):
        if int(code.group(1)) <= 0:
            raise ValueError("El identificador debe ser positivo")
    if client:
        match = re.fullmatch(r"(?:SGCLI|cliente-)?(\d+)", text, re.IGNORECASE)
        if not match or int(match.group(1)) <= 0:
            raise ValueError("El identificador del cliente debe ser positivo")
    elif isinstance(value, (int, float, Decimal)) or re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text):
        numeric = Decimal(text)
        if not numeric.is_finite() or numeric <= 0 or numeric != numeric.to_integral_value():
            raise ValueError("El identificador debe ser un entero positivo")
    return value


def validate_exercises(entries):
    if entries is None:
        return
    if not isinstance(entries, list):
        raise ValueError("Los ejercicios deben ser una lista")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Ejercicio inválido")
        if entry.get("id_ejercicio") is not None:
            identifier(entry["id_ejercicio"])
        if not str(entry.get("nombre_ejercicio") or "").strip() and entry.get("id_ejercicio") is None:
            raise ValueError("El ejercicio necesita un nombre o identificador")
        for field in ("peso_sugerido_kg", "peso_utilizado_kg", "series_completadas", "descanso_segundos"):
            if entry.get(field) is not None:
                nonnegative(entry[field], field)
        if entry.get("series") is not None:
            nonnegative(entry["series"], "Series")
            if int(entry["series"]) < 1:
                raise ValueError("Las series deben ser mayores que cero")
