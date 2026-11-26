"""Adaptadores de las capacidades de autenticación."""
import hashlib
import hmac
import json
import time

import jwt

from infrastructure import security
from infrastructure.services import google_auth_service


class PasswordService:
    def hash(self, password):
        return security.hash_password(password)

    def verify(self, password, encoded):
        return security.verify_password(password, encoded)


class GoogleIdentityProvider:
    def verify(self, credential):
        return google_auth_service.verify_google_credential(credential)


class SignedSessionProvider:
    def validate_configuration(self):
        security.get_auth_secret()

    def issue(self, profile):
        return security.create_local_token(profile)

    def normalize(self, profile, token=""):
        return security.normalize_profile(profile, token)


class SignedPasswordRecoveryTokens:
    _issuer = "ac-silvers-gym"
    _audience = "gym-password-recovery"

    def __init__(self, secret: str):
        if len(secret.encode()) < 32:
            raise RuntimeError("Configura AUTH_SECRET_KEY para habilitar la recuperación.")
        self._secret = secret

    def _stamp(self, state: tuple[str, ...]) -> str:
        data = json.dumps(state, ensure_ascii=False, separators=(",", ":")).encode()
        return hmac.new(self._secret.encode(), b"password-recovery:v1:" + data, hashlib.sha256).hexdigest()

    def issue(self, account_id: str, client: bool, state: tuple[str, ...]) -> str:
        # Una solicitud repetida en la misma ventana conserva el enlace y la clave de envío.
        issued_at = int(time.time()) // 600 * 600
        payload = {
            "iss": self._issuer, "aud": self._audience, "sub": account_id, "client": client,
            "stamp": self._stamp(state), "iat": issued_at, "exp": issued_at + 1200,
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def read(self, token: str) -> dict | None:
        try:
            claims = jwt.decode(
                token, self._secret, algorithms=["HS256"], issuer=self._issuer,
                audience=self._audience,
                options={"require": ["exp", "iat", "iss", "aud", "sub", "client", "stamp"]},
            )
        except jwt.InvalidTokenError:
            return None
        if type(claims["client"]) is bool and isinstance(claims["stamp"], str) and claims["sub"]:
            return claims
        return None

    def matches(self, stamp: str, state: tuple[str, ...]) -> bool:
        return hmac.compare_digest(stamp, self._stamp(state))
