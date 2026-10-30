"""La programación se repite; cada matrícula reserva una única fecha de clase."""
from datetime import date, timedelta

DAYS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")


def next_session(schedule, reference):
    day = date.fromisoformat(str(reference)[:10])
    if schedule.get("dia") not in DAYS:
        raise ValueError("El horario no tiene un día válido.")
    return (day + timedelta(days=(DAYS.index(schedule["dia"]) - day.weekday()) % 7)).isoformat()


def enrollment_session(enrollment, schedule):
    """Compatibilidad histórica fija desde el alta, nunca desde el reloj actual."""
    try:
        if enrollment.get("fecha_clase"):
            return date.fromisoformat(str(enrollment["fecha_clase"])).isoformat()
        return next_session(schedule, enrollment.get("fecha_matricula") or "")
    except (ValueError, TypeError):
        return ""


def validate_session(schedule, value, today):
    try:
        selected = date.fromisoformat(str(value)) if value else date.fromisoformat(next_session(schedule, today))
    except (ValueError, TypeError) as error:
        raise ValueError("Selecciona una fecha de clase válida.") from error
    if selected.isoformat() < today:
        raise ValueError("No puedes matricular una clase de una fecha pasada.")
    if DAYS[selected.weekday()] != schedule.get("dia"):
        raise ValueError("La fecha de clase no corresponde al día del horario.")
    return selected.isoformat()
