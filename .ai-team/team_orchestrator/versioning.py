from __future__ import annotations

import tomllib
from importlib import metadata
from pathlib import Path
from typing import Any

from team_orchestrator.paths import repo_root


def version_file_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "VERSION"


def pyproject_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "pyproject.toml"


def load_version_file(root: Path | None = None) -> str:
    return version_file_path(root).read_text(encoding="utf-8").strip()


def load_pyproject_version(root: Path | None = None) -> str:
    data: dict[str, Any] = tomllib.loads(pyproject_path(root).read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("pyproject.toml is missing project.version")
    return version.strip()


def load_project_version(root: Path | None = None) -> str:
    resolved_root = root or repo_root()
    if not version_file_path(resolved_root).exists() or not pyproject_path(resolved_root).exists():
        return metadata.version("ai-dev-team-core")
    version_file = load_version_file(resolved_root)
    pyproject_version = load_pyproject_version(resolved_root)
    if version_file != pyproject_version:
        raise ValueError(
            f"Version mismatch: VERSION has {version_file!r}, pyproject.toml has {pyproject_version!r}"
        )
    return version_file
