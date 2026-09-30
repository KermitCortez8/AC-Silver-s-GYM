from app.main import get_gym_service
import asyncio
import json

async def test():
    svc = get_gym_service()
    
    # Simular la creacion de cliente
    payload = {
        "cliente": {
            "nombre": "Rodrigo 11",
            "correo": "rodrigo11@gmail.com",
            "telefono": "920111222",
            "dni": "76111222",
            "password": "testpassword",
            "plan": "MENSUAL",
            "estado": "ACTIVO"
        },
        "id_pm": 1,
        "fecha_inicio": "2026-09-23",
        "fecha_fin": "2026-10-23",
        "id_promocion": 3
    }
    
    print('Testing registrar_cliente_con_membresia...')
    try:
        res = svc.registrar_cliente_con_membresia(payload)
        
        # Check if it's in the state
        mem = svc.gym._latest_membership_for_cliente(svc.state, res['cliente']['id_cliente'])
        print('State Mem:', mem)
        
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
