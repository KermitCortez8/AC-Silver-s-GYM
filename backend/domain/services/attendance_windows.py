"""Ventanas del aviso entre visitas: no sustituyen las reglas de admisión."""
from datetime import datetime, timedelta

from domain.services.attendance_status import LIMA

NEAR_ATTENDANCE_MINUTES = 30


def _near(start, end, now):
    margin = timedelta(minutes=NEAR_ATTENDANCE_MINUTES)
    return start <= end and start - margin <= now <= end + margin


def schedule_near_now(schedule, day, now):
    try:
        start = datetime.fromisoformat(f"{day}T{schedule['hora_inicio']}").replace(tzinfo=LIMA)
        end = datetime.fromisoformat(f"{day}T{schedule['hora_fin']}").replace(tzinfo=LIMA)
        return _near(start, end, now)
    except (ValueError, TypeError, KeyError):
        return False


def class_visit_near_now(row, now):
    try:
        start = datetime.fromisoformat(f"{row['fecha']}T{row.get('hora_entrada') or row['hora']}").replace(tzinfo=LIMA)
        # El plazo guardado es el fin original más una hora. No usar un horario editado.
        deadline = datetime.fromisoformat(row['limite_salida'])
        deadline = deadline.replace(tzinfo=LIMA) if deadline.tzinfo is None else deadline
        return _near(start, deadline - timedelta(hours=1), now)
    except (ValueError, TypeError, KeyError):
        return False
