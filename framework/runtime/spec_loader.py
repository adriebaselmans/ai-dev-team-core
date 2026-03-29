from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


CANONICAL_PHASE_SOURCES = {'artifacts', 'state'}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def runtime_dir() -> Path:
    return Path(__file__).resolve().parent


def config_dir() -> Path:
    return repo_root() / 'framework' / 'config'


def schemas_dir() -> Path:
    return repo_root() / 'framework' / 'schemas'


def docs_dir() -> Path:
    return repo_root() / 'docs'


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open('r', encoding='utf-8') as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f'Expected mapping in {path}')
    return data


def load_team_spec() -> dict[str, Any]:
    return load_yaml(runtime_dir() / 'team.yaml')


def load_workflow_spec() -> dict[str, Any]:
    return load_yaml(runtime_dir() / 'workflow.yaml')


def load_models_config() -> dict[str, Any]:
    return load_yaml(config_dir() / 'models.yaml')


def load_context_slices() -> dict[str, Any]:
    return load_yaml(runtime_dir() / 'context_slices.yaml')


def load_artifact_schema(name: str) -> dict[str, Any]:
    return load_yaml(schemas_dir() / f'{name}.schema.yaml')


def role_spec(role: str) -> dict[str, Any]:
    roles = load_team_spec().get('roles', {})
    if role not in roles:
        raise KeyError(f'Unknown role: {role}')
    role_value = roles[role]
    if not isinstance(role_value, dict):
        raise ValueError(f"Expected mapping for role '{role}'.")
    return role_value


def phase_spec(phase: str) -> dict[str, Any]:
    phases = load_workflow_spec().get('phases', {})
    if phase not in phases:
        raise KeyError(f'Unknown phase: {phase}')
    phase_value = phases[phase]
    if not isinstance(phase_value, dict):
        raise ValueError(f"Expected mapping for phase '{phase}'.")
    return phase_value


def phase_canonical_source(phase: str) -> str:
    source = phase_spec(phase).get('canonical_source')
    if source not in CANONICAL_PHASE_SOURCES:
        raise ValueError(f"Phase '{phase}' must declare canonical_source as one of {sorted(CANONICAL_PHASE_SOURCES)}.")
    return str(source)


def transition_spec(trigger: str) -> dict[str, Any]:
    transitions = load_workflow_spec().get('transitions', {})
    if trigger not in transitions:
        raise KeyError(f'Unknown transition trigger: {trigger}')
    transition = transitions[trigger]
    if not isinstance(transition, dict):
        raise ValueError(f"Expected mapping for transition '{trigger}'.")
    return transition


def default_trigger_for_phase(phase: str) -> str | None:
    value = load_workflow_spec().get('default_triggers', {}).get(phase)
    return value if isinstance(value, str) else None
