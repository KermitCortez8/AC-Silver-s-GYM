"""Composición de reglas mediante capacidades concretas; sin herencia múltiple."""
from dataclasses import dataclass
from domain.services.rule_context import RuleContext
from domain.services.accounts_rules import AccountsRules, AccountsDependencies
from domain.services.store_rules import StoreRules, StoreDependencies
from domain.services.schedules_rules import SchedulesRules, SchedulesDependencies
from domain.services.inventory_rules import InventoryRules, InventoryDependencies
from domain.services.memberships_rules import MembershipsRules, MembershipsDependencies
from domain.services.dashboard_rules import DashboardRules, DashboardDependencies
from domain.services.attendance_rules import AttendanceRules, AttendanceDependencies

@dataclass(frozen=True)
class DomainComponents:
    context: RuleContext
    accounts: AccountsRules
    store: StoreRules
    schedules: SchedulesRules
    inventory: InventoryRules
    memberships: MembershipsRules
    dashboard: DashboardRules
    attendance: AttendanceRules

def compose_domain(context):
    accounts = AccountsRules(context, AccountsDependencies(ensure_membership_for_active_client=lambda *args, **kwargs: memberships._ensure_membership_for_active_client(*args, **kwargs), parse_cliente_id=lambda *args, **kwargs: attendance._parse_cliente_id(*args, **kwargs)))
    memberships = MembershipsRules(context, MembershipsDependencies(get_account_by_google_sub=accounts.get_account_by_google_sub, get_cliente=accounts.get_cliente, get_cliente_by_dni=accounts.get_cliente_by_dni, get_cliente_by_email=accounts.get_cliente_by_email, get_usuario_by_email=accounts.get_usuario_by_email, upsert_cliente=accounts.upsert_cliente))
    inventory = InventoryRules(context, InventoryDependencies(normalize_usuario_id=accounts._normalize_usuario_id, get_usuario=accounts.get_usuario))
    store = StoreRules(context, StoreDependencies(actualizar_estados_tienda=inventory._actualizar_estados_tienda, es_item_tienda=inventory._es_item_tienda, find_item_in_state=inventory._find_item_in_state, next_n_activo=inventory._next_n_activo))
    schedules = SchedulesRules(context, SchedulesDependencies(active_membership_for_cliente=memberships._active_membership_for_cliente, normalize_usuario_id=accounts._normalize_usuario_id, parse_cliente_id=lambda *args, **kwargs: attendance._parse_cliente_id(*args, **kwargs), get_cliente=accounts.get_cliente, get_cliente_by_dni=accounts.get_cliente_by_dni, get_usuario=accounts.get_usuario))
    attendance = AttendanceRules(context, AttendanceDependencies(active_membership_for_cliente=memberships._active_membership_for_cliente, normalize_usuario_id=accounts._normalize_usuario_id, validate_service_schedule=schedules._validate_service_schedule, get_cliente=accounts.get_cliente, get_cliente_by_dni=accounts.get_cliente_by_dni))
    dashboard = DashboardRules(context, DashboardDependencies(configuracion_gimnasio=schedules.configuracion_gimnasio))
    return DomainComponents(context, accounts, store, schedules, inventory, memberships, dashboard, attendance)
