from __future__ import annotations

from pathlib import Path

from artifacts import artifact_summary
from memory_store import append_memory_record


def compact_phase(phase: str, artifact_name: str | None, active_feature: str | None) -> Path | None:
    if artifact_name is None:
        payload = {"feature": active_feature, "phase": phase}
        return append_memory_record(
            kind="phase-brief",
            phase=phase,
            summary=f"Compact brief for {phase}",
            payload=payload,
            tags=["compact"],
        )
    payload = {
        "feature": active_feature,
        "phase": phase,
        "artifact": artifact_name,
        "artifact_summary": artifact_summary(artifact_name),
    }
    return append_memory_record(
        kind="phase-brief",
        phase=phase,
        summary=f"Compact brief for {phase}",
        payload=payload,
        tags=["compact", artifact_name],
        artifact_refs=[f"docs/{artifact_name}/current.yaml"],
    )
