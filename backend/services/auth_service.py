"""Autentica cuentas existentes y emite sesiones firmadas del gimnasio."""
from __future__ import annotations

from models.auth import AuthGoogleRequest, AuthPasswordRequest, AuthResponse, UserProfile
from services.google_auth_service import verify_google_credential
from services.gym_domain_service import GymDomainService
from utils.security import create_local_token, get_auth_secret, normalize_profile, verify_password


class GoogleLinkRequired(ValueError):
    pass


class ClientActivationRequired(ValueError):
    def __init__(self) -> None:
        super().__init__(
            "Tu cuenta aún no está activa. Debe ser activada por el administrador para poder ingresar."
        )


class AuthService:
    def __init__(self, gym_service: GymDomainService) -> None:
        self.gym_service = gym_service

    @staticmethod
    def _profile(account: dict, *, client: bool, google: dict | None = None) -> UserProfile:
        profile = normalize_profile(google or {}, "")
        account_id = str(account.get("id_usuario") or f"SGCLI{int(account.get('id_cliente', 0)):03d}")
        profile.update(
            id=account_id,
            id_usuario=account_id,
            id_cliente=int(account["id_cliente"]) if client else None,
            email=str(account.get("correo") or account.get("email") or ""),
            name=str(account.get("nombre") or profile["name"]),
            telefono=str(account.get("telefono") or ""),
            dni=str(account.get("dni") or ""),
            role="user" if client else str(account.get("rol") or "staff"),
        )
        return UserProfile(**profile)

    @staticmethod
    def _require_active_client(client: dict | None) -> None:
        # CLIENTES.Estado se habilita en la activación administrativa, no al pagar.
        if not client or str(client.get("estado") or "").strip().upper() not in {"ACTIVO", "ACTIVA"}:
            raise ClientActivationRequired()

    def session_for_user(self, user: UserProfile) -> AuthResponse:
        if user.id_cliente is not None:
            self._require_active_client(self.gym_service.get_cliente(user.id_cliente))
        return AuthResponse(user=user, token=create_local_token(user.model_dump()), expiresIn=3600)

    def session_for_client(self, client: dict, google: dict | None = None) -> AuthResponse:
        return self.session_for_user(self._profile(client, client=True, google=google))

    def google_auth(self, payload: AuthGoogleRequest) -> AuthResponse:
        claims = verify_google_credential(payload.credential)
        get_auth_secret()  # Valida configuración antes de persistir una vinculación.
        subject = str(claims["sub"])
        match = self.gym_service.get_account_by_google_sub(subject)
        if match:
            kind, account = match
            return self.session_for_user(self._profile(account, client=kind == "clientes", google=claims))

        email = str(claims["email"]).strip().lower()
        account = self.gym_service.get_usuario_by_email(email)
        kind = "usuario"
        if not account:
            account = self.gym_service.get_cliente_by_email(email)
            kind = "clientes"
        if not account:
            raise ValueError("Aún no tienes una cuenta. Ve a Registrarse y completa tu registro con Google.")
        if account.get("google_sub"):
            raise ValueError("Esta cuenta ya está vinculada a otra identidad de Google")
        if not payload.password:
            raise GoogleLinkRequired("Ya tienes una cuenta. Confirma tu contraseña del gimnasio para vincular Google.")
        if not verify_password(payload.password, str(account.get("password_hash") or "")):
            raise GoogleLinkRequired("La contraseña del gimnasio es incorrecta. Inténtalo nuevamente.")
        if kind == "clientes":
            self._require_active_client(account)
        account = self.gym_service.link_google_account(kind, account["id_usuario"], subject)
        return self.session_for_user(self._profile(account, client=kind == "clientes", google=claims))

    def password_auth(self, payload: AuthPasswordRequest) -> AuthResponse:
        correo = str(payload.correo or "").strip().lower()
        if not correo or not payload.password:
            raise ValueError("Ingresa correo y contraseña")
        usuario = self.gym_service.authenticate_usuario_password(correo, payload.password)
        if usuario:
            return self.session_for_user(self._profile(usuario, client=False))
        cliente = self.gym_service.authenticate_cliente_password(correo, payload.password)
        if cliente:
            return self.session_for_client(cliente)
        raise ValueError("Correo o contraseña incorrectos")

    def user_from_payload(self, payload: dict) -> UserProfile:
        # Roles y datos actuales salen de la base de datos, usando el ID de la sesión firmada.
        client = payload.get("id_cliente") is not None
        rows = self.gym_service.state["clientes" if client else "usuario"]
        account = next((row for row in rows if str(row.get("id_usuario")) == str(payload.get("sub"))), None)
        if not account:
            raise ValueError("La cuenta de esta sesión ya no existe. Inicia sesión nuevamente.")
        if client:
            self._require_active_client(account)
        return self._profile(account, client=client, google=payload)
