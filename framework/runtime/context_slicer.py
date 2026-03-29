from __future__ import annotations

from typing import Any

from artifacts import load_artifact
from memory_store import latest_brief
from spec_loader import load_context_slices, phase_canonical_source


ARTIFACT_SLICE_NAMES = ('requirements', 'design', 'review', 'dod')


def _select_fields(source: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: source[field] for field in fields if field in source}


def build_context_slice(role: str, state: dict[str, Any]) -> dict[str, Any]:
    slices = load_context_slices().get('slices', {})
    if role not in slices:
        raise KeyError(f"No context slice configured for role '{role}'.")

    config = slices[role]
    phase = str(state.get('phase', 'idle'))
    canonical_source = phase_canonical_source(phase)
    result: dict[str, Any] = {'canonical_phase_source': canonical_source}
    if 'state' in config:
        result['state'] = _select_fields(state, list(config['state']))

    artifact_fields = [artifact_name for artifact_name in ARTIFACT_SLICE_NAMES if config.get(artifact_name)]
    if canonical_source == 'state' and artifact_fields:
        raise ValueError(
            f"Role '{role}' requests artifact slices {artifact_fields} during state-canonical phase '{phase}'."
        )

    for artifact_name in artifact_fields:
        result[artifact_name] = _select_fields(load_artifact(artifact_name), list(config[artifact_name]))

    if 'memory' in config:
        result['memory'] = {}
        if 'latest_brief' in config['memory']:
            result['memory']['latest_brief'] = latest_brief()
    return result
