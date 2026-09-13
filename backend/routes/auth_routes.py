"""Acceso con Google o contraseña y consulta de la sesión verificada."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_current_user, get_gym_service
from models.auth import AuthGoogleRequest, AuthPasswordRequest, AuthResponse, GoogleProfile, UserProfile
from services.auth_service import AuthService, ClientActivationRequired, GoogleLinkRequired
from services.google_auth_service import verify_google_credential
from services.gym_domain_service import GymDomainService
from utils.security import normalize_profile

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google/profile", response_model=GoogleProfile)
def google_profile(payload: AuthGoogleRequest):
    try:
        return GoogleProfile(**normalize_profile(verify_google_credential(payload.credential), ""))
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/google", response_model=AuthResponse)
def google_auth(payload: AuthGoogleRequest, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return AuthService(gym_service).google_auth(payload)
    except GoogleLinkRequired as error:
        raise HTTPException(status_code=409, detail={"code": "google_link_required", "message": str(error)}) from error
    except ClientActivationRequired as error:
        raise HTTPException(status_code=403, detail={"code": "account_pending_activation", "message": str(error)}) from error
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/password", response_model=AuthResponse)
def password_auth(payload: AuthPasswordRequest, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return AuthService(gym_service).password_auth(payload)
    except ClientActivationRequired as error:
        raise HTTPException(status_code=403, detail={"code": "account_pending_activation", "message": str(error)}) from error
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/me", response_model=UserProfile)
def auth_me(current_user: UserProfile = Depends(get_current_user)):
    return current_user
