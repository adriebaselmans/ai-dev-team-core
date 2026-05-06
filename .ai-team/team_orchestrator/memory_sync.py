from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from framework.runtime.memory_store import query_wiki, write_repository_wiki, write_wiki_page
from team_orchestrator.project_context import load_project_metadata, memory_enabled, repo_root


class MemorySynchronizer:
    def __init__(
        self,
        root: Path | None = None,
        *,
        page_writer: Callable[..., Path] = write_wiki_page,
        page_query: Callable[..., list[dict[str, Any]]] = query_wiki,
    ) -> None:
        self.root = root or repo_root()
        self.page_writer = page_writer
        self.page_query = page_query

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
        return write_repository_wiki(
            repo_path=repo_path,
            phase=step_name,
            summary=f"Repository exploration captured for {repo_path}.",
            insights=list(analysis.get("insights", [])),
            repository_roles=list(analysis.get("repository_roles", [])),
            categorized_findings={
                "architecture": list(analysis.get("architecture", [])),
                "conventions": list(analysis.get("conventions", [])),
                "context": list(analysis.get("context", [])),
                "decisions": list(analysis.get("decisions", [])),
                "incidents": list(analysis.get("incidents", [])),
            },
            source="explorer",
            root=self.root,
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
        subject: str,
        source: str,
        tags: list[str],
        summary: str,
        payload: dict[str, Any],
    ) -> list[Path]:
        # Check if wiki already has an equivalent page
        existing = self.page_query(
            tags=[kind, phase] if phase else [kind],
            limit=5,
            root=self.root,
        )
        for page in existing:
            if page.get("summary") == summary:
                return []

        page_path = self.page_writer(
            kind=kind,
            phase=phase,
            summary=summary,
            payload=payload,
            tags=tags,
            subject=subject,
            source=source,
            root=self.root,
        )
        return [page_path]
