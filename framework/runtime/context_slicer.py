from __future__ import annotations

from typing import Any

from artifacts import load_artifact
from memory_store import query_memory
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
        result['memory'] = _build_memory_slice(config['memory'])
    return result


def _build_memory_slice(memory_config: Any) -> dict[str, Any]:
    if isinstance(memory_config, dict):
        return {name: _query_memory_recipe(name, recipe) for name, recipe in memory_config.items()}
    if isinstance(memory_config, list):
        return {str(index): _query_memory_recipe(str(index), recipe) for index, recipe in enumerate(memory_config)}
    raise TypeError("Memory slice configuration must be a mapping or a list.")


def _query_memory_recipe(name: str, recipe: Any) -> Any:
    if isinstance(recipe, str):
        selector: dict[str, Any] = {'kind': recipe}
        limit = 10
        single = False
    elif isinstance(recipe, dict):
        selector = dict(recipe)
        limit = int(selector.pop('limit', 10))
        single = bool(selector.pop('single', False))
    else:
        raise TypeError(f"Memory recipe '{name}' must be a string or mapping.")

    entries = query_memory(limit=limit, **selector)
    if single:
        return entries[0] if entries else None
    return entries
