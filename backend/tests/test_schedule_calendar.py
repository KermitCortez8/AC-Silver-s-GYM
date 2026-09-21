from datetime import date, datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from config import Settings
from routes.attendance_routes import week
from services.attendance_service import AttendanceService
from services.schedule_notifications import schedule_email
from test_schedule_enrollment import _schedule_service


def test_week_attendance_matches_date_and_client_across_month_boundary():
    gym = _schedule_service()
    gym.state['matriculas_horario'] = [
        {'id_matricula': 20, 'id_cliente': 1, 'id_horario_servicio': 10,
         'estado': 'ACTIVA', 'fecha_matricula': '2026-08-01'},
    ]
    gym.state['asistencia'] = [
        {'id_asistencia': 1, 'id_cliente': 1, 'id_matricula': 20, 'fecha': '2026-08-31', 'hora_entrada': '08:00'},
        {'id_asistencia': 2, 'id_cliente': 2, 'id_matricula': 20, 'fecha': '2026-09-07', 'hora_entrada': '08:05'},
    ]
    attendance = AttendanceService(gym, clock=lambda: datetime(2026, 9, 7, 8, 30, tzinfo=ZoneInfo('America/Lima')))
    user = SimpleNamespace(role='user', id_cliente=1)
    previous = week(date(2026, 9, 1), user, attendance)
    current = week(date(2026, 9, 7), user, attendance)
    assert previous['horarios'][0]['fecha'] == '2026-08-31'
    assert previous['horarios'][0]['asistencia']['id_asistencia'] == 1
    assert previous['visitas_por_fecha'] == {'2026-08-31': 1}
    assert current['horarios'][0]['fecha'] == '2026-09-07'
    assert current['horarios'][0]['asistencia'] is None
    assert current['visitas'] == 0
    assert current['visitas_por_fecha'] == {}


def test_reminder_opens_the_class_date_in_peru_even_when_utc_is_next_month():
    settings = Settings(email_from='gym@example.com', resend_api_key='re_test', frontend_public_url='https://gym.example.com')
    data = {'event_type': 'reminder', 'correo': 'client@example.com', 'nombre': 'Ana',
            'servicio': 'fitness', 'dia': 'lunes', 'hora_inicio': '23:00', 'hora_fin': '23:59',
            'class_start': '2026-09-01T04:00:00+00:00'}
    mail = schedule_email(settings, data)
    assert '31/08/2026' in mail['text']
    assert '/user/schedule?fecha=2026-08-31' in mail['text']
    assert '/user/schedule?fecha=2026-08-31' in mail['html']
    assert 'Perú (America/Lima)' in mail['text']


def test_enrollment_email_keeps_weekly_recurrence():
    settings = Settings(email_from='gym@example.com', resend_api_key='re_test', frontend_public_url='https://gym.example.com')
    mail = schedule_email(settings, {'event_type': 'enrollment', 'correo': 'client@example.com',
        'servicio': 'fitness', 'dia': 'lunes', 'hora_inicio': '08:00', 'hora_fin': '09:00'})
    assert 'Cada lunes' in mail['text']
    assert '?fecha=' not in mail['text']
