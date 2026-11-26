"""Integración SQL real. Opt-in con GYM_TEST_POSTGRES_CONTAINER, sin datos externos."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import threading

import pytest

from application.services.gym_service import GymService
from domain.services.schedule_sessions import SALAS_HORARIO
from infrastructure.repositories.atomic_changes import SnapshotConflict, commit_snapshot
from infrastructure.repositories.gym_repository import SupabaseGymRepository
from tests.transversales.integracion.test_priority_fixes import Passwords

CONTAINER = os.getenv('GYM_TEST_POSTGRES_CONTAINER')
pytestmark = pytest.mark.skipif(not CONTAINER, reason='Requiere un PostgreSQL desechable explícito')
BACKEND = Path(__file__).resolve().parents[3]


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
    database.sql((BACKEND / 'tests/soporte/fixtures/priority_schema.sql').read_text())
    for filename in ['014_preserve_business_fields.sql', '015_atomic_gym_transactions.sql',
                     '016_transaction_sequence_permissions.sql', '018_archivar_inventario_tienda.sql',
                     '019_papelera_tienda.sql', '020_public_preregistrations.sql',
                     '026_inventario_unidades.sql', '027_mov_inv_unidad_hora.sql',
                     '032_bajas_y_pedidos_confirmados.sql']:
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


def test_migracion_030_permita_asignar_sala_sin_alterar_el_horario_existente(database, monkeypatch):
    gym = service(database, monkeypatch)
    rutina = gym.upsert_rutina({"servicio": "fitness", "nombre_rutina": "Circuito"})
    rutina_id = rutina["id_rutina"]
    database.sql(f'''insert into public."HORARIOS_SERVICIO"
      (id_horario_servicio, servicio, id_rutina, dia, codigo_dia, hora_inicio, hora_fin, cupos, activo)
      values (1,'fitness',{rutina_id},'lunes','LUN','10:00','11:00',8,true);''')
    migracion = (BACKEND / "migrations/030_sala_horario_servicio.sql").read_text(encoding="utf-8")
    try:
        database.sql(migracion)
        gym.repository.cache.invalidate()
        [previo] = gym.horarios_servicio()
        assert previo["sala"] is None
        assert gym.upsert_horario_servicio({**previo, "sala": SALAS_HORARIO[0]})["sala"] == SALAS_HORARIO[0]
        database.sql(migracion)
        gym.repository.cache.invalidate()
        assert gym.horarios_servicio() == [{**previo, "sala": SALAS_HORARIO[0]}]
    finally:
        database.sql('alter table public."HORARIOS_SERVICIO" drop column if exists sala;')


@pytest.mark.parametrize("tabla_existente", [False, True])
def test_migracion_028_permite_guardar_parametros_con_o_sin_tabla_previa(database, monkeypatch, tabla_existente):
    tabla = 'public."CONFIGURACION_GIMNASIO"'
    migracion = (BACKEND / 'migrations/028_parametros_horarios.sql').read_text(encoding='utf-8')
    if tabla_existente:
        aforo = {"capacidad_total": 48, "capacidad_por_hora": 12}
        database.sql(f"insert into {tabla} (capacidad_total, capacidad_por_hora) values (48, 12)")
    else:
        aforo = {"capacidad_total": 30, "capacidad_por_hora": 10}
        database.sql(f"alter table {tabla} rename to configuracion_gimnasio_fixture")

    try:
        database.sql(migracion)
        gym = service(database, monkeypatch)
        iniciales = {"hora_inicio": "06:00", "duracion_minutos": 60, "cupos": 10}
        guardados = {"hora_inicio": "08:30", "duracion_minutos": 120, "cupos": 16}
        leidos = gym.configuracion_gimnasio()
        assert {campo: leidos[campo] for campo in aforo} == aforo
        if tabla_existente:
            assert leidos["parametros_horarios"] == iniciales
        else:
            assert database.rows("CONFIGURACION_GIMNASIO") == []
            assert database.sql(f"select relrowsecurity from pg_class where oid = '{tabla}'::regclass") == "t"
            secuencia = database.sql(f"select pg_get_serial_sequence('{tabla}', 'id_config')")
            for rol in ("anon", "authenticated"):
                assert database.sql(f"select has_table_privilege('{rol}', '{tabla}', 'SELECT, INSERT, UPDATE')") == "f"
                assert database.sql(f"select has_sequence_privilege('{rol}', '{secuencia}', 'USAGE, SELECT, UPDATE')") == "f"

        final = {**aforo, "parametros_horarios": guardados}
        assert gym.actualizar_configuracion_gimnasio({"parametros_horarios": guardados}) == final
        database.sql(migracion)
        assert database.rows("CONFIGURACION_GIMNASIO") == [{"id_config": 1, **final}]
    finally:
        if tabla_existente:
            database.sql(f"alter table {tabla} drop column if exists parametros_horarios")
        else:
            database.sql(f'drop table if exists {tabla}; '
                         'alter table public.configuracion_gimnasio_fixture rename to "CONFIGURACION_GIMNASIO"')


def test_sequence_permission_migration_repairs_real_insert_failure_without_granting_other_roles(database, monkeypatch):
    database.sql('revoke update on sequence public."USUARIO_id_usuario_seq" from service_role;')
    gym = service(database, monkeypatch)
    payload = dict(nombre='Prueba visual', correo='visual@gmail.com', password='solo-pruebas', rol='admin')
    with pytest.raises(RuntimeError, match='permission denied for sequence'):
        gym.upsert_usuario(payload)
    assert database.rows('USUARIO') == []
    database.sql('create table public.unrelated_sequence_test (id bigint generated by default as identity);')
    try:
        migration = (BACKEND / 'migrations/016_transaction_sequence_permissions.sql').read_text()
        database.sql(migration)
        database.sql(migration)
        saved = gym.upsert_usuario(payload)
        assert database.rows('USUARIO')[0]['codigo_usuario'] == saved['id_usuario']
        assert database.sql('''set role service_role;
            select nextval('public."USUARIO_id_usuario_seq"') > 1;''') == 't'
        for role in ['anon', 'authenticated']:
            assert database.sql(f'''select has_sequence_privilege('{role}',
                'public."USUARIO_id_usuario_seq"', 'USAGE,SELECT,UPDATE');''') == 'f'
        assert database.sql('''select has_sequence_privilege('service_role',
            'public.unrelated_sequence_test_id_seq', 'USAGE,SELECT,UPDATE');''') == 'f'
    finally:
        database.sql('drop table public.unrelated_sequence_test;')


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
    first = gym.upsert_usuario(dict(nombre='Admin', correo='admin@gmail.com', rol='admin', password='secret123'))
    second = gym.upsert_usuario(dict(nombre='Trainer', correo='trainer@gmail.com', rol='trainer', password='secret123'))
    assert (first['id_usuario'], second['id_usuario']) == ('SGADM001', 'SGTRA002')
    changed = gym.upsert_usuario({**first, 'rol': 'staff'})
    gym.repository._last_refresh_at = 0
    gym.ensure_fresh(('usuario',))
    assert gym.get_usuario(first['id_usuario'])['rol'] == 'staff'
    assert changed['id_usuario'] == first['id_usuario']
    gym.delete_usuario(second['id_usuario'])
    third = gym.upsert_usuario(dict(nombre='Staff', correo='staff@gmail.com', rol='staff', password='secret123'))
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
        futures = [pool.submit(gym.upsert_usuario, dict(nombre=role, correo=role+'@gmail.com', rol=role, password='secret123'))
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
    saved = gym.registrar_cliente_publico({'nombre': 'Ana', 'correo': 'ana@gmail.com', 'dni': '12345678',
                                          'password': 'secret123', 'telefono': '987654321', 'plan': 'MENSUAL'})
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


def test_client_registration_date_survives_edit_and_database_reload(database, monkeypatch):
    database.sql('''insert into public."CLIENTES" (id_cliente,"Nombres","Correo","Estado","Fecha_Registro")
                   values (1,'Ana','ana@gmail.com',false,'2021-02-03');''')
    gym = service(database, monkeypatch)
    gym.upsert_cliente(dict(id_usuario='SGCLI001', nombre='Ana editada', correo='ana@gmail.com', estado='EN_TRAMITE'))
    gym.repository.cache.invalidate()
    assert gym.get_cliente(1)['fecha_registro'] == '2021-02-03'
    assert database.rows('CLIENTES')[0]['Fecha_Registro'] == '2021-02-03'


def test_order_breakdown_survives_actual_database_reload(database, monkeypatch):
    database.sql('''insert into public."TIENDA_PRODUCTOS" (id_producto,"nombre_Producto","precio_Venta",cantidad_stock)
                   values (1,'Agua',10,5);''')
    gym = service(database, monkeypatch)
    created = gym.crear_pedido_tienda_pago_pendiente({'items': [{'id_producto': 1, 'cantidad': 1}]})
    gym.repository.cache.invalidate()
    reloaded = gym.get_pedido_tienda(created['id_pedido'])
    assert (reloaded['subtotal'], reloaded['igv'], reloaded['total']) == (10, 1.8, 11.8)
    assert reloaded['items'] == created['items']


def test_inactive_internal_account_stays_disabled_after_database_edit(database, monkeypatch):
    from application.services.auth_service import AuthService
    from infrastructure.authentication import SignedSessionProvider
    database.sql('''insert into public."USUARIO" (id_usuario,codigo_usuario,"Nombre","Correo","Rol","Estado")
                   values (1,'SGADM001','Admin','admin@gmail.com','admin',false);''')
    gym = service(database, monkeypatch)
    gym.sessions = SignedSessionProvider()
    gym.upsert_usuario(dict(id_usuario='SGADM001', nombre='Admin editado', correo='admin@gmail.com', rol='admin'))
    gym.repository.cache.invalidate()
    with pytest.raises(ValueError, match='inactiva'):
        AuthService(gym).user_from_payload({'sub': 'SGADM001'})
    assert database.rows('USUARIO')[0]['Estado'] is False


def test_client_deletion_cascades_atomically_with_restrictive_foreign_keys(database, monkeypatch):
    database.sql('''alter table public."MATRICULAS_HORARIO" add constraint review_enrollment_client_fk
                     foreign key (id_cliente) references public."CLIENTES" (id_cliente);
                   alter table public."RUTINA_PROGRESO" add constraint review_progress_enrollment_fk
                     foreign key (id_matricula) references public."MATRICULAS_HORARIO" (id_matricula);''')
    try:
        database.sql('''insert into public."CLIENTES" (id_cliente,"Nombres","Estado") values (1,'Ana',false),(2,'Luis',false);
                       insert into public."HORARIOS_SERVICIO" (id_horario_servicio,cupos,dia,activo) values (1,2,'lunes',true);
                       insert into public."MATRICULAS_HORARIO" (id_matricula,id_cliente,id_horario_servicio,estado,fecha_clase)
                         select i,i,1,'ACTIVA',current_date+((1-extract(isodow from current_date)::integer+7)%7)
                         from generate_series(1,2) i;
                       insert into public."RUTINA_PROGRESO" (id_progreso,id_matricula) values (1,1),(2,2);
                       create function public.review_reject_client_delete() returns trigger language plpgsql as $$
                         begin raise exception 'review deletion rejected'; end $$;
                       create trigger review_reject_client_delete before delete on public."CLIENTES"
                         for each row execute function public.review_reject_client_delete();''')
        gym = service(database, monkeypatch)
        resources = ('clientes', 'matriculas_horario', 'rutina_progreso', 'horarios_servicio')
        gym.ensure_fresh(resources)
        tables = ('CLIENTES', 'MATRICULAS_HORARIO', 'RUTINA_PROGRESO')
        original = {table: database.rows(table) for table in tables}
        with pytest.raises(RuntimeError, match='review deletion rejected'):
            gym.delete_cliente(1)
        assert {table: database.rows(table) for table in tables} == original
        assert len(gym.repository.state['matriculas_horario']) == 2
        assert len(gym.repository.state['rutina_progreso']) == 2
        database.sql('drop trigger review_reject_client_delete on public."CLIENTES";')
        gym.delete_cliente(1)
        assert [row['id_cliente'] for row in database.rows('CLIENTES')] == [2]
        assert [row['id_cliente'] for row in database.rows('MATRICULAS_HORARIO')] == [2]
        assert [row['id_matricula'] for row in database.rows('RUTINA_PROGRESO')] == [2]
        gym.repository.cache.invalidate()
        assert gym.horarios_servicio()[0]['cupos_disponibles'] == 1
    finally:
        database.sql('''drop trigger if exists review_reject_client_delete on public."CLIENTES";
                       drop function if exists public.review_reject_client_delete();
                       alter table public."RUTINA_PROGRESO" drop constraint review_progress_enrollment_fk;
                       alter table public."MATRICULAS_HORARIO" drop constraint review_enrollment_client_fk;''')


def test_routine_transaction_ignores_a_concurrent_attendance_write(database, monkeypatch):
    class Interleaved(Postgres):
        commits = 0
        def rpc(self, name, body):
            if name == 'commit_gym_transaction':
                self.commits += 1
                assert set(body['p_expected']) == {'CATALOGO_RUTINA'}
                database.sql('insert into public."ASISTENCIA" (id_asistencia,id_cliente,"Fecha") values (1,1,\'2026-10-23\');')
            return super().rpc(name, body)
    remote = Interleaved()
    gym = service(remote, monkeypatch)
    routine = gym.upsert_rutina(dict(nombre_rutina='Fuerza', servicio='fitness', zonas_musculares='Pierna'))
    assert remote.commits == 1
    assert database.rows('CATALOGO_RUTINA')[0]['id_rutina'] == routine['id_rutina']
    assert len(database.rows('ASISTENCIA')) == 1


def test_unit_migration_numbers_existing_equipment_once(database):
    database.sql('''insert into public."INVENTARIO" (id_item,"Nombre_item","Tipo","Cantidad_Stock_E","Estado","N_ACTIVO",ubicacion)
                   values (1,'Máquina para correr','Equipo cardiovascular',3,'En mantenimiento',1008,'Sala de cardio'),
                          (2,'Desinfectante','Limpieza',4,'Operativo',1009,'Almacén');''')
    migration = (BACKEND / 'migrations/026_inventario_unidades.sql').read_text()
    database.sql(migration)
    database.sql(migration)  # Repetirla no duplica unidades.
    units = sorted(database.rows('INVENTARIO_UNIDADES'), key=lambda row: row['correlativo'])
    assert [row['codigo'] for row in units] == ['1008-MC-001', '1008-MC-002', '1008-MC-003']
    assert {(row['id_item'], row['estado'], row['ubicacion']) for row in units} == {(1, 'En mantenimiento', 'Sala de cardio')}
    prefixes = {row['id_item']: row['prefijo_activo'] for row in database.rows('INVENTARIO')}
    assert prefixes == {1: 'MC', 2: ''}


def test_equipment_units_are_committed_atomically(database, monkeypatch):
    gym = service(database, monkeypatch)
    item = gym.upsert_inventario(dict(nombre_item='Bicicleta estatica', tipo='Equipo cardiovascular', cantidad_stock=2,
                                      estado='Operativo', ubicacion='Sala de cardio'))
    first = next(u for u in gym.unidades_inventario() if u['correlativo'] == 1)
    gym.actualizar_unidad_inventario(first['id_unidad'], {'estado': 'En mantenimiento', 'ubicacion': 'Taller'})
    gym.repository._last_refresh_at = 0
    gym.ensure_fresh()
    rows = sorted(database.rows('INVENTARIO_UNIDADES'), key=lambda row: row['correlativo'])
    assert [row['codigo'] for row in rows] == [f"{item['n_activo']}-BE-001", f"{item['n_activo']}-BE-002"]
    assert (rows[0]['estado'], rows[0]['ubicacion']) == ('En mantenimiento', 'Taller')
    assert gym.get_item_inventario(item['id_item'])['cantidad_stock'] == 2



def test_unit_transfer_and_restore_are_stored_with_unit_and_time(database, monkeypatch):
    gym = service(database, monkeypatch)
    admin = gym.upsert_usuario(dict(nombre='Admin', correo='admin@gmail.com', rol='admin', password='secret123'))
    gym.upsert_inventario(dict(nombre_item='Banco plano', tipo='Equipo de fuerza', cantidad_stock=2,
                               estado='Operativo', ubicacion='Almacén'))
    first = next(u for u in gym.unidades_inventario() if u['correlativo'] == 1)
    gym.actualizar_unidad_inventario(first['id_unidad'], {'ubicacion': 'Sala de fuerza', 'id_usuario': admin['id_usuario']})
    gym.dar_de_baja_unidad_inventario(first['id_unidad'], {'motivo': 'Rota', 'id_usuario': admin['id_usuario']})
    gym.restablecer_unidad_inventario(first['id_unidad'], {'motivo': 'Soldada', 'id_usuario': admin['id_usuario']})
    rows = sorted(database.rows('MOV_INV'), key=lambda row: row['id_mov'])
    assert [row['tipo_movimiento'] for row in rows] == ['entrada', 'traslado', 'salida', 'entrada']
    assert [row['id_unidad'] for row in rows] == [None, first['id_unidad'], first['id_unidad'], first['id_unidad']]
    assert all(row['hora_movimiento'] for row in rows)
    unit = next(row for row in database.rows('INVENTARIO_UNIDADES') if row['id_unidad'] == first['id_unidad'])
    assert (unit['estado'], unit['ubicacion'], unit['fecha_baja']) == ('Operativo', 'Sala de fuerza', None)
    item = database.rows('INVENTARIO')[0]
    assert item['Cantidad_Stock_E'] == 2



def test_p05_migration_032_confirms_paid_pending_orders_once(database):
    database.sql('''insert into public."VENTAS" (id_venta, estado_pago, estado_pedido) values
                    (901, 'PAGADO', 'PENDIENTE'), (902, 'PENDIENTE', 'PENDIENTE'),
                    (903, 'PAGADO', 'ENTREGADO'), (904, 'pagado', 'pendiente');''')
    migration = (BACKEND / 'migrations/032_bajas_y_pedidos_confirmados.sql').read_text()
    database.sql(migration)
    database.sql(migration)  # Repetirla no cambia nada.
    states = {row['id_venta']: row['estado_pedido'] for row in database.rows('VENTAS') if row['id_venta'] >= 901}
    assert states == {901: 'CONFIRMADO', 902: 'PENDIENTE', 903: 'ENTREGADO', 904: 'CONFIRMADO'}
    database.sql('delete from public."VENTAS" where id_venta >= 901;')


def test_r02_archiving_and_unit_transfer_are_committed_together(database, monkeypatch):
    gym = service(database, monkeypatch)
    admin = gym.upsert_usuario(dict(nombre='Admin', correo='admin2@gmail.com', rol='admin', password='secret123'))
    item = gym.upsert_inventario(dict(nombre_item='Rack sentadilla', tipo='Equipo de fuerza', cantidad_stock=2,
                                      estado='Operativo', ubicacion='Almacén'))
    units = sorted((u for u in gym.unidades_inventario() if u['id_item'] == item['id_item']), key=lambda u: u['correlativo'])
    gym.registrar_movimiento_inventario({'id_item': item['id_item'], 'id_usuario': admin['id_usuario'],
                                         'tipo_movimiento': 'traslado', 'cantidad': 2,
                                         'unidades': [u['id_unidad'] for u in units], 'ubicacion_destino': 'Sala 2'})
    gym.delete_inventario(item['id_item'])
    row = next(r for r in database.rows('INVENTARIO') if r['id_item'] == item['id_item'])
    assert row['archivado'] is True and row['fecha_baja'] is not None
    moved = [r for r in database.rows('MOV_INV') if r['tipo_movimiento'] == 'traslado' and r['id_item'] == item['id_item']]
    assert sorted(r['id_unidad'] for r in moved) == sorted(u['id_unidad'] for u in units)


def test_y10_yape_order_is_stored_pending_until_reception_confirms(database, monkeypatch):
    database.sql('''insert into public."TIENDA_PRODUCTOS" (id_producto,"nombre_Producto","precio_Venta",cantidad_stock)
                   values (77,'Agua Yape',10,5);''')
    gym = service(database, monkeypatch)
    created = gym.crear_pedido_tienda({'metodo_pago': 'Yape', 'items': [{'id_producto': 77, 'cantidad': 2}]})
    row = next(r for r in database.rows('VENTAS') if r['id_venta'] == created['id_pedido'])
    assert (row['metodo_Pago'], row['estado_pago'], row['estado_pedido']) == ('yape', 'PENDIENTE', 'PENDIENTE')
    gym.actualizar_pedido_tienda(created['id_pedido'], {'estado_pedido': 'CONFIRMADO'})
    row = next(r for r in database.rows('VENTAS') if r['id_venta'] == created['id_pedido'])
    assert (row['estado_pago'], row['estado_pedido']) == ('PAGADO', 'CONFIRMADO')
