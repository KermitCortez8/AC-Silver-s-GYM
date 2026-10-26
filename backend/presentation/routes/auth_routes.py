"""Acceso con Google o contraseña y consulta de la sesión verificada."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from presentation.dependencies import get_current_user, get_gym_service, get_identity_service
from domain.models.auth import AuthGoogleRequest, AuthPasswordRequest, AuthResponse, GoogleProfile, UserProfile
from application.services.auth_service import AuthService, ClientActivationRequired, GoogleLinkRequired
from application.services.gym_service import GymService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google/profile", response_model=GoogleProfile)
def google_profile(payload: AuthGoogleRequest, identity=Depends(get_identity_service)):
    try:
        return GoogleProfile(**identity.profile(payload.credential))
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/google", response_model=AuthResponse)
def google_auth(payload: AuthGoogleRequest, gym_service: GymService = Depends(get_gym_service)):
    try:
        return AuthService(gym_service).google_auth(payload)
    except GoogleLinkRequired as error:
        raise HTTPException(status_code=409, detail={"code": "google_link_required", "message": str(error)}) from error
    except ClientActivationRequired as error:
        raise HTTPException(status_code=403, detail={"code": error.code, "message": str(error)}) from error
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/password", response_model=AuthResponse)
def password_auth(payload: AuthPasswordRequest, gym_service: GymService = Depends(get_gym_service)):
    try:
        return AuthService(gym_service).password_auth(payload)
    except ClientActivationRequired as error:
        raise HTTPException(status_code=403, detail={"code": error.code, "message": str(error)}) from error
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/me", response_model=UserProfile)
def auth_me(current_user: UserProfile = Depends(get_current_user)):
    return current_user
