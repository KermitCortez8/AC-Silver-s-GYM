"""Recorrido matrícula → entrada administrativa → falta de salida, sin datos externos."""
import json
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import time

import pytest

from tests.test_atomic_transactions_postgres import Postgres
from tests.test_attendance_deadline_postgres import save

pytestmark = pytest.mark.skipif(not os.getenv('GYM_TEST_POSTGRES_CONTAINER'),
    reason='Requiere un PostgreSQL desechable explícito')
BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def database():
    db = Postgres()
    db.sql((BACKEND / 'tests/fixtures/priority_schema.sql').read_text())
    # Se comprueba el contrato de clases (021); el cierre general de 023 es otro flujo.
    for name in ['002_harden_schedule_enrollment.sql', '005_harden_attendance.sql',
                 '006_schedule_email_notifications.sql', '013_general_attendance.sql',
                 '018_attendance_schedule_exit_deadline.sql', '019_schedule_sessions.sql',
                 '021_persist_attendance_status.sql']:
        db.sql((BACKEND / 'migrations' / name).read_text())
    return db


@pytest.fixture(autouse=True)
def clean(database):
    database.sql('''truncate public."CLIENTES", public."USUARIO", public."MEMBRESIA", public."ASISTENCIA",
        public."HORARIOS_SERVICIO", public."MATRICULAS_HORARIO" restart identity cascade;''')
    yield
    if database.sql("select to_regclass('cron.job') is not null;") == 't':
        database.sql("select cron.unschedule(jobid) from cron.job where jobname='silver-gym-incomplete-attendance';")


def enrolled_client(database):
    database.sql('''insert into public."CLIENTES" (id_cliente,"Estado") values (95,true);
        insert into public."MEMBRESIA" (id_membresia,id_cliente,"Estado",estado_pago,"Fecha_Inicio","Fecha_Fin")
        values (100,95,'ACTIVA','PAGADO',
          ((clock_timestamp() at time zone 'America/Lima')::date-1)::text,
          ((clock_timestamp() at time zone 'America/Lima')::date+30)::text);
        insert into public."HORARIOS_SERVICIO" (id_horario_servicio,servicio,dia,hora_inicio,hora_fin,cupos,activo)
        values (24,'cardio',(array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[
          extract(isodow from clock_timestamp() at time zone 'America/Lima')::integer],
          '00:00','23:59:59',1,true);''')
    enrollment = json.loads(database.sql('''set role service_role;
        select public.matricular_cliente_sesion(95,24,(clock_timestamp() at time zone 'America/Lima')::date);'''))
    return {
        'horario': dict(id_cliente=95, id_membresia=100, id_matricula=enrollment['id_matricula'], servicio='cardio'),
        'general': dict(id_cliente=95, id_membresia=100, servicio='gimnasio'),
    }


def save_entry(database, payload):
    return save(database, payload, request_id='00000000-0000-0000-0000-000000000095')


@pytest.mark.parametrize('first_kind', ['general', 'horario'])
def test_rpc_bloquea_otro_tipo_hasta_guardar_salida(database, first_kind):
    payloads = enrolled_client(database)
    other_kind = 'horario' if first_kind == 'general' else 'general'
    first = save_entry(database, payloads[first_kind])
    with pytest.raises(RuntimeError, match='entrada sin salida'):
        save_entry(database, payloads[other_kind])
    assert len(database.rows('ASISTENCIA')) == 1
    closed = save(database, first, 1, 'salida')
    assert closed['hora_salida']
    following = save_entry(database, payloads[other_kind])
    assert following['id_asistencia'] != first['id_asistencia']
    assert len(database.rows('ASISTENCIA')) == 2
    assert sum(not r['hora_salida'] for r in database.rows('ASISTENCIA')) == 1


def test_rpc_entradas_general_y_horario_simultaneas_guardan_solo_una(database):
    payloads = enrolled_client(database)

    def attempt(kind):
        try:
            return save_entry(database, payloads[kind])
        except RuntimeError as error:
            assert 'entrada sin salida' in str(error)
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, ['general', 'horario']))
    assert sum(result is not None for result in results) == 1
    assert len(database.rows('ASISTENCIA')) == 1


