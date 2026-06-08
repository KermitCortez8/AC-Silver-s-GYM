from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from dependencies import get_gym_service
from models.auth import AuthGoogleRequest, AuthPasswordRequest, AuthResponse, UserProfile
from services.auth_service import AuthService
from services.gym_service import GymService
from utils.security import decode_token_payload

router = APIRouter(prefix="/auth", tags=["auth"])


# POST /auth/google: valida la credencial y crea la sesión del usuario.
@router.post("/google", response_model=AuthResponse)
def google_auth(payload: AuthGoogleRequest, gym_service: GymService = Depends(get_gym_service)):
    auth_service = AuthService(gym_service)
    try:
        return auth_service.google_auth(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/password", response_model=AuthResponse)
def password_auth(payload: AuthPasswordRequest, gym_service: GymService = Depends(get_gym_service)):
    auth_service = AuthService(gym_service)
    try:
        return auth_service.password_auth(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error


# GET /auth/me: devuelve los datos del usuario autenticado a partir del token.
@router.get("/me", response_model=UserProfile)
def auth_me(
    authorization: str | None = Header(default=None),
    gym_service: GymService = Depends(get_gym_service),
):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta token")
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_token_payload(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    auth_service = AuthService(gym_service)
    return auth_service.user_from_payload(payload)
