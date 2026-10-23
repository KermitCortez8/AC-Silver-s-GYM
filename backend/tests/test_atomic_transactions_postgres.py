"""Integración SQL real. Opt-in con GYM_TEST_POSTGRES_CONTAINER, sin datos externos."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import threading

import pytest

from application.services.gym_service import GymService
from infrastructure.repositories.atomic_changes import SnapshotConflict, commit_snapshot
from infrastructure.repositories.gym_repository import SupabaseGymRepository
from tests.test_priority_fixes import Passwords

CONTAINER = os.getenv('GYM_TEST_POSTGRES_CONTAINER')
pytestmark = pytest.mark.skipif(not CONTAINER, reason='Requiere un PostgreSQL desechable explícito')
BACKEND = Path(__file__).resolve().parents[1]


class Postgres:
    def sql(self, statement):
        result = subprocess.run(['docker', 'exec', '-i', CONTAINER, 'psql', '-U', 'postgres', '-d', 'gym_test',
                                 '-v', 'ON_ERROR_STOP=1', '-v', 'VERBOSITY=verbose', '-At'],
                                input=statement, text=True, capture_output=True, timeout=25)
        if result.returncode:
            raise RuntimeError(result.stderr)
        lines = result.stdout.strip().splitlines()
        return lines[-1] if lines else ''

    def rows(self, table):
        return json.loads(self.sql(f'''select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public."{table}" t;'''))

    def select_all(self, table, order=None):
        return self.rows(table)

    select = select_all

    def validate_columns(self, table, columns):
        names = ','.join('"'+column+'"' for column in columns)
        self.sql(f'select {names} from public."{table}" limit 0;')

    def rpc(self, name, body):
        if name == 'gym_identity_floors':
            values = ','.join("'"+table+"'" for table in body['p_tables'])
            return json.loads(self.sql(f'select public.gym_identity_floors(array[{values}]::text[]);'))
        assert name == 'commit_gym_transaction'
        expected = json.dumps(body['p_expected']).replace("'", "''")
        operations = json.dumps(body['p_operations']).replace("'", "''")
        try:
            return json.loads(self.sql(f"set role service_role; select public.commit_gym_transaction('{expected}'::jsonb, '{operations}'::jsonb);"))
        except RuntimeError as error:
            if '40001' in str(error):
                raise RuntimeError('PostgreSQL: {"code":"40001"}') from error
            if '40P01' in str(error):
                raise RuntimeError('PostgreSQL: {"code":"40P01"}') from error
            raise


@pytest.fixture(scope='module')
def database():
    database = Postgres()
    database.sql((BACKEND / 'tests/fixtures/priority_schema.sql').read_text())
    for filename in ['014_preserve_business_fields.sql', '015_atomic_gym_transactions.sql']:
        migration = (BACKEND / 'migrations' / filename).read_text()
        database.sql(migration)
        database.sql(migration)  # El despliegue repetido no debe borrar ni duplicar datos.
    return database


@pytest.fixture(autouse=True)
def clear(database):
    tables = list(SupabaseGymRepository.CORE_TABLES[key][0] for key in SupabaseGymRepository.CORE_TABLES)
    tables += ['VENTAS', 'DETALLE_VENTA', 'CONFIGURACION_GIMNASIO', 'gym_identity_counters']
    database.sql('truncate '+','.join('public."'+table+'"' for table in tables)+' restart identity cascade;')


def service(database, monkeypatch):
    monkeypatch.setattr('infrastructure.repositories.gym_repository.SupabaseRestClient', lambda *_args: database)
    return GymService(SupabaseGymRepository('local', 'unused'), Passwords())


def test_transaction_rolls_back_deletes_details_and_updates_on_failure(database):
    database.sql('''insert into public."INVENTARIO" (id_item,"Cantidad_Stock_E") values (1,5),(2,8);
                   insert into public."VENTAS" (id_venta) values (1);
                   insert into public."DETALLE_VENTA" (id_venta,id_producto,"Cantidad") values (1,1,2);''')
    expected = {table: database.rows(table) for table in ['INVENTARIO', 'VENTAS', 'DETALLE_VENTA']}
    operations = [
        {'table': 'INVENTARIO', 'pk': 'id_item', 'action': 'delete', 'id': 1},
        {'table': 'DETALLE_VENTA', 'pk': 'id_detalle', 'action': 'delete_details', 'id': 1},
        {'table': 'DETALLE_VENTA', 'pk': 'id_detalle', 'action': 'insert', 'body': {'id_venta': 1, 'id_producto': 1, 'Cantidad': 7}},
        {'table': 'INVENTARIO', 'pk': 'id_item', 'action': 'update', 'id': 2, 'body': {'id_item': 2, 'Cantidad_Stock_E': -1}},
    ]
    with pytest.raises(RuntimeError, match='check constraint'):
        commit_snapshot(database, expected, operations)
    assert {table: database.rows(table) for table in expected} == expected


def test_stale_snapshot_is_rejected_without_partial_writes(database):
    expected = {'INVENTARIO': []}
    database.sql('insert into public."INVENTARIO" (id_item,"Cantidad_Stock_E") values (1,5);')
    with pytest.raises(SnapshotConflict):
        commit_snapshot(database, expected, [dict(table='INVENTARIO', pk='id_item', action='insert', id=2,
                                                  body={'id_item': 2, 'Cantidad_Stock_E': 4})])
    assert len(database.rows('INVENTARIO')) == 1


def test_private_rpc_cannot_be_called_as_anon(database):
    with pytest.raises(RuntimeError, match='permission denied for function'):
        database.sql('set role anon; select public.commit_gym_transaction(\'{"USUARIO":[]}\', \'[]\');')


def test_user_ids_survive_role_change_and_are_not_reused_after_delete(database, monkeypatch):
    gym = service(database, monkeypatch)
    first = gym.upsert_usuario(dict(nombre='Admin', correo='admin@example.com', rol='admin', password='secret123'))
    second = gym.upsert_usuario(dict(nombre='Trainer', correo='trainer@example.com', rol='trainer', password='secret123'))
    assert (first['id_usuario'], second['id_usuario']) == ('SGADM001', 'SGTRA002')
    changed = gym.upsert_usuario({**first, 'rol': 'staff'})
    gym.repository._last_refresh_at = 0
    gym.ensure_fresh(('usuario',))
    assert gym.get_usuario(first['id_usuario'])['rol'] == 'staff'
    assert changed['id_usuario'] == first['id_usuario']
    gym.delete_usuario(second['id_usuario'])
    third = gym.upsert_usuario(dict(nombre='Staff', correo='staff@example.com', rol='staff', password='secret123'))
    assert third['id_usuario'] == 'SGSTA003'
    assert {row['id_usuario'] for row in database.rows('USUARIO')} == {1, 3}


def test_preserved_fields_survive_actual_database_reload(database, monkeypatch):
    gym = service(database, monkeypatch)
    item = gym.upsert_inventario(dict(nombre_item='Toalla', tipo='Tienda', cantidad_stock=10,
                                      unidad_venta='pack', precio_venta=12.5, stock_minimo=7, ubicacion='Sala A', observaciones='nota'))
    product = gym.productos_tienda()[0]
    gym.upsert_producto_tienda({**product, 'descripcion': 'Paquete de toallas', 'unidad_venta': 'pack', 'precio_venta': 12.5})
    gym.repository._last_refresh_at = 0
    gym.ensure_fresh()
    loaded = gym.get_item_inventario(item['id_item'])
    assert (loaded['unidad_venta'], loaded['precio_venta'], loaded['stock_minimo'], loaded['ubicacion'], loaded['observaciones']) == ('pack', 12.5, 7, 'Sala A', 'nota')
    assert gym.productos_tienda()[0]['descripcion'] == 'Paquete de toallas'
    assert gym.productos_tienda()[0]['unidad_venta'] == 'pack'


def test_two_instances_cannot_sell_the_same_stock(database, monkeypatch):
    database.sql('''insert into public."TIENDA_PRODUCTOS" (id_producto,"nombre_Producto","precio_Venta",cantidad_stock,stock_minimo)
                   values (1,'Agua',10,5,0);''')
    first = service(database, monkeypatch)
    second = service(database, monkeypatch)
    first.ensure_fresh()
    second.ensure_fresh()
    barrier = threading.Barrier(2)
    class Concurrent(Postgres):
        def __init__(self):
            self.waited = False
        def rpc(self, name, body):
            if name == 'commit_gym_transaction' and not self.waited:
                self.waited = True
                barrier.wait(timeout=5)
            return super().rpc(name, body)
    first.repository.supabase, second.repository.supabase = Concurrent(), Concurrent()
    def buy(gym):
        try:
            return gym.crear_pedido_tienda({'items': [{'id_producto': 1, 'cantidad': 3}]})
        except ValueError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(buy, [first, second]))
    assert sum(isinstance(result, dict) for result in results) == 1
    assert any(isinstance(result, str) and 'Stock insuficiente' in result for result in results)
    assert database.rows('TIENDA_PRODUCTOS')[0]['cantidad_stock'] == 2
    assert len(database.rows('VENTAS')) == 1
    assert len(database.rows('DETALLE_VENTA')) == 1


def test_two_instances_allocate_distinct_user_ids(database, monkeypatch):
    first = service(database, monkeypatch)
    second = service(database, monkeypatch)
    first.ensure_fresh(('usuario',))
    second.ensure_fresh(('usuario',))
    barrier = threading.Barrier(2)
    class Concurrent(Postgres):
        def __init__(self):
            self.waited = False
        def rpc(self, name, body):
            if name == 'commit_gym_transaction' and not self.waited:
                self.waited = True
                barrier.wait(timeout=5)
            return super().rpc(name, body)
    first.repository.supabase, second.repository.supabase = Concurrent(), Concurrent()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(gym.upsert_usuario, dict(nombre=role, correo=role+'@example.com', rol=role, password='secret123'))
                   for gym, role in [(first, 'admin'), (second, 'trainer')]]
        users = [future.result() for future in futures]
    assert len({user['id_usuario'] for user in users}) == 2
    assert {row['id_usuario'] for row in database.rows('USUARIO')} == {1, 2}


def test_promotions_and_membership_association_survive_database_reload(database, monkeypatch):
    gym = service(database, monkeypatch)
    gym.upsert_plan_membresia({'id_pm': 1, 'nombre_plan': 'MENSUAL', 'duracion': '45 dias', 'precio': 79})
    promotion = gym.upsert_promocion({'nombre': 'Flash', 'tipo_descuento': 'porcentaje', 'valor_descuento': 10,
        'planes_aplicables': [1], 'activo': True, 'limite_cupos': 2, 'usos_actuales': 0,
        'icono_etiqueta': 'x', 'palabra_clave': 'FLASH'})
    saved = gym.registrar_cliente_publico({'nombre': 'Ana', 'correo': 'ana@example.com', 'dni': '12345678',
                                          'password': 'secret123', 'plan': 'MENSUAL'})
    assert saved['membresia']['monto_pago'] == 71.10
    gym.repository._last_refresh_at = 0
    gym.ensure_fresh()
    loaded = gym.promociones()[0]
    assert (loaded['limite_cupos'], loaded['usos_actuales'], loaded['icono_etiqueta'], loaded['palabra_clave']) == (2, 1, 'x', 'FLASH')
    assert gym.latest_membership(saved['cliente']['id_cliente'])['id_promocion'] == promotion['id_promocion']


def test_migration_backfills_the_same_codes_for_nullable_or_padded_roles(database):
    database.sql('''insert into public."USUARIO" (id_usuario,"Rol",codigo_usuario) values
                   (1,null,null),(2,' ADMIN ',null),(3,'staff','');''')
    database.sql((BACKEND / 'migrations/014_preserve_business_fields.sql').read_text())
    rows = {row['id_usuario']: row['codigo_usuario'] for row in database.rows('USUARIO')}
    assert rows == {1: 'SGSTA001', 2: 'SGADM002', 3: 'SGSTA003'}
    database.sql('update public."USUARIO" set "Rol"=\'trainer\' where id_usuario=2;')
    database.sql((BACKEND / 'migrations/014_preserve_business_fields.sql').read_text())
    assert next(row for row in database.rows('USUARIO') if row['id_usuario'] == 2)['codigo_usuario'] == 'SGADM002'
