"""Adapta los comandos tipados al motor transaccional y a las instantáneas."""
from copy import deepcopy
from domain.services.gym_domain_service import GymDomainService
from domain.services import gym_domain_service as domain_clock
from domain.services.membership_lifecycle import apply_membership_expiration


def query_operation(query, state, passwords):
    snapshot = deepcopy({key: state.get(key, []) for key in query.resources})
    apply_membership_expiration(snapshot, domain_clock._today_iso())
    return deepcopy(query.run(GymDomainService(snapshot, passwords).components))


def command_operation(command, state, passwords):
    # El comando trabaja solo sobre su unidad de datos. Un error no publica cambios
    # parciales en caché y nunca modifica recursos ajenos a su contrato.
    snapshot = {key: deepcopy(state.get(key, [])) for key in command.resources}
    snapshot["_identity_floors"] = deepcopy(state.get("_identity_floors", {}))
    result = deepcopy(command.run(GymDomainService(snapshot, passwords).components))
    state.update({key: snapshot[key] for key in command.resources})
    return result
