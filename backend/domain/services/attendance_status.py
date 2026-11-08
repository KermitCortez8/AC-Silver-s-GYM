"""Estado temporal de una visita; el límite guardado conserva el horario original."""
from datetime import datetime
from zoneinfo import ZoneInfo

LIMA = ZoneInfo("America/Lima")
LATE_EXIT_MESSAGE = "Ya pasó más de una hora desde el término de la clase. La asistencia queda incompleta."


def attendance_status(row, now=None):
    if row.get("anulado"):
        return "anulada"
    if row.get("servicio") != "gimnasio" and row.get("limite_salida"):
        deadline = datetime.fromisoformat(str(row["limite_salida"]))
        deadline = deadline.replace(tzinfo=LIMA) if deadline.tzinfo is None else deadline
        if row.get("hora_salida"):
            end = datetime.fromisoformat(f"{row.get('fecha_salida') or row['fecha']}T{row['hora_salida']}").replace(tzinfo=LIMA)
        else:
            end = now or datetime.now(LIMA)
        if end > deadline:
            return "incompleta"
    if row.get("salida_tardia"):
        return "incompleta"
    return "completada" if row.get("hora_salida") else "dentro"
