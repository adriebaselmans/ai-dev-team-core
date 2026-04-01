from __future__ import annotations

from typing import Any


def resolve_path(state: dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = state
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return default
        current = current[segment]
    return current


def set_path(state: dict[str, Any], path: str, value: Any) -> None:
    current = state
    segments = path.split(".")
    for segment in segments[:-1]:
        nested = current.get(segment)
        if not isinstance(nested, dict):
            nested = {}
            current[segment] = nested
        current = nested
    current[segments[-1]] = value


def evaluate_condition(condition: dict[str, Any], state: dict[str, Any]) -> bool:
    if "all" in condition:
        return all(evaluate_condition(item, state) for item in condition["all"])
    if "any" in condition:
        return any(evaluate_condition(item, state) for item in condition["any"])

    path = condition.get("path")
    if not isinstance(path, str):
        raise ValueError("Condition must declare a string 'path' unless using 'all' or 'any'.")

    value = resolve_path(state, path)
    if "equals" in condition:
        return value == condition["equals"]
    if "not_equals" in condition:
        return value != condition["not_equals"]
    if condition.get("truthy") is True:
        return bool(value)
    if condition.get("falsy") is True:
        return not bool(value)
    if "in" in condition:
        return value in condition["in"]
    if "gte" in condition:
        return value >= condition["gte"]
    if "lte" in condition:
        return value <= condition["lte"]
    raise ValueError(f"Unsupported condition shape: {condition}")
