from __future__ import annotations

import io
import json
import shutil
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import init


class InitScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._sandbox_root = Path(__file__).resolve().parents[2] / ".tmp-init-tests"
        shutil.rmtree(self._sandbox_root, ignore_errors=True)
        (self._sandbox_root / ".ai-team" / "framework" / "runtime").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / ".ai-team" / "framework" / "roles").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / ".ai-team" / "framework" / "memory").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / ".ai-team" / "context").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / ".ai-team" / "runtime").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / ".github" / "skills").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / "phase_artifacts").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / "docs").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / "src").mkdir(parents=True, exist_ok=True)
        for filename in ["AGENTS.md", "README.md", "CHANGELOG.md"]:
            (self._sandbox_root / filename).write_text(f"# {filename}\n", encoding="utf-8")
        (self._sandbox_root / "VERSION").write_text("1.0.5\n", encoding="utf-8")
        (self._sandbox_root / "pyproject.toml").write_text('[project]\nversion = "1.0.5"\n', encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self._sandbox_root, ignore_errors=True)

    def test_main_seeds_empty_artifacts_from_metadata(self) -> None:
        metadata_path = self._sandbox_root / ".ai-team" / "framework" / "init-metadata.json"

        with (
            patch.object(init, "REPO_ROOT", self._sandbox_root),
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

        self.assertEqual(exit_code, 0)
        mocked_run.assert_not_called()
        self.assertTrue(metadata_path.exists())
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        requirements = yaml.safe_load((self._sandbox_root / "phase_artifacts" / "requirements" / "current.yaml").read_text(encoding="utf-8"))
        design = yaml.safe_load((self._sandbox_root / "phase_artifacts" / "design" / "current.yaml").read_text(encoding="utf-8"))
        review = yaml.safe_load((self._sandbox_root / "phase_artifacts" / "review" / "current.yaml").read_text(encoding="utf-8"))
        dod = yaml.safe_load((self._sandbox_root / "phase_artifacts" / "dod" / "current.yaml").read_text(encoding="utf-8"))
        self.assertFalse((self._sandbox_root / "phase_artifacts" / "requirements" / "current.yaml").with_suffix(".md").exists())
        self.assertFalse((self._sandbox_root / "phase_artifacts" / "design" / "current.yaml").with_suffix(".md").exists())
        self.assertFalse((self._sandbox_root / "phase_artifacts" / "review" / "current.yaml").with_suffix(".md").exists())
        self.assertFalse((self._sandbox_root / "phase_artifacts" / "dod" / "current.yaml").with_suffix(".md").exists())

        self.assertEqual(requirements["title"], "Example Project")
        self.assertIn("Example bootstrap description", requirements["user_need"])
        self.assertEqual(design["title"], "Example Project")
        self.assertEqual(review["title"], "Example Project")
        self.assertEqual(dod["title"], "Example Project")
        self.assertTrue(metadata["artifact_persistence"])
        self.assertTrue(metadata["memory_persistence"])
        self.assertTrue(metadata["docs_export_on_release"])
        self.assertIn("Seeded active artifacts", buffer.getvalue())
        self.assertIn("Setup complete.", buffer.getvalue())

    def test_validate_version_consistency_rejects_skew(self) -> None:
        (self._sandbox_root / "VERSION").write_text("1.0.5\n", encoding="utf-8")
        (self._sandbox_root / "pyproject.toml").write_text('[project]\nversion = "9.9.9"\n', encoding="utf-8")

        with patch.object(init, "REPO_ROOT", self._sandbox_root):
            with self.assertRaises(SystemExit) as raised:
                init.validate_version_consistency()

        self.assertIn("Version mismatch", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
