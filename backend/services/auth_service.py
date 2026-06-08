from __future__ import annotations

from models.auth import AuthGoogleRequest, AuthPasswordRequest, AuthResponse, UserProfile
from services.gym_service import GymService
from utils.security import create_local_token, get_expiry_seconds, get_user_role, normalize_profile


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
            cliente = self.gym_service.get_cliente_by_email(profile["email"])
            if cliente:
                profile["id"] = str(cliente.get("id_usuario") or f"SGCLI{int(cliente.get('id_cliente', 0)):03d}")
                profile["id_usuario"] = str(cliente.get("id_usuario") or profile["id"])
                profile["id_cliente"] = int(cliente.get("id_cliente", 0) or 0)
                profile["correo"] = str(cliente.get("correo") or cliente.get("email") or profile["email"])
                profile["email"] = profile["correo"]
                profile["telefono"] = str(cliente.get("telefono") or "")
                profile["dni"] = str(cliente.get("dni") or "")
                profile["name"] = str(cliente.get("nombre") or profile["name"])
                profile["role"] = "user"
            else:
                profile["role"] = get_user_role(profile["email"])

        return AuthResponse(
            user=UserProfile(**profile),
            token=payload.credential,
            expiresIn=get_expiry_seconds(payload.credential),
        )

    def password_auth(self, payload: AuthPasswordRequest) -> AuthResponse:
        correo = str(payload.correo or "").strip().lower()
        password = str(payload.password or "")
        if not correo or not password:
            raise ValueError("Ingresa correo y contraseña")

        usuario = self.gym_service.authenticate_usuario_password(correo, password)
        if usuario:
            profile = {
                "id": str(usuario.get("id_usuario") or correo),
                "id_usuario": str(usuario.get("id_usuario") or ""),
                "email": str(usuario.get("correo") or correo),
                "correo": str(usuario.get("correo") or correo),
                "telefono": str(usuario.get("telefono") or ""),
                "dni": str(usuario.get("dni") or ""),
                "name": str(usuario.get("nombre") or correo),
                "role": str(usuario.get("rol") or "staff"),
            }
            token = create_local_token(profile)
            return AuthResponse(user=UserProfile(**profile), token=token, expiresIn=3600)

        cliente = self.gym_service.authenticate_cliente_password(correo, password)
        if cliente:
            profile = {
                "id": str(cliente.get("id_usuario") or f"SGCLI{int(cliente.get('id_cliente', 0)):03d}"),
                "id_usuario": str(cliente.get("id_usuario") or ""),
                "id_cliente": int(cliente.get("id_cliente", 0) or 0),
                "email": str(cliente.get("correo") or correo),
                "correo": str(cliente.get("correo") or correo),
                "telefono": str(cliente.get("telefono") or ""),
                "dni": str(cliente.get("dni") or ""),
                "name": str(cliente.get("nombre") or correo),
                "role": "user",
            }
            token = create_local_token(profile)
            return AuthResponse(user=UserProfile(**profile), token=token, expiresIn=3600)

        raise ValueError("Correo o contraseña incorrectos")

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
            profile["dni"] = str(usuario.get("dni") or "")
            return UserProfile(**profile)

        cliente = self.gym_service.get_cliente_by_email(profile["email"])
        if cliente:
            profile["id"] = str(cliente.get("id_usuario") or f"SGCLI{int(cliente.get('id_cliente', 0)):03d}")
            profile["id_usuario"] = str(cliente.get("id_usuario") or profile["id"])
            profile["id_cliente"] = int(cliente.get("id_cliente", 0) or 0)
            profile["correo"] = str(cliente.get("correo") or cliente.get("email") or profile["email"])
            profile["email"] = profile["correo"]
            profile["telefono"] = str(cliente.get("telefono") or "")
            profile["dni"] = str(cliente.get("dni") or "")
            profile["name"] = str(cliente.get("nombre") or profile["name"])
            profile["role"] = "user"
        return UserProfile(**profile)
