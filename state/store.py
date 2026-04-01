from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from state.factory import DEFAULT_STATE
from state.merge import merge_state


class StateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return merge_state({}, DEFAULT_STATE)
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return merge_state(DEFAULT_STATE, data)

    def save(self, state: dict[str, Any]) -> dict[str, Any]:
        normalized = merge_state(DEFAULT_STATE, state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
        return normalized
