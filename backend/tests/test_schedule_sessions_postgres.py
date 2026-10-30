"""Reservas por sesión y admisión real, solo en PostgreSQL desechable."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path

import pytest

from tests.test_atomic_transactions_postgres import Postgres
from tests.test_attendance_deadline_postgres import save

pytestmark = pytest.mark.skipif(not os.getenv("GYM_TEST_POSTGRES_CONTAINER"),
    reason="Requiere un PostgreSQL desechable explícito")
BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def database():
    db = Postgres()
    db.sql((BACKEND / "tests/fixtures/priority_schema.sql").read_text())
    db.sql('alter table public."MATRICULAS_HORARIO" drop column fecha_clase;')
    for name in ["002_harden_schedule_enrollment.sql", "005_harden_attendance.sql",
                 "006_schedule_email_notifications.sql", "013_general_attendance.sql",
                 "018_attendance_schedule_exit_deadline.sql", "019_schedule_sessions.sql"]:
        db.sql((BACKEND / "migrations" / name).read_text())
    db.sql((BACKEND / "migrations/019_schedule_sessions.sql").read_text())
    return db


@pytest.fixture(autouse=True)
def clean(database):
    database.sql('''truncate public."ASISTENCIA", public."CLIENTES", public."MEMBRESIA",
      public."HORARIOS_SERVICIO", public."MATRICULAS_HORARIO", public.schedule_email_notifications restart identity cascade;
      insert into public."CLIENTES" (id_cliente,"Estado") values (1,true),(2,true);
      insert into public."MEMBRESIA" (id_membresia,id_cliente,"Estado",estado_pago,"Fecha_Inicio","Fecha_Fin")
      select i,i,'ACTIVA','PAGADO',(current_date-2)::text,(current_date+120)::text from generate_series(1,2) i;
      insert into public."HORARIOS_SERVICIO" (id_horario_servicio,servicio,dia,hora_inicio,hora_fin,cupos,activo)
      values (1,'fitness',(array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])
        [extract(isodow from clock_timestamp() at time zone 'America/Lima')::integer],'00:00','23:59:59',1,true);''')


def enroll(db, client=1, offset=0):
    return json.loads(db.sql(f"""set role service_role;
      select public.matricular_cliente_sesion({client},1,(clock_timestamp() at time zone 'America/Lima')::date+{offset});"""))


def test_rpc_aisla_duplicados_cupos_y_cancelaciones_por_fecha(database):
    first = enroll(database)
    for client, message in [(1, "ya esta matriculado"), (2, "sin cupos")]:
        with pytest.raises(RuntimeError, match=message):
            enroll(database, client)
    second = enroll(database, offset=7)
    assert first["fecha_clase"] != second["fecha_clase"]
    database.sql(f'''update public."MATRICULAS_HORARIO" set estado='CANCELADA' where id_matricula={first['id_matricula']};''')
    assert enroll(database, client=2)["fecha_clase"] == first["fecha_clase"]
    rows = database.rows("MATRICULAS_HORARIO")
    assert next(r for r in rows if r["id_matricula"] == second["id_matricula"])["estado"] == "ACTIVA"


def test_rpc_concurrencia_no_sobrepasa_cupo_de_la_sesion(database):
    def attempt(client):
        try:
            return enroll(database, client)["id_matricula"]
        except RuntimeError as error:
            assert "sin cupos" in str(error)
            return None
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, [1, 2]))
    assert sum(result is not None for result in results) == 1
    assert len(database.rows("MATRICULAS_HORARIO")) == 1


def test_rpc_asistencia_rechaza_matricula_de_otra_semana_sin_guardar(database):
    future = enroll(database, offset=7)
    with pytest.raises(RuntimeError, match="fecha de esta clase"):
        save(database, {"id_cliente": 1, "id_membresia": 1,
                        "id_matricula": future["id_matricula"], "servicio": "fitness"})
    assert database.rows("ASISTENCIA") == []
    today = enroll(database)
    saved = save(database, {"id_cliente": 1, "id_membresia": 1,
                           "id_matricula": today["id_matricula"], "servicio": "fitness"})
    assert saved["Fecha"] == today["fecha_clase"]


@pytest.mark.parametrize("offset,message", [(1, "día del horario"), (-7, "fecha de clase vigente")])
def test_rpc_rechaza_fecha_incompatible_o_pasada(database, offset, message):
    with pytest.raises(RuntimeError, match=message):
        enroll(database, offset=offset)
    assert database.rows("MATRICULAS_HORARIO") == []


def test_migracion_repetible_backfill_no_renueva_clientes_y_conserva_permisos(database):
    database.sql('''alter table public."MATRICULAS_HORARIO" disable trigger validar_cupo_matricula_horario_trigger;
      insert into public."MATRICULAS_HORARIO" (id_cliente,id_horario_servicio,fecha_matricula,estado)
      values (1,1,'2026-01-01','ACTIVA');
      alter table public."MATRICULAS_HORARIO" enable trigger validar_cupo_matricula_horario_trigger;''')
    migration = (BACKEND / "migrations/019_schedule_sessions.sql").read_text()
    database.sql(migration)
    first = database.rows("MATRICULAS_HORARIO")[0]["fecha_clase"]
    assert first.startswith("2026-01-")
    database.sql(migration)
    assert database.rows("MATRICULAS_HORARIO")[0]["fecha_clase"] == first
    for role in ["anon", "authenticated"]:
        assert database.sql(f"select has_function_privilege('{role}', 'public.matricular_cliente_sesion(bigint,bigint,date)', 'EXECUTE');") == "f"
    # Una matrícula histórica no genera recordatorios para otra semana.
    assert database.sql("select public.enqueue_due_schedule_reminders(clock_timestamp());") == "0"


def test_recordatorios_solo_se_generan_en_la_fecha_reservada(database):
    database.sql('''update public."HORARIOS_SERVICIO" set hora_inicio='11:00', hora_fin='12:00',
      dia=(array['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[
        extract(isodow from (clock_timestamp() at time zone 'America/Lima')::date+1)::integer];''')
    reserved = enroll(database, offset=1)
    database.sql("update public.\"MATRICULAS_HORARIO\" set email_registered_at=clock_timestamp()-interval '7 days';")
    moment = f"('{reserved['fecha_clase']}'::date+time '10:30') at time zone 'America/Lima'"
    assert database.sql(f"select public.enqueue_due_schedule_reminders({moment});") == "1"
    assert database.sql(f"select public.enqueue_due_schedule_reminders(({moment})+interval '7 days');") == "0"
    jobs = json.loads(database.sql("select jsonb_agg(to_jsonb(j)) from public.schedule_email_notifications j;"))
    assert len(jobs) == 1
    with pytest.raises(RuntimeError, match="fecha de clase.*no se puede cambiar"):
        database.sql('update public."MATRICULAS_HORARIO" set fecha_clase=fecha_clase+7;')
