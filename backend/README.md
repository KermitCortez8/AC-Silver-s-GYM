# Backend FastAPI - AC Silver's GYM

Estructura basada en capas `routes`, `services` y `models`, con soporte de `dependencies`, `utils` y persistencia local en `db/state.json`.

## Estructura

```text
backend/
├── db/
├── dependencies/
├── models/
├── routes/
├── services/
├── utils/
├── config.py
├── dependencies.py
├── main.py
└── requirements.txt
```

## Ejecutar

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## Frontend

Configura en el frontend:

```env
VITE_AUTH_API_BASE_URL=http://localhost:8000
```

## Flujos implementados

1. Registro y control de inventario:
- `GET /inventario`
- `POST /inventario`
- `DELETE /inventario/{id_item}`
- `GET /inventario/movimientos`
- `POST /inventario/movimientos`

2. Registro de usuarios y membresía:
- `GET /usuarios`
- `POST /usuarios`
- `GET /clientes`
- `POST /clientes`
- `GET /planes-membresia`
- `POST /planes-membresia`
- `GET /membresias`
- `POST /membresias`
- `POST /registro-cliente-membresia`

3. Registro de asistencia por usuario/cliente:
- `GET /asistencia`
- `POST /asistencia/checkin`
- `POST /asistencia/checkin-dni`

4. Soporte operacional:
- `GET /gym/tickets`, `POST /gym/tickets`
- `GET /gym/rutinas`, `POST /gym/rutinas`
- `GET /gym/horarios`, `POST /gym/horarios`
- `GET /gym/summary`

## Descripción rápida de endpoints

| Endpoint | Método | Qué hace |
|---|---:|---|
| `/auth/google` | POST | Valida la credencial y crea la sesión del usuario. |
| `/auth/me` | GET | Devuelve el usuario autenticado según el token. |
| `/usuarios` | GET/POST | Lista y crea/actualiza usuarios del sistema. |
| `/usuarios/{id_usuario}` | DELETE | Elimina un usuario. |
| `/clientes` | GET/POST | Lista y crea/actualiza clientes. |
| `/clientes/{id_cliente}` | DELETE | Elimina un cliente. |
| `/planes-membresia` | GET/POST | Lista y administra planes de membresía. |
| `/membresias` | GET/POST | Lista y registra membresías. |
| `/registro-cliente-membresia` | POST | Registra cliente y membresía en una sola acción. |
| `/clientes/{id_cliente}/membresias` | GET | Muestra el historial de membresías del cliente. |
| `/asistencia` | GET | Lista la asistencia registrada. |
| `/asistencia/checkin` | POST | Marca asistencia usando el id del cliente. |
| `/asistencia/checkin-dni` | POST | Marca asistencia usando el DNI del cliente. |
| `/inventario` | GET/POST | Lista y administra el inventario. |
| `/inventario/{id_item}` | DELETE | Elimina un ítem del inventario. |
| `/inventario/movimientos` | GET/POST | Lista y registra movimientos de stock. |
| `/gym/summary` | GET | Resume métricas, flujos y alertas del gimnasio. |
| `/gym/tickets` | GET/POST | Lista y registra tickets de atención. |
| `/gym/rutinas` | GET/POST | Lista y administra el catálogo de rutinas. |
| `/gym/horarios` | GET/POST | Lista y administra horarios. |

