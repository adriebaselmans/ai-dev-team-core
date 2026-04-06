from __future__ import annotations

from pathlib import Path

import yaml


def test_bootstrap_manifest_references_existing_project_runtime_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest_path = root / ".ai-team" / "framework" / "runtime" / "bootstrap-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    include_paths = manifest.get("include_paths", [])
    assert isinstance(include_paths, list)
    assert include_paths

    for relative_path in include_paths:
        assert isinstance(relative_path, str)
        cleaned = relative_path.rstrip("/\\")
        assert (root / cleaned).exists(), f"Bootstrap include path is missing: {relative_path}"


def test_bootstrap_manifest_excludes_framework_source_runtime_dirs() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest_path = root / ".ai-team" / "framework" / "runtime" / "bootstrap-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    include_paths = {str(path).rstrip("/\\") for path in manifest.get("include_paths", [])}

    assert ".ai-team/agents" not in include_paths
    assert ".ai-team/team_orchestrator" not in include_paths
    assert ".ai-team/state" not in include_paths
    assert ".ai-team/tests" not in include_paths
