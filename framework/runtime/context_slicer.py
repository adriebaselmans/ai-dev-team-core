from __future__ import annotations

from typing import Any

from artifacts import load_artifact
from memory_store import latest_brief
from spec_loader import load_context_slices


def _select_fields(source: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: source[field] for field in fields if field in source}


def build_context_slice(role: str, state: dict[str, Any]) -> dict[str, Any]:
    slices = load_context_slices().get("slices", {})
    if role not in slices:
        raise KeyError(f"No context slice configured for role '{role}'.")

    config = slices[role]
    result: dict[str, Any] = {}
    if "state" in config:
        result["state"] = _select_fields(state, list(config["state"]))
    for artifact_name in ("requirements", "design", "review", "dod"):
        fields = config.get(artifact_name)
        if fields:
            result[artifact_name] = _select_fields(load_artifact(artifact_name), list(fields))
    if "memory" in config:
        result["memory"] = {}
        if "latest_brief" in config["memory"]:
            result["memory"]["latest_brief"] = latest_brief()
    return result
