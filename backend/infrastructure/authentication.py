"""Adaptadores de las capacidades de autenticación."""
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
