"""Fachada del puerto GymRepository; delega cada capacidad a su componente."""
from domain.services.gym_domain_service import GymDomainService
from infrastructure.supabase_client import SupabaseRestClient
from infrastructure.repositories.gym_cache import GymCache
from infrastructure.repositories.gym_table_access import TableMetadata
from infrastructure.repositories.gym_repository_components import compose_repository
from infrastructure.repositories.schema_policy import missing_column
from infrastructure.repositories import gym_tables
from infrastructure.repositories.enrollment_errors import raise_schedule_enrollment_error
from infrastructure.repositories.mappers import accounts, attendance, common, configuration, inventory, memberships, schedules, store
from infrastructure.repositories.mappers.registry import to_remote_body


class SupabaseGymRepository:
    REFRESH_TTL_SECONDS = gym_tables.REFRESH_TTL_SECONDS
    PAYMENT_COLUMNS = gym_tables.PAYMENT_COLUMNS
    STORE_PAYMENT_COLUMNS = gym_tables.STORE_PAYMENT_COLUMNS
    CORE_TABLES = gym_tables.CORE_TABLES
    SYNC_STATE_KEYS = gym_tables.SYNC_STATE_KEYS
    READ_STATE_KEYS = gym_tables.READ_STATE_KEYS
    RELATED_READS = gym_tables.RELATED_READS

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = SupabaseRestClient(supabase_url, supabase_key)
        self._validate_payment_schema()
        self._validate_store_payment_schema()

    @property
    def cache(self):
        if "_cache" not in self.__dict__:
            self._cache = GymCache()
        return self._cache

    @property
    def metadata(self):
        if "_metadata" not in self.__dict__:
            self._metadata = TableMetadata()
        return self._metadata

    @property
    def supabase(self):
        return self._database

    @supabase.setter
    def supabase(self, database):
        self._database = database
        self.__dict__.pop("_assembled", None)

    @property
    def components(self):
        if "_assembled" not in self.__dict__:
            self._assembled = compose_repository(self.supabase, self.cache, self.metadata, self.REFRESH_TTL_SECONDS)
        return self._assembled

    def read(self, operation, resources=None):
        return self.cache.read(operation, resources)

    def change(self, operation, resources=None):
        return self.components.writer.change(operation, resources)

    def refresh(self, resources=None):
        self.components.reader.refresh(resources)

    def enroll(self, payload):
        return self.components.enrollments.enroll(payload)

    def save_attendance(self, row, expected_version, audit):
        return self.components.attendance.save_attendance(row, expected_version, audit)

    def save_settings(self, payload):
        return self.components.settings.save_settings(payload)

    def validate_admin_registration_schema(self):
        self.components.tables.validate_admin_registration_schema()

    # Adaptación del contrato antiguo; la API nueva usa las operaciones anteriores.
    @property
    def state(self):
        return self.cache.state

    @state.setter
    def state(self, value):
        self.cache.state = value

    @property
    def lock(self):
        return self.cache.lock

    @lock.setter
    def lock(self, value):
        self.cache.lock = value

    @property
    def _raw_rows(self):
        return self.cache.raw_rows

    @_raw_rows.setter
    def _raw_rows(self, value):
        self.cache.raw_rows = value

    @property
    def _last_refresh_at(self):
        return self.cache.last_refresh_at

    @_last_refresh_at.setter
    def _last_refresh_at(self, value):
        self.cache.last_refresh_at = value

    @property
    def _resource_refreshed_at(self):
        return self.cache.resource_refreshed_at

    @_resource_refreshed_at.setter
    def _resource_refreshed_at(self, value):
        self.cache.resource_refreshed_at = value

    @property
    def remote_columns(self):
        return self.metadata.columns

    @remote_columns.setter
    def remote_columns(self, value):
        self.metadata.columns = value

    @property
    def missing_remote_tables(self):
        return self.metadata.missing_tables

    @missing_remote_tables.setter
    def missing_remote_tables(self, value):
        self.metadata.missing_tables = value

    def _validate_payment_schema(self):
        return self.components.tables.validate_payment_schema()

    def _validate_store_payment_schema(self):
        return self.components.tables.validate_store_payment_schema()

    def _remember_remote_columns(self, table, rows):
        return self.components.tables.remember_columns(table, rows)

    def _select_required(self, table, order=None):
        return self.components.tables.select_required(table, order)

    def _select_optional(self, table, order=None):
        return self.components.tables.select_optional(table, order)

    def _filter_remote_columns(self, table, body):
        return self.components.tables.prepare_write(table, body)

    def _read_resources(self, resources=None):
        return gym_tables.selected_resources(resources)

    def _refresh_remote_state(self, resources=None):
        return self.components.reader.load(resources)

    def _refresh_remote_state_if_stale(self, resources=None):
        return self.components.reader.refresh_if_stale(resources)

    def _mutation_snapshot(self, resources=None):
        return self.components.writer.snapshot(resources)

    def _changed_state_keys(self, previous, current):
        return self.components.writer.changed_keys(previous, current)

    def _mutate(self, operation, resources=None):
        return self.change(operation, resources)

    def _sync_remote_changes(self, previous, current, changed_keys, *legacy_tracking):
        return self.components.planner.commit(previous, current, changed_keys)

    def _guardar_estados_automaticos(self, rows, state):
        return self.components.inventory_status.reconcile(rows, state)

    def configuracion_gimnasio(self):
        return dict(self.cache.state.get("configuracion_gimnasio") or {})

    @property
    def rules(self):
        return GymDomainService(self.cache.state)

    _is_missing_column_error = staticmethod(missing_column)
    _raise_schedule_enrollment_error = staticmethod(raise_schedule_enrollment_error)
    _to_remote_body = staticmethod(to_remote_body)
    _pk = staticmethod(common._pk)
    _remote_pk_value = staticmethod(common._remote_pk_value)
    _remote_user_id = staticmethod(common._remote_user_id)
    _remote_user_id_or_none = staticmethod(common._remote_user_id_or_none)
    _split_name = staticmethod(common._split_name)
    _phone_number = staticmethod(common._phone_number)
    _status_to_bool = staticmethod(common._status_to_bool)
    _bool_to_status = staticmethod(common._bool_to_status)
    _date_or_today = staticmethod(common._date_or_today)
    _date_or_none = staticmethod(common._date_or_none)
    _map_config = staticmethod(configuration._map_config)
    _config_to_remote = staticmethod(configuration._config_to_remote)
    _map_plan = staticmethod(memberships._map_plan)
    _plan_to_remote = staticmethod(memberships._plan_to_remote)
    _map_promotion = staticmethod(memberships._map_promotion)
    _promotion_to_remote = staticmethod(memberships._promotion_to_remote)
    _map_membership = staticmethod(memberships._map_membership)
    _membership_to_remote = staticmethod(memberships._membership_to_remote)
    _map_client = staticmethod(accounts._map_client)
    _client_to_remote = staticmethod(accounts._client_to_remote)
    _map_user = staticmethod(accounts._map_user)
    _map_user_legacy = staticmethod(accounts._map_user_legacy)
    _user_to_remote = staticmethod(accounts._user_to_remote)
    _map_inventory = staticmethod(inventory._map_inventory)
    _inventory_to_remote = staticmethod(inventory._inventory_to_remote)
    _map_inventory_move = staticmethod(inventory._map_inventory_move)
    _inventory_move_to_remote = staticmethod(inventory._inventory_move_to_remote)
    _map_product = staticmethod(inventory._map_product)
    _product_to_remote = staticmethod(inventory._product_to_remote)
    _map_sale_detail = staticmethod(store._map_sale_detail)
    _map_sale = staticmethod(store._map_sale)
    _sale_to_remote = staticmethod(store._sale_to_remote)
    _sale_detail_to_remote = staticmethod(store._sale_detail_to_remote)
    _map_routine = staticmethod(schedules._map_routine)
    _routine_to_remote = staticmethod(schedules._routine_to_remote)
    _map_schedule = staticmethod(schedules._map_schedule)
    _schedule_to_remote = staticmethod(schedules._schedule_to_remote)
    _map_service_schedule = staticmethod(schedules._map_service_schedule)
    _service_schedule_to_remote = staticmethod(schedules._service_schedule_to_remote)
    _map_schedule_enrollment = staticmethod(schedules._map_schedule_enrollment)
    _schedule_enrollment_to_remote = staticmethod(schedules._schedule_enrollment_to_remote)
    _map_routine_progress = staticmethod(schedules._map_routine_progress)
    _routine_progress_to_remote = staticmethod(schedules._routine_progress_to_remote)
    _map_ticket = staticmethod(schedules._map_ticket)
    _ticket_to_remote = staticmethod(schedules._ticket_to_remote)
    _map_attendance = staticmethod(attendance._map_attendance)
    _attendance_to_remote = staticmethod(attendance._attendance_to_remote)
