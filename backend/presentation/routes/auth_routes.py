"""Acceso con Google o contraseña y consulta de la sesión verificada."""
from __future__ import annotations

from presentation.error_handlers import http_error

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response

from presentation.dependencies import get_current_user, get_gym_service, get_identity_service, get_password_recovery
from domain.models.auth import (
    AuthGoogleRequest, AuthPasswordRequest, AuthResponse, GoogleProfile, PasswordRecoveryRequest,
    PasswordResetRequest, UpdateProfileRequest, UserProfile,
)
from application.services.auth_service import AuthService, ClientActivationRequired, GoogleLinkRequired
from application.services.gym_service import GymService
from application.services.password_recovery import PasswordRecoveryLimit

router = APIRouter(prefix="/auth", tags=["auth"])
_password_recovery_limit = PasswordRecoveryLimit()


def get_password_recovery_limit():
    return _password_recovery_limit


@router.post("/google/profile", response_model=GoogleProfile)
def google_profile(payload: AuthGoogleRequest, identity=Depends(get_identity_service)):
    try:
        return GoogleProfile(**identity.profile(payload.credential))
    except ValueError as error:
        raise http_error(error, validation_status=401) from error
    except RuntimeError as error:
        raise http_error(error, validation_status=503) from error


@router.post("/google", response_model=AuthResponse)
def google_auth(payload: AuthGoogleRequest, gym_service: GymService = Depends(get_gym_service)):
    try:
        return AuthService(gym_service).google_auth(payload)
    except GoogleLinkRequired as error:
        raise HTTPException(status_code=409, detail={"code": "google_link_required", "message": str(error)}) from error
    except ClientActivationRequired as error:
        raise HTTPException(status_code=403, detail={"code": error.code, "message": str(error)}) from error
    except ValueError as error:
        raise http_error(error, validation_status=401) from error
    except RuntimeError as error:
        raise http_error(error, validation_status=503) from error


@router.post("/password", response_model=AuthResponse)
def password_auth(payload: AuthPasswordRequest, gym_service: GymService = Depends(get_gym_service)):
    try:
        return AuthService(gym_service).password_auth(payload)
    except ClientActivationRequired as error:
        raise HTTPException(status_code=403, detail={"code": error.code, "message": str(error)}) from error
    except ValueError as error:
        raise http_error(error, validation_status=401) from error
    except RuntimeError as error:
        raise http_error(error, validation_status=503) from error


@router.get("/me", response_model=UserProfile)
def auth_me(current_user: UserProfile = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserProfile)
def update_auth_me(
    payload: UpdateProfileRequest,
    current_user: UserProfile = Depends(get_current_user),
    gym_service: GymService = Depends(get_gym_service),
):
    return AuthService(gym_service).update_profile(current_user, payload)


@router.post("/recuperar-contrasena", status_code=202)
def request_password_recovery(
    payload: PasswordRecoveryRequest, request: Request, background: BackgroundTasks,
    recovery=Depends(get_password_recovery), limit=Depends(get_password_recovery_limit),
):
    if not limit.allow(request.client.host if request.client else ""):
        raise HTTPException(status_code=429, detail="Espera unos minutos antes de volver a solicitar un enlace.")
    email = recovery.validate_request(payload.correo)
    background.add_task(recovery.send, email)
    return {"message": "Si el correo está registrado, recibirás un enlace de recuperación."}


@router.post("/restablecer-contrasena", status_code=204)
def reset_password(payload: PasswordResetRequest, recovery=Depends(get_password_recovery)):
    recovery.reset(payload.token.get_secret_value(), payload.password_nueva.get_secret_value())
    return Response(status_code=204)
