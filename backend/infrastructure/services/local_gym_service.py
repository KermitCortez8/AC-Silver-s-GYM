"""Constructor local compatible, compuesto con el repositorio en memoria."""
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from infrastructure.services.legacy_gym_facade import LegacyGymFacade


class LocalGymService(LegacyGymFacade):
    repository_type = MemoryGymRepository

    def __init__(self):
        self.repository = MemoryGymRepository()
        self.repository.state = self._rules(self.repository.state).normalize()
