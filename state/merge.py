from __future__ import annotations

from copy import deepcopy
from typing import Any


def merge_state(current: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(current)
    for key, value in updates.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_state(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged
