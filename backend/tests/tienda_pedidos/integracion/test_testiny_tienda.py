"""Contratos documentados de catálogo y pedidos; HTTP real, memoria QA aislada."""
from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.soporte.testiny_api import business_state, documented_api  # noqa: F401


def product(api, **changes):
    response = api.client.post("/api/tienda", json={
        "nombre_producto": "Botella QA", "precio_venta": 15, "categoria": "Bebidas",
        "cantidad_stock": 10, "descripcion": "Producto QA", "imagen_url": "https://example.com/botella.png",
        **changes,
    })
    assert response.status_code == 200, response.text
    return response.json()


def order(api, item, quantity=2, **changes):
    return api.client.post("/api/tienda/pedidos", json={
        "id_cliente": 1, "cliente_nombre": "Cliente QA 1", "cliente_correo": "cliente1@example.com",
        "cliente_dni": "11111111", "metodo_pago": "Yape", "referencia_pago": "QA-no-cobro-real",
        "items": [{"id_producto": item["id_producto"], "cantidad": quantity}], **changes,
    })


def test_tc092_tc093_catalogo_persiste_campos_y_consultar_no_cambia_stock(documented_api):
    api = documented_api
    saved = product(api)
    before = business_state(api)
    [loaded] = api.client.get("/api/tienda").json()
    for field in ("id_producto", "nombre_producto", "precio_venta", "cantidad_stock", "imagen_url", "descripcion", "estado"):
        assert loaded[field] == saved[field]
    assert (loaded["precio_venta"], loaded["cantidad_stock"]) == (15, 10)
    assert business_state(api) == before


def test_tc094_actualizar_precio_no_recalcula_pedido_historico(documented_api):
    api = documented_api
    saved = product(api)
    bought = order(api, saved).json()
    response = api.client.post("/api/tienda", json={**saved, "precio_venta": 25, "descripcion": "Descripción nueva"})
    assert response.status_code == 200, response.text
    [loaded] = api.client.get("/api/tienda").json()
    assert loaded["precio_venta"] == 25 and loaded["descripcion"] == "Descripción nueva"
    [history] = api.client.get("/api/tienda/pedidos").json()
    assert history["items"] == bought["items"]
    assert history["total"] == bought["total"] == 35.40


def test_tc095_producto_retirado_no_admite_compras(documented_api):
    api = documented_api
    saved = product(api)
    assert api.client.delete(f"/api/tienda/{saved['id_producto']}").status_code == 200
    assert api.gym.get_producto_tienda(saved["id_producto"])["archivado"] is True
    before = business_state(api)
    response = order(api, saved)
    assert response.status_code == 400 and "Producto no disponible" in response.text
    assert business_state(api) == before


@pytest.mark.parametrize("changes", [{"nombre_producto": ""}, {"categoria": ""}])
def test_tc096_campos_requeridos_no_crean_producto_ni_reserva(documented_api, changes):
    api = documented_api
    before = business_state(api)
    response = api.client.post("/api/tienda", json={"nombre_producto": "Botella QA", "precio_venta": 15,
                                                   "categoria": "Bebidas", **changes})
    assert response.status_code == 422
    assert business_state(api) == before


@pytest.mark.parametrize("changes", [{"precio_venta": -15}, {"precio_venta": 0}, {"precio_venta": "abc"},
                                      {"cantidad_stock": -1}, {"cantidad_stock": 1.5}])
def test_tc097_precio_y_stock_invalidos_no_escriben(documented_api, changes):
    api = documented_api
    before = business_state(api)
    response = api.client.post("/api/tienda", json={"nombre_producto": "Botella QA", "precio_venta": 15,
                                                   "categoria": "Bebidas", **changes})
    assert response.status_code == 422
    assert business_state(api) == before


def test_tc098_archivar_conserva_venta_y_oculta_producto_e_inventario(documented_api):
    api = documented_api
    saved = product(api)
    bought = order(api, saved).json()
    assert api.client.delete(f"/api/tienda/{saved['id_producto']}").status_code == 200
    assert api.gym.get_producto_tienda(saved["id_producto"])["archivado"] is True
    assert api.gym.get_item_inventario(saved["id_item"])["archivado"] is True
    [history] = api.client.get("/api/tienda/pedidos").json()
    assert history["items"] == bought["items"] and history["total"] == bought["total"]
    assert order(api, saved).status_code == 400


def test_tc101_producto_sin_stock_se_conserva_pero_no_se_vende(documented_api):
    api = documented_api
    saved = product(api, cantidad_stock=0)
    [loaded] = api.client.get("/api/tienda").json()
    assert loaded["estado"] == "Agotado" and loaded["cantidad_stock"] == 0
    before = business_state(api)
    response = order(api, saved, 1)
    assert response.status_code == 400 and "Producto no disponible" in response.text
    assert business_state(api) == before


def test_tc102_compra_calcula_igv_reserva_stock_y_conserva_lineas(documented_api):
    api = documented_api
    saved = product(api)
    api.login("user")
    response = order(api, saved)
    assert response.status_code == 201, response.text
    bought = response.json()
    assert (bought["subtotal"], bought["igv"], bought["total"]) == (30, 5.40, 35.40)
    assert (bought["estado_pago"], bought["estado_pedido"]) == ("PAGADO", "PENDIENTE")
    assert bought["items"][0]["cantidad"] == 2 and bought["items"][0]["precio_unitario"] == 15
    assert api.gym.get_producto_tienda(saved["id_producto"])["cantidad_stock"] == 8
    api.login("admin")
    [history] = api.client.get("/api/tienda/pedidos").json()
    assert history["id_pedido"] == bought["id_pedido"] and history["items"] == bought["items"]


