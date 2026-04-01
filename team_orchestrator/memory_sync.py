from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from framework.runtime.memory_store import append_memory_record, query_memory
from team_orchestrator.project_context import load_project_metadata, memory_enabled, repo_root


class MemorySynchronizer:
    def __init__(
        self,
        root: Path | None = None,
        *,
        record_writer: Callable[..., Path] = append_memory_record,
        record_query: Callable[..., list[dict[str, Any]]] = query_memory,
    ) -> None:
        self.root = root or repo_root()
        self.record_writer = record_writer
        self.record_query = record_query

    def sync(self, state: dict[str, Any], *, role_key: str, step_name: str) -> list[Path]:
        if not memory_enabled(self.root):
            return []
        if role_key == "explorer":
            return self._sync_explorer_fact(state, step_name=step_name)
        if role_key == "architect":
            return self._sync_architecture_decision(state)
        return []

    def _sync_explorer_fact(self, state: dict[str, Any], *, step_name: str) -> list[Path]:
        analysis = state.get("analysis") or {}
        if analysis.get("status") != "ready":
            return []
        repo_path = str((state.get("repository") or {}).get("path") or "").strip()
        if not repo_path:
            return []
        payload = {
            "insights": list(analysis.get("insights", [])),
            "repository_roles": list(analysis.get("repository_roles", [])),
        }
        return self._write_if_changed(
            kind="fact",
            phase=step_name,
            scope="repository",
            subject=repo_path,
            source="explorer",
            tags=["repository-knowledge", "exploration"],
            summary=f"Repository exploration captured for {repo_path}.",
            payload=payload,
        )

    def _sync_architecture_decision(self, state: dict[str, Any]) -> list[Path]:
        design = state.get("design") or {}
        if not design.get("approved_for_build"):
            return []
        subject = str(state.get("input") or "").strip()
        if not subject:
            return []
        payload = {
            "architecture": list(design.get("architecture", [])),
            "non_functional_requirements": list(design.get("non_functional_requirements", [])),
            "work_items": list(design.get("work_items", [])),
        }
        return self._write_if_changed(
            kind="decision",
            phase="architecture",
            scope="project",
            subject=subject,
            source="architect",
            tags=["architecture", "design"],
            summary=f"Architecture baseline accepted for: {subject}",
            payload=payload,
        )

    def _write_if_changed(
        self,
        *,
        kind: str,
        phase: str,
        scope: str,
        subject: str,
        source: str,
        tags: list[str],
        summary: str,
        payload: dict[str, Any],
    ) -> list[Path]:
        previous_entries = self.record_query(
            kind=kind,
            phase=phase,
            scope=scope,
            subject=subject,
            limit=1,
            include_superseded=True,
            active_only=False,
            root=self.root,
        )
        supersedes: str | None = None
        if previous_entries:
            latest = previous_entries[0]
            if latest.get("summary") == summary and latest.get("payload") == payload:
                return []
            supersedes = str(latest.get("entry_id") or "") or None

        record_path = self.record_writer(
            kind=kind,
            phase=phase,
            scope=scope,
            subject=subject,
            source=source,
            confidence="high",
            summary=summary,
            payload=payload,
            tags=tags,
            supersedes=supersedes,
            root=self.root,
        )
        return [record_path]
