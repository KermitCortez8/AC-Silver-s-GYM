"""Plazos de asistencia: las visitas generales vencidas se cierran a las tres horas."""
from datetime import datetime, timedelta
from domain.services.attendance_status import LIMA


def general_deadline(row):
    start = datetime.fromisoformat(f"{row['fecha']}T{row.get('hora_entrada') or row['hora']}")
    return start.replace(tzinfo=LIMA) + timedelta(hours=3)


def reconcile_attendance(rows, now):
    changed = 0
    for row in rows:
        if row.get('anulado') or row.get('hora_salida'):
            continue
        general = row.get('servicio') == 'gimnasio'
        deadline = general_deadline(row) if general else (
            datetime.fromisoformat(row['limite_salida']) if row.get('limite_salida') else None)
        if deadline is None:
            continue
        deadline = deadline.replace(tzinfo=LIMA) if deadline.tzinfo is None else deadline
        if general:
            row['limite_salida'] = deadline.isoformat()
        if now <= deadline or (not general and row.get('estado_asistencia') == 'incompleta'):
            continue
        previous = {k: row.get(k) for k in ('estado_asistencia', 'hora_salida', 'fecha_salida')}
        row['estado_asistencia'] = 'incompleta'
        if general:
            row.update(hora_salida=deadline.strftime('%H:%M:%S'), fecha_salida=deadline.date().isoformat(),
                       cierre_automatico=True, salida_tardia=False, version=int(row.get('version') or 0) + 1)
        row['auditoria'] = [*row.get('auditoria', []), {
            'accion': 'cierre_automatico' if general else 'incompleta_automatica',
            'actor_id': 'sistema', 'actor_nombre': 'Sistema', 'fecha': now.isoformat(),
            'motivo': 'Visita general sin salida después de tres horas desde la entrada.' if general
                      else 'Se superó el límite de salida sin registrar la salida.',
            'antes': previous,
            'despues': {k: row.get(k) for k in ('estado_asistencia', 'hora_salida', 'fecha_salida', 'cierre_automatico')},
        }]
        changed += 1
    return changed
