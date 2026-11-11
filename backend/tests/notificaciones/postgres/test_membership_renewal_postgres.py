"""Migración de avisos: requiere PostgreSQL desechable explícito."""
import os
from pathlib import Path

import pytest

from tests.transversales.postgres.test_atomic_transactions_postgres import Postgres

pytestmark = pytest.mark.skipif(not os.getenv('GYM_TEST_POSTGRES_CONTAINER'),
    reason='Requiere un PostgreSQL desechable explícito')
BACKEND = Path(__file__).resolve().parents[3]


@pytest.fixture(scope='module')
def database():
    db = Postgres()
    db.sql((BACKEND / 'tests/soporte/fixtures/priority_schema.sql').read_text())
    db.sql((BACKEND / 'migrations/004_membership_email_notifications.sql').read_text())
    db.sql((BACKEND / 'migrations/024_membership_renewal_notifications.sql').read_text())
    db.sql((BACKEND / 'migrations/024_membership_renewal_notifications.sql').read_text())
    db.sql('''insert into public."CLIENTES" (id_cliente,"Estado") values (1,true);
        insert into public."MEMBRESIA" (id_membresia,id_cliente,"Estado",estado_pago)
        values (1,1,'ACTIVA','PAGADO');''')
    return db


def test_aviso_deduplicado_y_reclamado_una_sola_vez(database):
    for event in ['expiring', 'expired']:
        enqueue = f"""set role service_role; select count(*) from public.enqueue_membership_email(
            'membership/1/{event}',1,'{event}','{{"subject":"Prueba"}}'::jsonb);"""
        assert database.sql(enqueue) == '1'
        assert database.sql(enqueue) == '1'
    assert database.sql('select count(*) from public.membership_email_notifications;') == '2'
    assert database.sql("set role service_role; select count(*) from public.claim_membership_email('uno','membership/1/expiring');") == '1'
    assert database.sql("set role service_role; select count(*) from public.claim_membership_email('dos','membership/1/expiring');") == '0'


def test_la_migracion_conserva_privacidad_y_validacion_de_eventos(database):
    for role in ['anon', 'authenticated']:
        with pytest.raises(RuntimeError, match='permission denied'):
            database.sql(f'set role {role}; select * from public.membership_email_notifications;')
        with pytest.raises(RuntimeError, match='permission denied'):
            database.sql(f"set role {role}; select * from public.enqueue_membership_email('otro',1,'expired','{{}}');")
    with pytest.raises(RuntimeError, match='check constraint'):
        database.sql("select * from public.enqueue_membership_email('invalido',1,'otro','{}');")
