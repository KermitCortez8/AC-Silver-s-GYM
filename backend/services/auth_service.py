from __future__ import annotations

from models.auth import AuthGoogleRequest, AuthResponse, UserProfile
from services.gym_service import GymService
from utils.security import get_expiry_seconds, get_user_role, normalize_profile


class AuthService:
    def __init__(self, gym_service: GymService) -> None:
        self.gym_service = gym_service

    def google_auth(self, payload: AuthGoogleRequest) -> AuthResponse:
        profile = normalize_profile(payload.profile, payload.credential)
        if not profile["email"]:
            raise ValueError("No se pudo validar la credencial")

        usuario = self.gym_service.get_usuario_by_email(profile["email"])
        if usuario:
            profile["id"] = str(usuario.get("id_usuario") or profile["id"])
            profile["id_usuario"] = str(usuario.get("id_usuario") or profile["id"])
            profile["correo"] = str(usuario.get("correo") or usuario.get("email") or profile["email"])
            profile["email"] = profile["correo"]
            profile["telefono"] = str(usuario.get("telefono") or "")
            profile["role"] = usuario.get("rol", profile["role"])
        else:
            profile["role"] = get_user_role(profile["email"])

        return AuthResponse(
            user=UserProfile(**profile),
            token=payload.credential,
            expiresIn=get_expiry_seconds(payload.credential),
        )

    def user_from_payload(self, payload: dict) -> UserProfile:
        profile = normalize_profile(payload, "")
        usuario = self.gym_service.get_usuario_by_email(profile["email"])
        if usuario:
            profile["id"] = str(usuario.get("id_usuario") or profile["id"])
            profile["id_usuario"] = str(usuario.get("id_usuario") or profile["id"])
            profile["correo"] = str(usuario.get("correo") or usuario.get("email") or profile["email"])
            profile["email"] = profile["correo"]
            profile["telefono"] = str(usuario.get("telefono") or "")
            profile["role"] = usuario.get("rol", profile["role"])
        return UserProfile(**profile)