def test_tc103_stock_insuficiente_no_crea_pedido(documented_api):
    api = documented_api
    saved = product(api)
    before = business_state(api)
    response = order(api, saved, 11)
    assert response.status_code == 400 and "Stock insuficiente" in response.text
    assert business_state(api) == before


def test_tc104_carrito_vacio_rechaza_pedido_y_checkout_sin_guardar(documented_api):
    api = documented_api
    api.login("user")
    before = business_state(api)
    response = api.client.post("/api/tienda/pedidos", json={"items": [], "metodo_pago": "Yape"})
    assert response.status_code == 400 and "El pedido no tiene productos" in response.text
    assert api.client.post("/api/tienda/pedidos/checkout", json={"items": []}).status_code == 422
    assert business_state(api) == before


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "abc"])
def test_tc105_cantidad_invalida_no_crea_pedidos_ni_mueve_stock(documented_api, quantity):
    api = documented_api
    saved = product(api)
    before = business_state(api)
    assert order(api, saved, quantity).status_code == 422
    assert business_state(api) == before


def test_tc107_confirmacion_no_exige_stock_ya_reservado(documented_api):
    api = documented_api
    saved = product(api, cantidad_stock=2)
    bought = order(api, saved).json()
    endpoint = f"/api/tienda/pedidos/{bought['id_pedido']}"
    assert api.gym.get_producto_tienda(saved["id_producto"])["cantidad_stock"] == 0
    response = api.client.put(endpoint, json={"estado_pedido": "CONFIRMADO"})
    assert response.status_code == 200, response.text
    assert api.gym.get_producto_tienda(saved["id_producto"])["cantidad_stock"] == 0
    assert response.json()["items"] == bought["items"]


def test_tc141_total_del_navegador_no_reemplaza_precio_autorizado(documented_api):
    api = documented_api
    saved = product(api)
    response = order(api, saved, total=1, subtotal=1, igv=0,
                     items=[{"id_producto": saved["id_producto"], "cantidad": 2, "precio_unitario": 1}])
    assert response.status_code == 201, response.text
    assert response.json()["total"] == 35.40
    assert response.json()["items"][0]["precio_unitario"] == 15
    assert api.gym.pedidos_tienda()[0]["total"] == 35.40


@pytest.mark.parametrize("stock,attempts", [(1, 2), (2, 5)])
def test_tc196_compras_concurrentes_no_sobrevenden(documented_api, stock, attempts):
    api = documented_api
    saved = product(api, cantidad_stock=stock)
    def buy(index):
        return order(api, saved, 1, id_cliente=1 + index % 2)
    with ThreadPoolExecutor(max_workers=attempts) as pool:
        responses = list(pool.map(buy, range(attempts)))
    assert sum(response.status_code == 201 for response in responses) == stock
    assert sum(response.status_code == 400 for response in responses) == attempts - stock
    assert api.gym.get_producto_tienda(saved["id_producto"])["cantidad_stock"] == 0
    assert len(api.gym.pedidos_tienda()) == stock
    assert api.gym.summary()["stats"]["ventas_mes"] == round(stock * 17.70, 2)


def test_tc197_ciclo_entregado_y_cancelado_inmutable(documented_api):
    api = documented_api
    saved = product(api)
    delivered, cancelled = order(api, saved).json(), order(api, saved).json()
    endpoint = f"/api/tienda/pedidos/{delivered['id_pedido']}"
    for status in ("CONFIRMADO", "ENTREGADO"):
        response = api.client.put(endpoint, json={"estado_pedido": status, "observacion_admin": "Entrega QA"})
        assert response.status_code == 200, response.text
        assert response.json()["estado_pedido"] == status
        assert response.json()["observacion_admin"] == "Entrega QA"
        assert api.gym.get_producto_tienda(saved["id_producto"])["cantidad_stock"] == 6
    assert api.client.put(endpoint, json={"estado_pedido": "CANCELADO"}).status_code == 400
    endpoint = f"/api/tienda/pedidos/{cancelled['id_pedido']}"
    assert api.client.put(endpoint, json={"estado_pedido": "CANCELADO"}).status_code == 200
    assert api.gym.get_producto_tienda(saved["id_producto"])["cantidad_stock"] == 8
    assert api.client.put(endpoint, json={"estado_pedido": "CONFIRMADO"}).status_code == 400
    assert api.client.put(endpoint, json={"estado_pedido": "CANCELADO"}).status_code == 200
    assert api.gym.get_producto_tienda(saved["id_producto"])["cantidad_stock"] == 8


def test_tc198_cliente_no_administra_catalogo_ni_pedido_ajeno(documented_api):
    api = documented_api
    saved = product(api)
    other = order(api, saved, id_cliente=2).json()
    api.login("user", 1)
    before = business_state(api)
    for method, endpoint, payload in [
        ("POST", "/api/tienda", {"nombre_producto": "No permitido", "precio_venta": 15, "categoria": "Bebidas"}),
        ("POST", "/api/tienda", {**saved, "precio_venta": 1}),
        ("DELETE", f"/api/tienda/{saved['id_producto']}", None),
        ("PUT", f"/api/tienda/pedidos/{other['id_pedido']}", {"estado_pedido": "CONFIRMADO"}),
    ]:
        assert api.client.request(method, endpoint, json=payload).status_code == 403
    assert business_state(api) == before
    assert api.client.get("/api/tienda/pedidos").json() == []
    bought = order(api, saved, id_cliente=2)
    assert bought.status_code == 201 and bought.json()["id_cliente"] == 1
    assert [row["id_cliente"] for row in api.client.get("/api/tienda/pedidos").json()] == [1]
