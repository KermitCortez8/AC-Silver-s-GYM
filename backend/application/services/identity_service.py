"""Consulta de identidad sin depender de la base de datos del gimnasio."""
from application.ports.integrations import IdentityProvider, SessionProvider


class IdentityService:
    def __init__(self, identity: IdentityProvider, sessions: SessionProvider):
        self.identity = identity
        self.sessions = sessions

    def profile(self, credential):
        return self.sessions.normalize(self.identity.verify(credential), "")
