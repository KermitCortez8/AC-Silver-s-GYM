from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes.attendance_routes import router as attendance_router
from routes.auth_routes import router as auth_router
from routes.gym_routes import router as gym_router
from routes.inventory_routes import router as inventory_router
from routes.members_routes import router as members_router

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


app.include_router(auth_router)
app.include_router(gym_router)
app.include_router(members_router)
app.include_router(attendance_router)
app.include_router(inventory_router)
