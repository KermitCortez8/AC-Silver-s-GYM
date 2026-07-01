from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes.attendance_routes import router as attendance_router
from routes.auth_routes import router as auth_router
from routes.clients_routes import router as clients_router
from routes.gym_routes import router as gym_router
from routes.inventory_routes import router as inventory_router
from routes.memberships_routes import router as membership_router
from routes.store_routes import router as store_router
from routes.trainer_routes import router as trainer_router
from routes.users_routes import router as users_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Backend HTTP con FastAPI para AC Silver's GYM",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(auth_router, prefix="/api")
app.include_router(gym_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(clients_router, prefix="/api")
app.include_router(membership_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(store_router, prefix="/api")
app.include_router(trainer_router, prefix="/api")


def main() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()
