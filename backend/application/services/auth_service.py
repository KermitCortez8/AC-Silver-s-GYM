"""Autentica cuentas existentes y emite sesiones firmadas del gimnasio."""
from __future__ import annotations

import time

from domain.models.auth import AuthGoogleRequest, AuthPasswordRequest, AuthResponse, MembershipProfile, UpdateProfileRequest, UserProfile
from application.services.gym_service import GymService
from domain.services.gym_domain_service import _today_iso
from domain.services.membership_lifecycle import membership_current, membership_expired
from domain.services.accounts_rules import internal_account_active
from application.operations.accounts import UpdateOwnProfileCommand


class GoogleLinkRequired(ValueError):
    pass


class ClientActivationRequired(ValueError):
    code = "account_pending_activation"

    def __init__(self) -> None:
        super().__init__(
            "Tu cuenta aún no está activa. Debe ser activada por el administrador para poder ingresar."
        )


class ClientMembershipExpired(ClientActivationRequired):
    code = "membership_expired"

    def __init__(self) -> None:
        ValueError.__init__(
            self, "Tu membresía está vencida y tu cuenta está bloqueada. Contacta con administración para renovarla."
        )


class ClientMembershipRequired(ClientActivationRequired):
    code = "membership_required"

    def __init__(self) -> None:
        ValueError.__init__(
            self, "Tu cuenta necesita una membresía activa, pagada y vigente. Contacta con administración."
        )


class AuthService:
    def __init__(self, gym_service: GymService) -> None:
        self.gym_service = gym_service
        self.identity = gym_service.identity
        self.sessions = gym_service.sessions
        self.passwords = gym_service.passwords

    def _profile(self, account: dict, *, client: bool, google: dict | None = None) -> UserProfile:
        profile = self.sessions.normalize(google or {}, "")
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
            estado="ACTIVO" if internal_account_active(account) else "INACTIVO",
            fecha_registro=str(account.get("fecha_registro") or "") if client else "",
            google_vinculado=bool(account.get("google_sub")),
            tiene_contrasena=bool(account.get("password_hash")),
        )
        return UserProfile(**profile)

    def _require_active_client(self, client: dict | None) -> dict:
        self.gym_service.ensure_fresh(resources=("clientes", "membresia"))
        if client:
            client = self.gym_service.get_cliente(int(client["id_cliente"]))
        memberships = [
            row
            for row in (self.gym_service.membresias_por_cliente(int(client["id_cliente"])) if client else [])
            if client and int(row.get("id_cliente") or 0) == int(client["id_cliente"])
        ]
        today = _today_iso()
        current = max(
            (row for row in memberships if membership_current(row, today)),
            key=lambda row: (str(row["fecha_fin"]), int(row.get("id_membresia") or 0)),
            default=None,
        )
        if current is None and (any(membership_expired(row, today) for row in memberships)
                                or (client and str(client.get("estado") or "").strip().upper() == "VENCIDA")):
            raise ClientMembershipExpired()
        # CLIENTES.Estado se habilita en la activación administrativa, no al pagar.
        if not client or str(client.get("estado") or "").strip().upper() not in {"ACTIVO", "ACTIVA"}:
            raise ClientActivationRequired()
        if current is None:
            raise ClientMembershipRequired()
        return current

    @staticmethod
    def _membership_profile(client: dict, current: dict) -> MembershipProfile:
        return MembershipProfile(
            plan=str(client.get("plan") or ""),
            fecha_inicio=str(current["fecha_inicio"]),
            fecha_fin=str(current["fecha_fin"]),
            estado_pago=str(current["estado_pago"]).strip().upper(),
        )

    def session_for_user(self, user: UserProfile) -> AuthResponse:
        if user.id_cliente is not None:
            account = self.gym_service.get_cliente(user.id_cliente)
            current = self._require_active_client(account)
            user.membresia = self._membership_profile(account, current)
        else:
            self._require_active_internal(self.gym_service.get_usuario(user.id_usuario or user.id))
        return AuthResponse(user=user, token=self.sessions.issue(user.model_dump()), expiresIn=3600)

    @staticmethod
    def _require_active_internal(account: dict | None) -> None:
        if not internal_account_active(account):
            raise ValueError("La cuenta está inactiva. Contacta con administración.")

    def session_for_client(self, client: dict, google: dict | None = None) -> AuthResponse:
        return self.session_for_user(self._profile(client, client=True, google=google))

    def google_auth(self, payload: AuthGoogleRequest) -> AuthResponse:
        claims = self.identity.verify(payload.credential)
        self.sessions.validate_configuration()  # Valida configuración antes de persistir una vinculación.
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
        if not self.passwords.verify(payload.password, str(account.get("password_hash") or "")):
            raise GoogleLinkRequired("La contraseña del gimnasio es incorrecta. Inténtalo nuevamente.")
        if kind == "clientes":
            self._require_active_client(account)
        else:
            self._require_active_internal(account)
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
        account = self.gym_service.account_for_session(payload.get("sub"), client=client)
        if not account:
            raise ValueError("La cuenta de esta sesión ya no existe. Inicia sesión nuevamente.")
        membership = None
        if client:
            membership = self._membership_profile(account, self._require_active_client(account))
        else:
            self._require_active_internal(account)
        profile = self._profile(account, client=client, google=payload)
        profile.membresia = membership
        return profile

    def update_profile(self, user: UserProfile, payload: UpdateProfileRequest) -> UserProfile:
        changes = payload.model_dump(exclude_unset=True, exclude={"password_actual", "google_credential"})
        if "password_nueva" in changes:
            changes["password_nueva"] = payload.password_nueva.get_secret_value()

        sensitive = bool(changes.keys() & {"correo", "dni", "password_nueva"})
        password_actual = payload.password_actual.get_secret_value()
        credential = payload.google_credential.get_secret_value()

        google_subject = ""
        if sensitive and credential and user.google_vinculado and not user.tiene_contrasena:
            claims = self.identity.verify(credential)
            issued_at = claims.get("iat")
            if not isinstance(issued_at, int) or not 0 <= time.time() - issued_at <= 300:
                raise PermissionError("Vuelve a confirmar tu cuenta de Google para guardar los cambios.")
            google_subject = str(claims["sub"])

        account = self.gym_service.executor.execute(UpdateOwnProfileCommand(
            user.id_usuario or user.id, user.id_cliente, changes,
            verify_credentials=bool(password_actual or credential),
            password_actual=password_actual, google_subject=google_subject,
        ))
        profile = self._profile(account, client=user.id_cliente is not None, google=user.model_dump())
        profile.membresia = user.membresia
        return profile
