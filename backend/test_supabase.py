from app.main import get_gym_service
import asyncio

async def test():
    svc = get_gym_service()
    mem_data = svc._membership_to_remote({
        "id_membresia": 9999,
        "fecha_inicio": "2026-09-23",
        "fecha_fin": "2026-10-23",
        "estado": "PENDIENTE_PAGO",
        "id_cliente": 54,
        "id_pm": 1,
        "monto_pago": 64.0,
        "estado_pago": "PENDIENTE",
        "metodo_pago": "stripe",
        "id_promocion": 3,
        "referencia_pago": "",
        "fecha_pago": ""
    })
    print('Sending:', mem_data)
    
    try:
        res = svc.insert("MEMBRESIA", mem_data)
        print('Response:', res)
    except Exception as e:
        print('Error:', e)

asyncio.run(test())
