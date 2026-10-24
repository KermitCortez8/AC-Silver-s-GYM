import asyncio

async def test():
    from app.main import get_gym_service

    svc = get_gym_service()
    try:
        # Consultar mediante el servicio de aplicación
        data = svc.membresias()[:5]
        print('MEMBRESIA Data:', data)
    except Exception as e:
        print('Error:', e)

if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    asyncio.run(test())
