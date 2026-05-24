import json
import base64
from pathlib import Path
import sys
from pprint import pprint

from fastapi.testclient import TestClient

# Asegúrate que el paquete backend esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app


DB_PATH = Path(__file__).resolve().parents[1] / "db" / "state.json"


def load_state():
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def save_state(state):
    DB_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def run():
    original = load_state()
    client = TestClient(app)
    errors = []

    try:
        print("-> POST /auth/google")
        payload = {"credential": "fake-token", "profile": {"sub": "123", "email": "test@example.com", "name": "Test User", "picture": ""}}
        r = client.post("/auth/google", json=payload)
        print(r.status_code, r.text)
        if r.status_code != 200:
            errors.append(("/auth/google", r.status_code, r.text))
        else:
            # Construir un token base64 válido a partir del profile para poder usar /auth/me
            profile = payload.get("profile") or {}
            token = base64.b64encode(json.dumps(profile).encode()).decode()
            headers = {"Authorization": f"Bearer {token}"}

            print("-> GET /auth/me")
            r = client.get("/auth/me", headers=headers)
            print(r.status_code, r.text)
            if r.status_code != 200:
                errors.append(("/auth/me", r.status_code, r.text))

        print("-> GET /usuarios")
        r = client.get("/usuarios")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/usuarios", r.status_code, r.text))

        print("-> POST /usuarios")
        user_payload = {"dni": "99999999", "contrasena": "pass123", "rol": "user", "email": "testuser@example.com"}
        r = client.post("/usuarios", json=user_payload)
        print(r.status_code, r.text)
        if r.status_code not in (200, 201):
            errors.append(("POST /usuarios", r.status_code, r.text))
        else:
            new_user = r.json()

        print("-> GET /clientes")
        r = client.get("/clientes")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/clientes", r.status_code, r.text))

        print("-> POST /clientes")
        cliente_payload = {"nombres": "Prueba", "apellidos": "Cliente", "dni": "88888888", "telefono": "999000111", "email": "cliente@prueba.com"}
        r = client.post("/clientes", json=cliente_payload)
        print(r.status_code, r.text)
        if r.status_code not in (200, 201):
            errors.append(("POST /clientes", r.status_code, r.text))
        else:
            cliente = r.json()

        print("-> GET /planes-membresia")
        r = client.get("/planes-membresia")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/planes-membresia", r.status_code, r.text))

        print("-> POST /planes-membresia")
        plan_payload = {"nombre_plan": "Trimestral", "duracion": "90 dias", "precio": 200}
        r = client.post("/planes-membresia", json=plan_payload)
        print(r.status_code, r.text)
        if r.status_code not in (200, 201):
            errors.append(("POST /planes-membresia", r.status_code, r.text))
        else:
            plan = r.json()

        print("-> POST /registro-cliente-membresia")
        reg_payload = {"cliente": cliente_payload, "id_pm": plan.get("id_pm"), "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31"}
        r = client.post("/registro-cliente-membresia", json=reg_payload)
        print(r.status_code, r.text)
        if r.status_code not in (200, 201):
            errors.append(("POST /registro-cliente-membresia", r.status_code, r.text))

        print("-> GET /membresias")
        r = client.get("/membresias")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/membresias", r.status_code, r.text))

        print("-> GET /asistencia")
        r = client.get("/asistencia")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/asistencia", r.status_code, r.text))

        print("-> POST /asistencia/checkin (cliente con id 1 existente)")
        r = client.post("/asistencia/checkin", json={"id_cliente": 1})
        print(r.status_code, r.text)
        if r.status_code not in (200, 201):
            errors.append(("POST /asistencia/checkin", r.status_code, r.text))

        print("-> POST /asistencia/checkin-dni (dni existente)")
        r = client.post("/asistencia/checkin-dni", json={"dni": "74281635"})
        print(r.status_code, r.text)
        if r.status_code not in (200, 201):
            errors.append(("POST /asistencia/checkin-dni", r.status_code, r.text))

        print("-> GET /inventario")
        r = client.get("/inventario")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/inventario", r.status_code, r.text))

        print("-> POST /inventario")
        inv_payload = {"nombre_item": "Colchoneta", "tipo": "Accesorio", "cantidad_stock": 5, "stock_minimo": 2}
        r = client.post("/inventario", json=inv_payload)
        print(r.status_code, r.text)
        if r.status_code not in (200, 201):
            errors.append(("POST /inventario", r.status_code, r.text))
        else:
            item = r.json()

        print("-> POST /inventario/movimientos (entrada)")
        mov_payload = {"id_item": 1, "id_usuario": 1, "tipo_movimiento": "entrada", "cantidad": 2}
        r = client.post("/inventario/movimientos", json=mov_payload)
        print(r.status_code, r.text)
        if r.status_code not in (200, 201):
            errors.append(("POST /inventario/movimientos", r.status_code, r.text))

        print("-> GET /gym/summary")
        r = client.get("/gym/summary")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/gym/summary", r.status_code, r.text))

        print("-> GET /gym/tickets")
        r = client.get("/gym/tickets")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/gym/tickets", r.status_code, r.text))

        print("-> GET /gym/rutinas")
        r = client.get("/gym/rutinas")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/gym/rutinas", r.status_code, r.text))

        print("-> GET /gym/horarios")
        r = client.get("/gym/horarios")
        print(r.status_code)
        if r.status_code != 200:
            errors.append(("/gym/horarios", r.status_code, r.text))

    finally:
        # Restaurar estado
        save_state(original)

    print("\nRESULTADOS:")
    if not errors:
        print("Todas las pruebas HTTP terminaron sin errores.")
    else:
        print(f"Se encontraron {len(errors)} errores:")
        pprint(errors)


if __name__ == "__main__":
    run()
