"""Borrado con ventas: integración solo en PostgreSQL desechable explícito."""
from copy import deepcopy
import os
from pathlib import Path

import pytest

from tests.transversales.postgres.test_atomic_transactions_postgres import Postgres, clear, database as base_database, service

pytestmark = pytest.mark.skipif(not os.getenv('GYM_TEST_POSTGRES_CONTAINER'),
    reason='Requiere un PostgreSQL desechable explícito')


@pytest.fixture(scope='module')
def database(base_database):
    # Reproduce el esquema histórico remoto sin copias del comprador y con FK restrictiva.
    base_database.sql('''alter table public."VENTAS"
        drop column cliente_nombre, drop column cliente_correo, drop column cliente_dni,
        alter column id_cliente set not null;
        alter table public."VENTAS" add constraint venta_cliente_historico_fk
        foreign key (id_cliente) references public."CLIENTES" (id_cliente);
        alter table public."ASISTENCIA" add constraint asistencia_cliente_historico_fk
        foreign key (id_cliente) references public."CLIENTES" (id_cliente);
        alter table public."ASISTENCIA" add column limite_salida timestamptz,
        add column salida_tardia boolean not null default false;''')
    migration = (Path(__file__).resolve().parents[3] / 'migrations/025_delete_clients_preserve_sales.sql').read_text()
    base_database.sql(migration)
    base_database.sql(migration)
    return base_database


def seed(database):
    database.sql('''insert into public."CLIENTES" (id_cliente,"Nombres","Apellidos","Correo","DNI","Estado")
        values (1,'Ana','Prueba','ana@example.com','12345678',true),
               (2,'Luis','Prueba','luis@example.com','87654321',true);
        insert into public."VENTAS" (id_venta,id_cliente,"Fecha_Venta","total_Venta","metodo_Pago",estado_pago,estado_pedido,referencia_pago)
        values (1,1,'2026-10-06',7.67,'tarjeta','PAGADO','PENDIENTE','pago-sintetico'),
               (2,2,'2026-10-07',10,'efectivo','PAGADO','COMPLETADO','otro-pago');
        insert into public."DETALLE_VENTA" (id_venta,id_producto,"Cantidad","Precio_Unitario","Subtotal")
        values (1,5,1,6.5,6.5),(2,5,1,10,10);
        insert into public."ASISTENCIA" (id_asistencia,id_cliente,"Fecha")
        values (1,1,'2026-10-06'),(2,2,'2026-10-07');
        insert into public."TIENDA_PRODUCTOS" (id_producto,"nombre_Producto",cantidad_stock)
        values (5,'Agua',10);''')


def test_borrar_cliente_conserva_venta_pagada_detalles_y_otro_cliente(database, monkeypatch):
    seed(database)
    before = {table: database.rows(table) for table in ['VENTAS', 'DETALLE_VENTA', 'TIENDA_PRODUCTOS']}
    gym = service(database, monkeypatch)
    gym.delete_cliente(1)
    assert [r['id_cliente'] for r in database.rows('CLIENTES')] == [2]
    assert [r['id_cliente'] for r in database.rows('ASISTENCIA')] == [2]
    expected = deepcopy(before['VENTAS'])
    expected[0].update(id_cliente=None, cliente_nombre='Ana Prueba',
                       cliente_correo='ana@example.com', cliente_dni='12345678')
    assert sorted(database.rows('VENTAS'), key=lambda r: r['id_venta']) == expected
    for table in ['DETALLE_VENTA', 'TIENDA_PRODUCTOS']:
        assert database.rows(table) == before[table]
    assert next(r for r in gym.repository.state['pedidos_tienda'] if r['id_pedido'] == 1)['id_cliente'] is None
    gym.repository.cache.invalidate()
    gym.ensure_fresh(('pedidos_tienda',))
    saved = next(r for r in gym.repository.state['pedidos_tienda'] if r['id_pedido'] == 1)
    assert (saved['cliente_nombre'], saved['total'], saved['referencia_pago']) == (
        'Ana Prueba', 7.67, 'pago-sintetico')


def test_fallo_del_borrado_revierte_desvinculacion_y_copias_del_comprador(database, monkeypatch):
    seed(database)
    database.sql('''create function public.rechazar_borrado_prueba() returns trigger language plpgsql as $$
        begin raise exception 'borrado rechazado'; end $$;
        create trigger zz_rechazar_borrado_prueba before delete on public."CLIENTES"
        for each row execute function public.rechazar_borrado_prueba();''')
    try:
        before = {t: database.rows(t) for t in ['CLIENTES', 'VENTAS', 'DETALLE_VENTA', 'ASISTENCIA']}
        gym = service(database, monkeypatch)
        with pytest.raises(RuntimeError, match='borrado rechazado'):
            gym.delete_cliente(1)
        assert {t: database.rows(t) for t in before} == before
        assert len(gym.repository.state['clientes']) == 2
        assert all(r['id_cliente'] for r in gym.repository.state['pedidos_tienda'])
    finally:
        database.sql('''drop trigger zz_rechazar_borrado_prueba on public."CLIENTES";
            drop function public.rechazar_borrado_prueba();''')


def test_venta_concurrente_obliga_recalcular_y_tambien_se_conserva(database, monkeypatch):
    seed(database)

    class ConcurrentSale(Postgres):
        commits = 0

        def rpc(self, name, body):
            if name == 'commit_gym_transaction':
                self.commits += 1
                assert {'CLIENTES', 'VENTAS', 'DETALLE_VENTA'} <= body['p_expected'].keys()
                if self.commits == 1:
                    database.sql('''insert into public."VENTAS" (id_venta,id_cliente,"total_Venta",estado_pago)
                        values (3,1,15,'PAGADO');''')
            return super().rpc(name, body)

    remote = ConcurrentSale()
    gym = service(remote, monkeypatch)
    gym.delete_cliente(1)
    assert remote.commits == 2
    sales = {r['id_venta']: r for r in database.rows('VENTAS')}
    for identity in [1, 3]:
        assert sales[identity]['id_cliente'] is None
        assert sales[identity]['cliente_nombre'] == 'Ana Prueba'
    assert sales[2]['id_cliente'] == 2
