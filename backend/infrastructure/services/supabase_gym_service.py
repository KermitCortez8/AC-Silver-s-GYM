"""Constructor anterior conservado para consumidores existentes.

La persistencia vive en repositories/gym_repository.py; la API se ensambla en app/bootstrap.py.
"""
import time  # Reexportación para consumidores que personalizaban el reloj del adaptador.

from infrastructure.supabase_client import SupabaseRestClient
from infrastructure.repositories.gym_repository import SupabaseGymRepository
from infrastructure.services.legacy_gym_facade import LegacyGymFacade
from domain.services.gym_domain_service import _today_iso


class SupabaseGymService(LegacyGymFacade):
    repository_type = SupabaseGymRepository

    def __init__(self, supabase_url, supabase_key):
        self.repository = SupabaseGymRepository(supabase_url, supabase_key)
