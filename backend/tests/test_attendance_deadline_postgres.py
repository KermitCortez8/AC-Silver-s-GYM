"""RPC de asistencia real; exige el contenedor desechable explícito del DoD."""
import json
import os
from pathlib import Path

import pytest

from tests.test_atomic_transactions_postgres import Postgres

pytestmark = pytest.mark.skipif(not os.getenv("GYM_TEST_POSTGRES_CONTAINER"),
    reason="Requiere un PostgreSQL desechable explícito")
MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


@pytest.fixture(scope="module")
def database():
    db = Postgres()
    db.sql((Path(__file__).parent / "fixtures/priority_schema.sql").read_text())
    for name in ["005_harden_attendance.sql", "013_general_attendance.sql", "018_attendance_schedule_exit_deadline.sql"]:
        db.sql((MIGRATIONS / name).read_text())
    db.sql((MIGRATIONS / "018_attendance_schedule_exit_deadline.sql").read_text())
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


def save(db, row, version=None, action="entrada", **extra):
    row_sql = json.dumps(row).replace("'", "''")
    event = json.dumps({"accion": action, "actor_id": "1", "motivo": "Prueba aislada", **extra}).replace("'", "''")
    version_sql = "null" if version is None else str(version)
    return json.loads(db.sql(f"set role service_role; select public.guardar_asistencia('{row_sql}'::jsonb,{version_sql},'{event}'::jsonb);"))


def entry(db):
    return save(db, {"id_cliente": 1, "id_membresia": 1, "id_matricula": 1, "servicio": "fitness"})


def test_rpc_guarda_limite_no_acepta_hora_del_cliente_y_conserva_reintentos(database):
    row = save(database, {"id_cliente": 1, "id_membresia": 1, "id_matricula": 1, "servicio": "fitness",
        "hora_entrada": "00:00:00", "limite_salida": "2000-01-01T00:00:00-05:00", "salida_tardia": True})
    assert row["limite_salida"] is not None and row["salida_tardia"] is False
    assert not row["limite_salida"].startswith("2000-")
    database.sql('update public."HORARIOS_SERVICIO" set hora_fin=\'23:00\';')
    repeated = entry(database)
    assert repeated["limite_salida"] == row["limite_salida"]
    assert repeated["id_asistencia"] == row["id_asistencia"]
    assert len(database.rows("ASISTENCIA")) == 1


def test_rpc_rechaza_clase_terminada_sin_guardar(database):
    database.sql('update public."HORARIOS_SERVICIO" set hora_fin=\'00:00\';')
    with pytest.raises(RuntimeError, match="La hora de esta clase ya pasó"):
        entry(database)
    assert database.rows("ASISTENCIA") == []


def test_rpc_salida_fuera_de_plazo_persiste_tardia_y_auditoria(database):
    row = entry(database)
    database.sql('''update public."ASISTENCIA" set limite_salida=clock_timestamp()-interval '2 seconds';''')
    row["hora_salida"] = "00:00:00"
    saved = save(database, row, 1, "salida")
    assert saved["salida_tardia"] is True
    assert saved["hora_salida"] != "00:00:00"
    assert len(saved["auditoria"]) == 2
    assert saved["auditoria"][-1]["despues"]["salida_tardia"] is True
    assert save(database, row, 1, "salida")["hora_salida"] == saved["hora_salida"]


@pytest.mark.parametrize("second,late", [("00", False), ("01", True)])
def test_rpc_limite_inclusivo_y_correccion_auditada(database, second, late):
    row = entry(database)
    yesterday = database.sql("select (clock_timestamp() at time zone 'America/Lima')::date-1;")
    database.sql(f'''update public."ASISTENCIA" set "Fecha"='{yesterday}',hora_entrada='10:00',
        limite_salida='{yesterday} 13:00:00-05';''')
    row.update(Fecha=yesterday, hora_entrada="10:00:00", hora_salida=f"13:00:{second}", fecha_salida=yesterday)
    saved = save(database, row, 1, "correccion")
    assert saved["salida_tardia"] is late
    assert saved["limite_salida"].startswith(yesterday)


def test_migracion_repetible_completa_abiertas_y_conserva_cerradas_y_permisos(database):
    row = entry(database)
    database.sql('update public."ASISTENCIA" set limite_salida=null;')
    migration = (MIGRATIONS / "018_attendance_schedule_exit_deadline.sql").read_text()
    database.sql(migration)
    first = database.rows("ASISTENCIA")[0]["limite_salida"]
    database.sql('update public."HORARIOS_SERVICIO" set hora_fin=\'23:00\';')
    database.sql(migration)
    assert database.rows("ASISTENCIA")[0]["limite_salida"] == first
    assert row["id_asistencia"] == database.rows("ASISTENCIA")[0]["id_asistencia"]
    for role in ["anon", "authenticated"]:
        assert database.sql(f"select has_function_privilege('{role}', 'public.guardar_asistencia(jsonb,integer,jsonb)', 'EXECUTE');") == "f"
