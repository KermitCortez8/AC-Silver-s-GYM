"""Guardado automático real sin navegador; solo PostgreSQL desechable explícito."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import time

import pytest

from tests.transversales.postgres.test_atomic_transactions_postgres import Postgres
from tests.asistencias.postgres.test_attendance_deadline_postgres import entry, save

pytestmark = pytest.mark.skipif(not os.getenv('GYM_TEST_POSTGRES_CONTAINER'),
    reason='Requiere un PostgreSQL desechable explícito')
MIGRATIONS = Path(__file__).resolve().parents[3] / 'migrations'


@pytest.fixture(scope='module')
def database():
    db = Postgres()
    db.sql((Path(__file__).resolve().parents[2] / 'soporte/fixtures/priority_schema.sql').read_text())
    for name in ['005_harden_attendance.sql', '013_general_attendance.sql',
                 '018_attendance_schedule_exit_deadline.sql', '021_persist_attendance_status.sql',
                 '023_general_attendance_three_hour_close.sql']:
        db.sql((MIGRATIONS / name).read_text())
    return db


@pytest.fixture(autouse=True)
def clean(database):
    database.sql('''truncate public."ASISTENCIA", public."CLIENTES", public."MEMBRESIA",
        public."HORARIOS_SERVICIO", public."MATRICULAS_HORARIO" restart identity;
        insert into public."CLIENTES" (id_cliente,"Estado") values (1,true);
        insert into public."MEMBRESIA" (id_membresia,id_cliente,"Estado",estado_pago,"Fecha_Inicio","Fecha_Fin")
        values (1,1,'ACTIVA','PAGADO',(current_date-2)::text,(current_date+2)::text);
        insert into public."HORARIOS_SERVICIO" (id_horario_servicio,servicio,dia,hora_inicio,hora_fin,activo)
        values (1,'fitness',(array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])
          [extract(isodow from clock_timestamp() at time zone 'America/Lima')::integer],'00:00','23:59:59',true);
        insert into public."MATRICULAS_HORARIO" (id_matricula,id_cliente,id_horario_servicio,estado)
        values (1,1,1,'ACTIVA');''')
    yield
    if database.sql("select to_regclass('cron.job') is not null;") == 't':
        database.sql("select cron.unschedule(jobid) from cron.job where jobname='silver-gym-incomplete-attendance';")


def test_limite_exacto_y_hora_inclusiva(database):
    for end, expected in [('12:00:00', 'dentro'), ('12:00:00.000001', 'incompleta')]:
        assert database.sql(f"""select public.estado_visita_asistencia(false,
            '2026-11-08T12:00:00-05:00', null, false, '2026-11-08T{end}-05:00');""") == expected
    assert database.sql("""select public.estado_visita_asistencia(false,
        '2026-11-08T12:00:00-05:00', '2026-11-08 12:00:00', false,
        '2026-11-09T12:00:00-05:00');""") == 'completada'


def test_cron_persiste_sin_pantalla_y_sin_inventar_salida(database):
    if database.sql("select exists(select 1 from pg_available_extensions where name='pg_cron');") != 't':
        pytest.skip('Esta imagen PostgreSQL no incluye pg_cron; el resto del contrato sí se comprueba')
    row = entry(database)
    assert row['estado_asistencia'] == 'dentro'
    database.sql('''update public."ASISTENCIA" set limite_salida=clock_timestamp()+interval '2 seconds';''')
    # La misma programación se puede aplicar otra vez sin crear dos trabajos.
    for _ in range(2):
        database.sql((MIGRATIONS / '022_attendance_status_cron.sql').read_text())
    assert database.sql("select count(*) from cron.job where jobname='silver-gym-incomplete-attendance' and active;") == '1'
    expires = time.monotonic() + 30
    while time.monotonic() < expires:
        persisted = database.rows('ASISTENCIA')[0]
        if persisted['estado_asistencia'] == 'incompleta':
            break
        time.sleep(0.5)
    assert persisted['estado_asistencia'] == 'incompleta'
    assert not persisted['hora_salida'] and not persisted['fecha_salida']
    assert persisted['version'] == 1
    automatic = [e for e in persisted['auditoria'] if e['accion'] == 'incompleta_automatica']
    assert len(automatic) == 1 and automatic[0]['actor_nombre'] == 'Sistema'
    assert database.sql('select public.marcar_asistencias_incompletas();') == '0'
    assert database.rows('ASISTENCIA')[0]['auditoria'] == persisted['auditoria']


def test_salida_real_y_proceso_concurrente_no_se_sobrescriben(database):
    row = entry(database)
    database.sql('''update public."ASISTENCIA" set limite_salida=clock_timestamp()-interval '2 seconds';''')
    with ThreadPoolExecutor(max_workers=2) as executor:
        sweep = executor.submit(database.sql, 'select public.marcar_asistencias_incompletas();')
        closing = executor.submit(save, database, row, 1, 'salida')
        sweep.result()
        result = closing.result()
    assert result['hora_salida'] and result['estado_asistencia'] == 'incompleta'
    assert result['salida_tardia'] is True and result['version'] == 2
    assert sum(e['accion'] == 'incompleta_automatica' for e in result['auditoria']) == 1
    assert save(database, result, 1, 'salida')['hora_salida'] == result['hora_salida']


def test_correccion_documentada_puede_recuperar_la_salida_real(database):
    row = entry(database)
    database.sql('''update public."ASISTENCIA" set limite_salida=clock_timestamp()-interval '1 second';''')
    # Reconstruye una visita real del día anterior al límite de esta prueba.
    yesterday = database.sql("select ((clock_timestamp() at time zone 'America/Lima')::date-1)::text;")
    row.update(Fecha=yesterday, Hora='09:00:00', hora_entrada='09:00:00',
               hora_salida='10:00:00', fecha_salida=yesterday)
    saved = save(database, row, 1, 'correccion')
    assert saved['estado_asistencia'] == 'completada'
    assert saved['salida_tardia'] is False
    assert any(e['accion'] == 'incompleta_automatica' for e in saved['auditoria'])


def test_migracion_repetible_no_duplica_auditoria_y_estado_no_se_falsifica(database):
    row = entry(database)
    database.sql('''update public."ASISTENCIA" set limite_salida=clock_timestamp()-interval '1 second';''')
    before = database.rows('ASISTENCIA')[0]
    database.sql((MIGRATIONS / '021_persist_attendance_status.sql').read_text())
    database.sql((MIGRATIONS / '023_general_attendance_three_hour_close.sql').read_text())
    assert database.rows('ASISTENCIA')[0]['auditoria'] == before['auditoria']
    row.update(estado_asistencia='completada', hora_salida=None)
    saved = save(database, row, 1, 'correccion')
    assert saved['estado_asistencia'] == 'incompleta'


@pytest.mark.parametrize('role', ['anon', 'authenticated'])
def test_proceso_automatico_no_es_una_operacion_publica(database, role):
    with pytest.raises(RuntimeError, match='permission denied'):
        database.sql(f'set role {role}; select public.marcar_asistencias_incompletas();')


def general_entry(db, request='00000000-0000-0000-0000-000000000001'):
    return save(db, {'id_cliente': 1, 'id_membresia': 1, 'servicio': 'gimnasio',
                    'limite_salida': '2000-01-01T00:00:00-05:00', 'cierre_automatico': True},
                request_id=request)


def test_general_guarda_plazo_servidor_e_ignora_cierre_enviado(database):
    row = general_entry(database)
    assert not row['cierre_automatico'] and row['estado_asistencia'] == 'dentro'
    assert database.sql('''select limite_salida = (("Fecha"::date + hora_entrada::time
        + interval '3 hours') at time zone 'America/Lima') from public."ASISTENCIA";''') == 't'


def test_cron_cierra_general_sin_actividad_y_libera_aforo(database):
    if database.sql("select exists(select 1 from pg_available_extensions where name='pg_cron');") != 't':
        pytest.skip('La imagen no incluye pg_cron; el cierre se comprueba también invocando la función')
    general_entry(database)
    database.sql('''update public."ASISTENCIA" set
        "Fecha"=((clock_timestamp() at time zone 'America/Lima')-interval '3 hours'+interval '4 seconds')::date,
        hora_entrada=((clock_timestamp() at time zone 'America/Lima')-interval '3 hours'+interval '4 seconds')::time;''')
    database.sql((MIGRATIONS / '022_attendance_status_cron.sql').read_text())
    end = time.monotonic() + 30
    while time.monotonic() < end:
        closed = database.rows('ASISTENCIA')[0]
        if closed['cierre_automatico']:
            break
        time.sleep(.5)
    assert closed['cierre_automatico'] and closed['estado_asistencia'] == 'incompleta'
    assert closed['hora_salida'] and closed['fecha_salida'] and closed['version'] == 2
    assert database.sql('''select count(*) from public."ASISTENCIA"
        where not anulado and coalesce(hora_salida::text,'')='';''') == '0'
    assert sum(e['accion'] == 'cierre_automatico' for e in closed['auditoria']) == 1
    assert database.sql('select public.marcar_asistencias_incompletas();') == '0'
    repeated = general_entry(database)
    assert repeated['id_asistencia'] == closed['id_asistencia'] and repeated['cierre_automatico']
    new = general_entry(database, '00000000-0000-0000-0000-000000000002')
    assert new['id_asistencia'] != closed['id_asistencia']


def test_migracion_recupera_abiertas_antiguas_y_correccion_conserva_auditoria(database):
    general_entry(database)
    yesterday = database.sql("select ((clock_timestamp() at time zone 'America/Lima')::date-1)::text;")
    database.sql(f'''update public."ASISTENCIA" set "Fecha"='{yesterday}', hora_entrada='22:30:00';''')
    database.sql((MIGRATIONS / '023_general_attendance_three_hour_close.sql').read_text())
    closed = database.rows('ASISTENCIA')[0]
    assert closed['cierre_automatico'] and closed['hora_salida'] == '01:30:00'
    before = closed['auditoria']
    database.sql((MIGRATIONS / '023_general_attendance_three_hour_close.sql').read_text())
    assert database.rows('ASISTENCIA')[0]['auditoria'] == before
    saved = save(database, {**closed, 'hora_salida': '23:00:00', 'fecha_salida': yesterday}, closed['version'], 'correccion')
    assert not saved['cierre_automatico'] and saved['estado_asistencia'] == 'completada'
    assert any(e['accion'] == 'cierre_automatico' for e in saved['auditoria'])


def test_cierre_general_y_salida_manual_concurrentes_conservan_primera_salida(database):
    row = general_entry(database)
    database.sql('''update public."ASISTENCIA" set "Fecha"=
        ((clock_timestamp() at time zone 'America/Lima')::date-1)::text;''')
    with ThreadPoolExecutor(max_workers=2) as executor:
        automatic = executor.submit(database.sql, 'select public.marcar_asistencias_incompletas();')
        manual = executor.submit(save, database, row, 1, 'salida')
        automatic.result()
        first = manual.result()
    persisted = database.rows('ASISTENCIA')[0]
    assert persisted['estado_asistencia'] == 'incompleta' and persisted['version'] == 2
    assert persisted['hora_salida'] == first['hora_salida']
    assert sum(e['accion'] in ('salida', 'cierre_automatico') for e in persisted['auditoria']) == 1
    assert save(database, row, 1, 'salida')['hora_salida'] == persisted['hora_salida']


def test_nueva_entrada_reconcilia_general_vencida_y_permite_reingreso(database):
    first = general_entry(database)
    database.sql('''update public."ASISTENCIA" set "Fecha"=
        ((clock_timestamp() at time zone 'America/Lima')::date-1)::text;''')
    second = general_entry(database, '00000000-0000-0000-0000-000000000002')
    rows = database.rows('ASISTENCIA')
    closed = next(row for row in rows if row['id_asistencia'] == first['id_asistencia'])
    assert closed['cierre_automatico'] and closed['estado_asistencia'] == 'incompleta'
    assert closed['version'] == 2
    assert sum(e['accion'] == 'cierre_automatico' for e in closed['auditoria']) == 1
    assert second['id_asistencia'] != first['id_asistencia']
    assert second['estado_asistencia'] == 'dentro' and not second['hora_salida']
    assert general_entry(database)['id_asistencia'] == first['id_asistencia']


def test_migracion_preserva_salida_real_historica_y_no_expone_rpc_auxiliar(database):
    row = general_entry(database)
    saved = save(database, row, 1, 'salida')
    assert saved['estado_asistencia'] == 'completada' and not saved['cierre_automatico']
    # Simula una visita ya cerrada antes de que existiera el plazo general.
    database.sql('update public."ASISTENCIA" set limite_salida=null;')
    before = database.rows('ASISTENCIA')[0]
    for _ in range(2):
        database.sql((MIGRATIONS / '023_general_attendance_three_hour_close.sql').read_text())
    assert database.rows('ASISTENCIA')[0] == before
    assert database.sql('select public.marcar_asistencias_incompletas();') == '0'
    for role in ['anon', 'authenticated', 'service_role']:
        with pytest.raises(RuntimeError, match='permission denied'):
            database.sql(f'''set role {role}; select
                public.guardar_asistencia_sin_cierre_general('{{}}',null,'{{}}');''')
