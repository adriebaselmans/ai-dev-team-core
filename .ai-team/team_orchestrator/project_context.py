from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from team_orchestrator.paths import repo_root


def metadata_path(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / ".ai-team" / "framework" / "init-metadata.json"


def load_project_metadata(root: Path | None = None) -> dict[str, Any] | None:
    path = metadata_path(root)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}.")
    return data


def artifacts_enabled(root: Path | None = None) -> bool:
    metadata = load_project_metadata(root)
    if metadata is None:
        return False
    return bool(metadata.get("artifact_persistence", True))


def memory_enabled(root: Path | None = None) -> bool:
    metadata = load_project_metadata(root)
    if metadata is None:
        return False
    return bool(metadata.get("memory_persistence", metadata.get("artifact_persistence", True)))


def release_docs_enabled(root: Path | None = None) -> bool:
    metadata = load_project_metadata(root)
    if metadata is None:
        return False
    return bool(metadata.get("docs_export_on_release", metadata.get("artifact_persistence", True)))
