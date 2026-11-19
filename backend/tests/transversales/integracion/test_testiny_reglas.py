"""Oráculos de casos documentados adicionales: validación, permisos y lecturas."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from types import SimpleNamespace

import pytest

from application.errors import PersistenceUnavailable
from application.services.auth_service import AuthService
from application.services.membership_notifications import enqueue_expiration_reminders
from tests.soporte.testiny_api import business_state, documented_api  # noqa: F401


USER = {"nombre": "Personal QA", "correo": "staff@example.com", "dni": "66666666", "telefono": "999999999",
        "rol": "staff", "password": "clave-sintetica-qa"}


@pytest.mark.parametrize("changes", [{"nombre": ""}, {"correo": "malformado"}, {"rol": "otro"},
                                      {"rol": ["staff", "trainer"]}, {"telefono": "bad"}])
def test_tc010_datos_y_roles_invalidos_permiten_corregir_sin_duplicar(documented_api, changes):
    api = documented_api
    before = business_state(api)
    response = api.client.post("/api/usuarios", json={**USER, **changes})
    assert response.status_code == 422, response.text
    assert business_state(api) == before
    assert api.client.post("/api/usuarios", json=USER).status_code == 200
    assert sum(user["correo"] == USER["correo"] for user in api.client.get("/api/usuarios").json()) == 1


def test_tc011_solo_admin_staff_gestionan_usuarios(documented_api):
    api = documented_api
    target = api.client.post("/api/usuarios", json=USER).json()
    before = business_state(api)
    for role in ("trainer", "user"):
        api.login(role)
        assert api.client.get("/api/usuarios").status_code == 403
        assert api.client.post("/api/usuarios", json={**USER, "id_usuario": target["id_usuario"]}).status_code == 403
        assert api.client.delete(f"/api/usuarios/{target['id_usuario']}").status_code == 403
    api.login("staff")
    assert api.client.get("/api/usuarios").status_code == 200
    assert business_state(api) == before


def test_tc042_cliente_inexistente_no_tiene_resumen_ni_compra_huerfana(documented_api):
    api = documented_api
    before = business_state(api)
    assert api.gym.get_cliente(999999) is None
    response = api.client.post("/api/membresias", json={"id_cliente": 999999, "id_pm": 1, "fecha_inicio": "2026-10-01", "fecha_fin": "2026-10-31"})
    assert response.status_code in (400, 404), response.text
    assert "Cliente" in response.text
    assert business_state(api) == before


@pytest.mark.parametrize("unavailable", ["inexistente", "inactivo"])
def test_tc043_plan_no_disponible_no_genera_compra(documented_api, unavailable):
    api = documented_api
    api.gym.state["membresia"] = []
    plan = api.gym.get_plan_membresia(1)
    identity = 999999
    if unavailable == "inactivo":
        api.gym.upsert_plan_membresia({**plan, "activo": False})
        assert api.gym.get_plan_membresia(1)["activo"] is False
        identity = 1
    before = business_state(api)
    response = api.client.post("/api/membresias", json={"id_cliente": 1, "id_pm": identity, "fecha_inicio": "2026-10-01", "fecha_fin": "2026-10-31"})
    assert response.status_code in (400, 404), response.text
    assert "plan" in response.text.lower()
    assert business_state(api) == before
    api.gym.upsert_plan_membresia({**plan, "activo": True})
    valid = api.client.post("/api/membresias", json={"id_cliente": 1, "id_pm": 1,
                           "fecha_inicio": "2026-10-01", "fecha_fin": "2026-10-31"})
    assert valid.status_code == 200, valid.text
    assert len(api.gym.membresias()) == 1


@pytest.mark.parametrize("payload", [{}, {"id_cliente": 1}, {"id_pm": 1}])
def test_tc044_compra_incompleta_no_tiene_escrituras(documented_api, payload):
    api = documented_api
    before = business_state(api)
    assert api.client.post("/api/membresias", json=payload).status_code == 422
    assert business_state(api) == before


@pytest.mark.parametrize("variant", ["lejana", "futura", "sin_pago", "renovacion_vigente"])
def test_tc049_sin_vencimientos_elegibles_no_envia_ni_cambia_historia(documented_api, monkeypatch, variant):
    api = documented_api
    monkeypatch.setattr("domain.services.gym_domain_service._today_iso", lambda: "2026-10-07")
    member = {"id_membresia": 1, "id_cliente": 1, "id_pm": 1, "estado": "ACTIVO", "estado_pago": "PAGADO",
              "fecha_inicio": "2026-10-01", "fecha_fin": "2026-12-31", "referencia_pago": "referencia-historica"}
    if variant == "futura":
        member["fecha_inicio"] = "2026-11-01"
    elif variant == "sin_pago":
        member.update(estado="EN_TRAMITE", estado_pago="PENDIENTE", fecha_inicio="", fecha_fin="")
    api.gym.state["membresia"] = [member]
    if variant == "renovacion_vigente":
        member["fecha_fin"] = "2026-10-06"
        api.gym.state["membresia"].append({**member, "id_membresia": 2, "fecha_inicio": "2026-10-07", "fecha_fin": "2026-11-07"})
    events = []
    before = business_state(api)
    enqueue_expiration_reminders(SimpleNamespace(notify=lambda *args: events.append(args)), api.gym, date(2026, 10, 7))
    assert events == []
    assert business_state(api) == before
    if variant == "renovacion_vigente":
        assert api.gym.get_cliente(1)["estado"] == "ACTIVO"


@pytest.mark.parametrize("start,end", [("", ""), ("incorrecta", "2099-12-31"), ("2020-01-01", "incorrecta")])
def test_tc050_fechas_invalidas_no_dan_acceso_y_corregirlas_conserva_pago(documented_api, start, end):
    api = documented_api
    api.gym.state["membresia"] = [dict(api.gym.state["membresia"][0], fecha_inicio=start, fecha_fin=end,
                                      referencia_pago="pago-original-qa", monto_pago=79)]
    before = business_state(api)
    with pytest.raises(ValueError):
        AuthService(api.gym).user_from_payload({"sub": "SGCLI001", "id_cliente": 1})
    events = []
    enqueue_expiration_reminders(SimpleNamespace(notify=lambda *args: events.append(args)), api.gym, date(2026, 10, 7))
    assert events == []
    assert business_state(api) == before
    api.gym.state["membresia"][0].update(fecha_inicio="2020-01-01", fecha_fin="2099-12-31")
    assert AuthService(api.gym).user_from_payload({"sub": "SGCLI001", "id_cliente": 1}).id_cliente == 1
    saved = api.gym.state["membresia"][0]
    assert saved["referencia_pago"] == "pago-original-qa" and saved["monto_pago"] == 79


def test_tc076_resumen_vacio_tiene_ceros_sin_crear_datos(documented_api):
    api = documented_api
    api.gym.state["clientes"] = []
    api.gym.state["membresia"] = []
    before = business_state(api)
    response = api.client.get("/api/gym/summary")
    assert response.status_code == 200
    assert response.json()["stats"]["total_clientes"] == 0
    assert response.json()["stats"]["membresias_activas"] == 0
    assert response.json()["stats"]["asistencias_hoy"] == 0
    assert business_state(api) == before


def test_tc077_fallo_de_consulta_no_presenta_resumen_parcial(documented_api, monkeypatch):
    api = documented_api
    assert api.client.get("/api/gym/summary").status_code == 200
    before = business_state(api)
    def fail(*_args, **_kwargs):
        raise PersistenceUnavailable("detalle-privado-qa")
    monkeypatch.setattr(api.gym.repository, "query", fail)
    response = api.client.get("/api/gym/summary")
    assert response.status_code == 503
    assert "detail" in response.json() and "stats" not in response.json()
    assert "detalle-privado-qa" not in response.text
    assert business_state(api) == before


def test_tc139_dos_salidas_simultaneas_consumen_la_ultima_unidad_una_vez(documented_api):
    api = documented_api
    item = api.client.post("/api/inventario", json={"nombre_item": "Recurso QA", "tipo": "Limpieza", "cantidad_stock": 1}).json()
    def consume(_index):
        return api.client.post("/api/inventario/movimientos", json={"id_item": item["id_item"], "id_usuario": "SGADM001",
                             "tipo_movimiento": "salida", "cantidad": 1, "descripcion": "Salida concurrente QA"})
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(consume, range(2)))
    assert sorted(response.status_code for response in responses) == [200, 400]
    assert api.gym.get_item_inventario(item["id_item"])["cantidad_stock"] == 0
    assert len([row for row in api.gym.movimientos_inventario() if row["tipo_movimiento"] == "salida"]) == 1
