from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from artifacts import ARTIFACT_FILES
from context_slicer import build_context_slice
from execution import DispatchEnvelope, model_selection_for_role
from skill_loader import load_role_skill_contracts, validate_skill_inputs, validate_skill_outputs
from spec_loader import phase_spec, repo_root


PHASE_OBJECTIVES = {
    'requirements': 'Produce an implementation-ready requirements baseline.',
    'architecture': 'Produce an implementation-safe design for the current requirements baseline.',
    'development': 'Implement the approved design and add supporting unit tests.',
    'review': 'Review the implementation and produce a clear technical review decision.',
    'testing': 'Validate the implementation and produce the current Definition of Done record.',
}

PATH_INPUT_PATTERN = re.compile(r'(?:\.github|doc_templates|framework|src|tests)(?:/[A-Za-z0-9_.-]+)*/?')
SEMANTIC_INPUTS = {
    'user need from the coordinator': lambda role, phase, state, team_spec: bool(state.get('active_feature')),
    'changed implementation': lambda role, phase, state, team_spec: bool(_owned_outputs(role, team_spec['roles'][role], phase)),
    'requirements and design context': lambda role, phase, state, team_spec: all(path in ARTIFACT_FILES.values() for path in (
        'doc_templates/requirements/current.yaml',
        'doc_templates/design/current.yaml',
    )),
    'implementation and existing tests': lambda role, phase, state, team_spec: (repo_root() / 'src').exists() and any(
        (repo_root() / candidate).exists() for candidate in ('tests', 'framework/runtime/tests')
    ),
    'current dod artifact': lambda role, phase, state, team_spec: (repo_root() / ARTIFACT_FILES['dod']).exists(),
    'current workflow phase and next intended phase': lambda role, phase, state, team_spec: bool(state.get('phase')) and bool(state.get('next_action')),
    'phase outcome': lambda role, phase, state, team_spec: bool(state.get('last_completed_phase') or state.get('phase')),
}


def _owned_outputs(role: str, role_spec: dict[str, Any], phase: str | None = None) -> list[str]:
    outputs = list(role_spec.get('writes', []))
    if role_spec.get('read_only'):
        if outputs:
            raise ValueError(f"Read-only role '{role}' cannot declare owned outputs.")
        return []
    if phase is not None:
        phase_outputs = phase_spec(phase).get('artifact')
        if isinstance(phase_outputs, str):
            outputs.append(f'doc_templates/{phase_outputs}/current.yaml')
    return list(dict.fromkeys(outputs))


def _collaboration_contract(phase: str, role_spec: dict[str, Any]) -> dict[str, Any]:
    phase_contract = phase_spec(phase).get('collaboration', {})
    role_contract = role_spec.get('collaboration', {})
    contract: dict[str, Any] = {}
    if 'focus' in role_spec:
        contract['focus'] = role_spec['focus']
    if isinstance(role_contract, dict):
        contract.update(role_contract)
    if isinstance(phase_contract, dict):
        contract.update(phase_contract)
    return contract


def _role_collaboration_contract(role_spec: dict[str, Any]) -> dict[str, Any]:
    contract: dict[str, Any] = {}
    if 'focus' in role_spec:
        contract['focus'] = role_spec['focus']
    role_contract = role_spec.get('collaboration', {})
    if isinstance(role_contract, dict):
        contract.update(role_contract)
    return contract


def build_phase_dispatch_envelope(
    phase: str,
    team_spec: dict[str, Any],
    state: dict[str, Any],
) -> DispatchEnvelope:
    role = phase_spec(phase)['owner']
    role_spec = team_spec['roles'][role]
    contracts = load_role_skill_contracts(role_spec)
    context_slice = build_context_slice(role, state)
    available_inputs = _available_inputs_for_role(role, phase, team_spec, contracts, state)
    messages = validate_skill_inputs(contracts, available_inputs)
    messages.extend(validate_skill_outputs(contracts))
    if messages:
        raise ValueError('; '.join(messages))

    return DispatchEnvelope(
        role=role,
        phase=phase,
        objective=PHASE_OBJECTIVES.get(phase, 'Complete the assigned phase work.'),
        context_slice=context_slice,
        owned_outputs=_owned_outputs(role, role_spec, phase),
        skill_contracts=contracts,
        model_selection=model_selection_for_role(role),
        correlation_id=uuid4().hex,
        collaboration_contract=_collaboration_contract(phase, role_spec),
    )


def build_specialist_payload(role: str, team_spec: dict[str, Any], state: dict[str, Any], objective: str) -> dict[str, Any]:
    role_spec = team_spec['roles'][role]
    contracts = load_role_skill_contracts(role_spec)
    context_slice = build_context_slice(role, state)
    return {
        'role': role,
        'objective': objective,
        'context_slice': context_slice,
        'skill_contracts': contracts,
        'owned_outputs': _owned_outputs(role, role_spec),
        'collaboration_contract': _role_collaboration_contract(role_spec),
    }


def _available_inputs_for_role(
    role: str,
    phase: str,
    team_spec: dict[str, Any],
    contracts: list[dict[str, Any]],
    state: dict[str, Any],
) -> set[str]:
    inputs = set(ARTIFACT_FILES.values())
    inputs.update(_all_declared_write_targets(team_spec))
    inputs.update(_repo_backed_contract_inputs(contracts))
    inputs.update(_semantic_inputs_for_role(role, phase, team_spec, state, contracts))
    return inputs


def _all_declared_write_targets(team_spec: dict[str, Any]) -> set[str]:
    outputs: set[str] = set()
    for role_spec in team_spec.get('roles', {}).values():
        outputs.update(str(path) for path in role_spec.get('writes', []))
    for tool_spec in team_spec.get('shared_tools', {}).values():
        outputs.update(str(path) for path in tool_spec.get('writes', []))
    return outputs


def _repo_backed_contract_inputs(contracts: list[dict[str, Any]]) -> set[str]:
    available: set[str] = set()
    for contract in contracts:
        for required_input in contract.get('required_inputs', []):
            value = str(required_input)
            matched_path = _extract_existing_repo_path(value)
            if matched_path is None:
                continue
            available.add(value)
            available.add(matched_path)
    return available


def _semantic_inputs_for_role(
    role: str,
    phase: str,
    team_spec: dict[str, Any],
    state: dict[str, Any],
    contracts: list[dict[str, Any]],
) -> set[str]:
    available: set[str] = {'state'}
    for contract in contracts:
        for required_input in contract.get('required_inputs', []):
            normalized = str(required_input).strip().lower()
            predicate = SEMANTIC_INPUTS.get(normalized)
            if predicate and predicate(role, phase, state, team_spec):
                available.add(str(required_input))
    return available


def _extract_existing_repo_path(value: str) -> str | None:
    match = PATH_INPUT_PATTERN.search(value)
    if match is None:
        return None
    path_text = match.group(0)
    if (repo_root() / path_text).exists():
        return path_text
    return None
