"""Aplicación local del asistente con acceso de lectura al catálogo real.

No inicia los trabajos de fondo ni publica rutas de pagos, correo o escritura.
"""

from fastapi import Depends, FastAPI

from application.services.gym_service import GymService
from domain.models.gym import HorarioPublico
from presentation.dependencies import get_gym_service
from presentation.routes.agent_routes import router as agent_router


app = FastAPI(title="Silver Gym: asistente público")
app.include_router(agent_router, prefix="/api")


@app.get("/api/gym/horarios-publicos", response_model=list[HorarioPublico])
def public_schedules(gym: GymService = Depends(get_gym_service)):
    return gym.horarios_servicio(solo_activos=True)


@app.get("/api/planes-membresia")
def public_plans(gym: GymService = Depends(get_gym_service)):
    return gym.planes_membresia()


@app.get("/api/promociones/vigentes-publico")
def public_promotions(gym: GymService = Depends(get_gym_service)):
    return gym.promociones_vigentes_publicas()
