from app.main import get_gym_service
import asyncio

async def test():
    svc = get_gym_service()
    try:
        # Hacer fetch manual usando _request
        data = svc._request("GET", "MEMBRESIA", query={"select": "*", "limit": "5"})
        print('MEMBRESIA Data:', data)
    except Exception as e:
        print('Error:', e)

asyncio.run(test())
