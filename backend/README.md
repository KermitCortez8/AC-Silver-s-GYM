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
python -m app.main
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
- `PUT /asistencia/{id_asistencia}`
- `DELETE /asistencia/{id_asistencia}`

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
| `/usuarios` | GET/POST | Lista y crea/actualiza usuarios del sistema. El ID se genera como `SGUS###`. |
| `/usuarios/{id_usuario}` | DELETE | Elimina un usuario. Acepta el formato `SGUS###`. |
| `/clientes` | GET/POST | Lista y crea/actualiza clientes. |
| `/clientes/{id_cliente}` | DELETE | Elimina un cliente. |
| `/membresias` | GET/POST | Lista y registra membresías. |
| `/registro-cliente-membresia` | POST | Registra cliente y membresía en una sola acción. |
| `/clientes/{id_cliente}/membresias` | GET | Muestra el historial de membresías del cliente. |
| `/asistencia` | GET | Lista la asistencia registrada. |
| `/asistencia/checkin` | POST | Marca asistencia usando el id del cliente. |
| `/asistencia/checkin-dni` | POST | Marca asistencia usando el DNI del cliente. |
| `/asistencia/{id_asistencia}` | PUT/DELETE | Edita o elimina un registro de asistencia. |
| `/inventario` | GET/POST | Lista y administra el inventario. |
| `/inventario/{id_item}` | DELETE | Elimina un ítem del inventario. |
| `/inventario/movimientos` | GET/POST | Lista y registra movimientos de stock. |
| `/gym/summary` | GET | Resume métricas, flujos y alertas del gimnasio. |
| `/gym/horarios-servicio` | GET/POST | Lista y actualiza los horarios permitidos por servicio para asistencia. |
| `/gym/tickets` | GET/POST | Lista y registra tickets de atención. |
| `/gym/rutinas` | GET/POST | Lista y administra el catálogo de rutinas. |
| `/gym/horarios` | GET/POST | Lista y administra horarios. |


## Cambios aplicados para feature inventario/tienda/asistencia/horarios

- Se dejó como entrypoint único `backend/app/main.py` y `start.sh` ahora levanta `app.main:app`.
- Se eliminó el `backend/main.py` duplicado, carpetas `__pycache__`, entorno virtual `backend/source` y `package-lock.json` raíz.
- Se registró `store_router` bajo `/api/tienda`.
- Inventario ahora genera y conserva `n_activo` automáticamente para cada item.
- Inventario incluye `unidad_venta`, `precio_venta`, `stock_minimo`, `ubicacion` y `observaciones`.
- Tienda puede vincular productos con items de almacén mediante `id_item` y actualizar unidad/precio de venta.
- Asistencia ahora guarda `id_asistencia` y permite editar/eliminar registros.
- Se agregó configuración de capacidad del gimnasio: `GET/POST /api/gym/configuracion`.
- Se agregó tabla de horarios por servicio: `GET/POST /api/gym/horarios-servicio`.
- Check-in valida capacidad total y capacidad por hora.
- Check-in valida que el servicio esté dentro de su horario configurado.
- Horarios por cliente validan cupos mediante `capacidad_maxima`.
- Planes de membresía ahora tienen CRUD básico en `/api/planes-membresia`.
