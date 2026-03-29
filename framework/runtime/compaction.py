from __future__ import annotations

from pathlib import Path

from artifacts import artifact_summary
from memory_store import append_memory_record, latest_brief


def compact_phase(phase: str, artifact_name: str | None, active_feature: str | None) -> Path | None:
    subject = active_feature or phase
    supersedes = _previous_phase_brief_id(phase, subject)
    if artifact_name is None:
        payload = {
            "feature": active_feature,
            "phase": phase,
            "why_it_changed": f"Phase '{phase}' completed and a compact brief was captured.",
            "resulting_state": "Structured memory record stored locally.",
        }
        return append_memory_record(
            kind="phase-brief",
            phase=phase,
            scope="phase",
            subject=subject,
            source="compaction",
            confidence="high",
            summary=f"Compact brief for {phase}",
            payload=payload,
            tags=["compact"],
            supersedes=supersedes,
        )
    payload = {
        "feature": active_feature,
        "phase": phase,
        "artifact": artifact_name,
        "artifact_summary": artifact_summary(artifact_name),
        "why_it_changed": f"Phase '{phase}' completed and a compact brief was captured.",
        "resulting_state": f"Structured memory record stored for {artifact_name}.",
    }
    return append_memory_record(
        kind="phase-brief",
        phase=phase,
        scope="phase",
        subject=subject,
        source="compaction",
        confidence="high",
        summary=f"Compact brief for {phase}",
        payload=payload,
        tags=["compact", artifact_name],
        artifact_refs=[f"doc_templates/{artifact_name}/current.yaml"],
        supersedes=supersedes,
    )


def _previous_phase_brief_id(phase: str, subject: str) -> str | None:
    existing = latest_brief(phase=phase, subject=subject, scope="phase")
    if existing is None:
        return None
    return existing["entry_id"]
