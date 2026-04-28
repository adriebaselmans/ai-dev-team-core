from __future__ import annotations

import io
import json
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import init  # noqa: E402  (import after sys.path tweak)


@pytest.fixture()
def sandbox_root(tmp_path: Path) -> Path:
    root = tmp_path / "sandbox"
    (root / ".ai-team" / "framework" / "runtime").mkdir(parents=True, exist_ok=True)
    (root / ".ai-team" / "framework" / "roles").mkdir(parents=True, exist_ok=True)
    (root / ".ai-team" / "framework" / "memory").mkdir(parents=True, exist_ok=True)
    (root / ".ai-team" / "context").mkdir(parents=True, exist_ok=True)
    (root / ".ai-team" / "runtime").mkdir(parents=True, exist_ok=True)
    (root / ".ai-team" / "memory").mkdir(parents=True, exist_ok=True)
    (root / ".github" / "skills").mkdir(parents=True, exist_ok=True)
    (root / "phase_artifacts").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    for filename in ("AGENTS.md", "README.md", "CHANGELOG.md"):
        (root / filename).write_text(f"# {filename}\n", encoding="utf-8")
    (root / "VERSION").write_text("1.0.5\n", encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nversion = "1.0.5"\n', encoding="utf-8")
    yield root
    shutil.rmtree(root, ignore_errors=True)


def test_main_seeds_empty_artifacts_from_metadata(sandbox_root: Path) -> None:
    metadata_path = sandbox_root / ".ai-team" / "framework" / "init-metadata.json"

    with (
        patch.object(init, "REPO_ROOT", sandbox_root),
        patch.object(sys, "argv", [
            "init.py",
            "--skip-install",
            "--name",
            "Example Project",
            "--description",
            "Example bootstrap description",
            "--stack",
            "Python 3.12",
        ]),
        patch.object(init, "ensure_python_version"),
        patch.object(init.subprocess, "run") as mocked_run,
    ):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = init.main()

    assert exit_code == 0
    mocked_run.assert_not_called()
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    artifacts = {
        name: yaml.safe_load(
            (sandbox_root / "phase_artifacts" / name / "current.yaml").read_text(encoding="utf-8")
        )
        for name in ("requirements", "design", "review", "dod")
    }

    for name in artifacts:
        artifact_path = sandbox_root / "phase_artifacts" / name / "current.yaml"
        assert not artifact_path.with_suffix(".md").exists()

    assert artifacts["requirements"]["title"] == "Example Project"
    assert "Example bootstrap description" in artifacts["requirements"]["user_need"]
    assert artifacts["design"]["title"] == "Example Project"
    assert artifacts["review"]["title"] == "Example Project"
    assert artifacts["dod"]["title"] == "Example Project"
    assert metadata["artifact_persistence"]
    assert metadata["memory_persistence"]
    assert metadata["docs_export_on_release"]
    output = buffer.getvalue()
    assert "Seeded active artifacts" in output
    assert "Setup complete." in output


def test_validate_version_consistency_rejects_skew(sandbox_root: Path) -> None:
    (sandbox_root / "VERSION").write_text("1.0.5\n", encoding="utf-8")
    (sandbox_root / "pyproject.toml").write_text('[project]\nversion = "9.9.9"\n', encoding="utf-8")

    with patch.object(init, "REPO_ROOT", sandbox_root):
        with pytest.raises(SystemExit) as excinfo:
            init.validate_version_consistency()

    assert "Version mismatch" in str(excinfo.value)
