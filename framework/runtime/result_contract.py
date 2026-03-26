from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class SubagentResult:
    status: str
    changed_artifacts: list[str] = field(default_factory=list)
    summary: str = ""
    blockers: list[str] = field(default_factory=list)
    recommended_next_phase: str | None = None

    @classmethod
    def from_json_text(cls, text: str) -> "SubagentResult":
        data = json.loads(text)
        return cls(
            status=data.get("status", "blocked"),
            changed_artifacts=list(data.get("changed_artifacts", [])),
            summary=data.get("summary", ""),
            blockers=list(data.get("blockers", [])),
            recommended_next_phase=data.get("recommended_next_phase"),
        )