@pytest.mark.parametrize('process', ['rpc', 'cron'])
def test_matricula_entrada_admin_y_salida_omitida(database, process):
    if process == 'cron' and database.sql("select exists(select 1 from pg_available_extensions where name='pg_cron');") != 't':
        pytest.skip('Requiere pg_cron para verificar persistencia sin consultas de aplicación')
    database.sql('''insert into public."CLIENTES" (id_cliente,"Nombres","Estado")
        values (95,'Cliente de prueba aislada',true);
        insert into public."USUARIO" (id_usuario,"Rol","Estado") values (1,'admin',true);
        insert into public."MEMBRESIA" (id_membresia,id_cliente,"Estado",estado_pago,"Fecha_Inicio","Fecha_Fin")
        values (100,95,'ACTIVA','PAGADO',
          ((clock_timestamp() at time zone 'America/Lima')::date-1)::text,
          ((clock_timestamp() at time zone 'America/Lima')::date+30)::text);
        insert into public."HORARIOS_SERVICIO" (id_horario_servicio,servicio,dia,hora_inicio,hora_fin,cupos,activo)
        values (24,'cardio',(array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[
          extract(isodow from clock_timestamp() at time zone 'America/Lima')::integer],
          '00:00','23:59:59',1,true);''')
    enrollment = json.loads(database.sql('''set role service_role;
        select public.matricular_cliente_sesion(95,24,(clock_timestamp() at time zone 'America/Lima')::date);'''))
    assert enrollment['id_cliente'] == 95 and enrollment['id_horario_servicio'] == 24
    payload = dict(id_cliente=95, id_membresia=100, id_matricula=enrollment['id_matricula'], servicio='cardio')
    row = save(database, payload)
    assert row['Fecha'] == enrollment['fecha_clase']
    assert row['estado_asistencia'] == 'dentro' and not row['hora_salida']
    assert row['auditoria'][-1]['accion'] == 'entrada'
    assert row['auditoria'][-1]['actor_id'] == '1'
    assert database.sql('''select limite_salida =
        (("Fecha"::date+time '23:59:59'+interval '1 hour') at time zone 'America/Lima')
        from public."ASISTENCIA";''') == 't'
    # El límite exacto todavía se admite. Solo se acelera el plazo en esta base desechable.
    assert database.sql('''select public.estado_visita_asistencia(false,
        limite_salida,null,false,limite_salida) from public."ASISTENCIA";''') == 'dentro'
    database.sql('''update public."ASISTENCIA" set limite_salida=clock_timestamp()+interval '2 seconds';''')
    if process == 'cron':
        for _ in range(2):
            database.sql((BACKEND / 'migrations/022_attendance_status_cron.sql').read_text())
        assert database.sql("select count(*) from cron.job where jobname='silver-gym-incomplete-attendance' and active;") == '1'
    until = time.monotonic() + 30
    while time.monotonic() < until:
        if process == 'rpc':
            database.sql('set role service_role; select public.marcar_asistencias_incompletas();')
        persisted = database.rows('ASISTENCIA')[0]
        if persisted['estado_asistencia'] == 'incompleta':
            break
        time.sleep(.5)
    assert persisted['estado_asistencia'] == 'incompleta'
    assert not persisted['hora_salida'] and not persisted['fecha_salida']
    assert persisted['version'] == 1 and not persisted['salida_tardia']
    assert database.sql('''select count(*) from public."ASISTENCIA"
        where not anulado and coalesce(hora_salida::text,'')='';''') == '1'
    events = persisted['auditoria']
    assert sum(e['accion'] == 'incompleta_automatica' for e in events) == 1
    assert next(e for e in events if e['accion'] == 'incompleta_automatica')['actor_nombre'] == 'Sistema'
    assert database.sql('select public.marcar_asistencias_incompletas();') == '0'
    # Reintentar la misma entrada no duplica; otra visita sigue bloqueada por falta de salida.
    assert save(database, payload)['id_asistencia'] == row['id_asistencia']
    with pytest.raises(RuntimeError, match='entrada sin salida'):
        save(database, dict(id_cliente=95, id_membresia=100, servicio='gimnasio'),
             request_id='00000000-0000-0000-0000-000000000095')
    closed = save(database, persisted, 1, 'salida')
    assert closed['hora_salida'] and closed['fecha_salida']
    assert closed['salida_tardia'] and closed['estado_asistencia'] == 'incompleta'
    assert closed['version'] == 2
    assert sum(e['accion'] == 'incompleta_automatica' for e in closed['auditoria']) == 1
    assert save(database, persisted, 1, 'salida')['hora_salida'] == closed['hora_salida']
    assert database.sql('''select count(*) from public."ASISTENCIA"
        where not anulado and coalesce(hora_salida::text,'')='';''') == '0'
