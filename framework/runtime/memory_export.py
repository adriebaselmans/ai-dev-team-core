from __future__ import annotations

from collections.abc import Callable
from typing import Any

from memory_store import query_memory


def render_project_log_snapshot(*, limit: int = 20) -> str:
    entries = query_memory(kind="phase-brief", limit=limit, include_superseded=True, active_only=False)
    return _render_snapshot(
        title="Project Log Snapshot",
        empty_text="No structured phase briefs are available.",
        entries=entries,
        detail_builder=_project_log_details,
    )


def render_decisions_snapshot(*, limit: int = 20) -> str:
    entries = query_memory(kind="decision", scope="project", limit=limit, include_superseded=True, active_only=False)
    return _render_snapshot(
        title="Decisions Snapshot",
        empty_text="No structured decisions are available.",
        entries=entries,
        detail_builder=_decision_details,
    )


def render_known_context_snapshot(*, fact_limit: int = 20, decision_limit: int = 10) -> str:
    fact_entries = query_memory(kind="fact", scope="project", limit=fact_limit)
    decision_entries = query_memory(kind="decision", scope="project", limit=decision_limit)
    lines = ["# Known Context Snapshot", ""]
    lines.extend(_render_section("Active Facts", fact_entries, _known_context_details))
    lines.append("")
    lines.extend(_render_section("Active Decisions", decision_entries, _decision_details))
    return "\n".join(lines).strip() + "\n"


def render_memory_snapshot(view: str, *, limit: int = 20) -> str:
    if view == "project-log":
        return render_project_log_snapshot(limit=limit)
    if view == "decisions":
        return render_decisions_snapshot(limit=limit)
    if view == "known-context":
        return render_known_context_snapshot(fact_limit=limit, decision_limit=max(1, limit // 2))
    raise ValueError(f"Unknown memory snapshot view '{view}'.")


def _render_snapshot(
    *,
    title: str,
    empty_text: str,
    entries: list[dict[str, Any]],
    detail_builder: Callable[[dict[str, Any]], list[str | None]],
) -> str:
    lines = [f"# {title}", ""]
    if not entries:
        lines.append(empty_text)
        return "\n".join(lines).strip() + "\n"
    for entry in entries:
        lines.extend(_render_entry(entry, detail_builder))
    return "\n".join(lines).strip() + "\n"


def _render_section(
    title: str,
    entries: list[dict[str, Any]],
    detail_builder: Callable[[dict[str, Any]], list[str | None]],
) -> list[str]:
    lines = [f"## {title}"]
    if not entries:
        lines.append("- None")
        return lines
    for entry in entries:
        lines.extend(_render_entry(entry, detail_builder))
    return lines


def _render_entry(entry: dict[str, Any], detail_builder: Callable[[dict[str, Any]], list[str | None]]) -> list[str]:
    timestamp = entry.get("timestamp_utc", "unknown-time")
    summary = entry.get("summary", "No summary")
    details = detail_builder(entry)
    lines = [f"- {timestamp}: {summary}"]
    lines.extend(f"  {detail}" for detail in details if detail)
    return lines


def _project_log_details(entry: dict[str, Any]) -> list[str]:
    payload = entry.get("payload", {})
    return [
        f"Phase: {entry.get('phase', 'unknown')}",
        f"Scope: {entry.get('scope', 'project')}",
        _optional_line("Subject", entry.get("subject")),
        _optional_line("Why it changed", payload.get("why_it_changed")),
        _optional_line("Resulting state", payload.get("resulting_state")),
    ]


def _decision_details(entry: dict[str, Any]) -> list[str]:
    payload = entry.get("payload", {})
    return [
        f"Phase: {entry.get('phase', 'unknown')}",
        _optional_line("Subject", entry.get("subject")),
        _optional_line("Decision", payload.get("decision")),
        _optional_line("Context", payload.get("context")),
        _optional_line("Reason", payload.get("reason")),
        _optional_line("Consequence", payload.get("consequence")),
    ]


def _known_context_details(entry: dict[str, Any]) -> list[str]:
    payload = entry.get("payload", {})
    return [
        f"Phase: {entry.get('phase', 'unknown')}",
        _optional_line("Subject", entry.get("subject")),
        _optional_line("Context", payload.get("context")),
        _optional_line("Evidence", payload.get("evidence")),
    ]


def _optional_line(label: str, value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return f"{label}: {text}"
