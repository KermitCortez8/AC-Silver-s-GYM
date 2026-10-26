"""Compatibilidad para integraciones antiguas que inspeccionaban el estado interno.

La API nueva utiliza GymService y sus contratos públicos. Esta fachada conserva
los constructores anteriores mediante composición, sin heredar reglas de negocio.
"""
from application.services.gym_service import GymService
from infrastructure.services.stripe_service import StripeService
from infrastructure.authentication import PasswordService, GoogleIdentityProvider, SignedSessionProvider


class LegacyGymFacade(GymService):
    passwords = PasswordService()
    identity = GoogleIdentityProvider()
    sessions = SignedSessionProvider()
    gateway_factory = StripeService

    @property
    def repository(self):
        if "_repository" not in self.__dict__:
            self.__dict__["_repository"] = object.__new__(self.repository_type)
        return self.__dict__["_repository"]

    @repository.setter
    def repository(self, value):
        self.__dict__["_repository"] = value

    def __getattr__(self, name):
        repository = self.repository
        try:
            return getattr(repository, name)
        except AttributeError:
            return getattr(self._rules(getattr(repository, "state", {})), name)

    def __setattr__(self, name, value):
        if name in {"repository", "_repository", "passwords", "identity", "sessions", "gateway_factory"}:
            object.__setattr__(self, name, value)
        else:
            setattr(self.repository, name, value)
