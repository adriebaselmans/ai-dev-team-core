from __future__ import annotations

import io
import json
import shutil
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import init


class InitScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._sandbox_root = Path(__file__).resolve().parents[1] / ".tmp-init-tests"
        shutil.rmtree(self._sandbox_root, ignore_errors=True)
        (self._sandbox_root / "framework" / "runtime").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / "framework" / "roles").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / "framework" / "memory").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / ".github" / "skills").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / "docs").mkdir(parents=True, exist_ok=True)
        (self._sandbox_root / "src").mkdir(parents=True, exist_ok=True)
        for filename in ["AGENTS.md", "README.md", "CHANGELOG.md"]:
            (self._sandbox_root / filename).write_text(f"# {filename}\n", encoding="utf-8")
        for artifact in [
            ("docs/requirements/current.yaml", ""),
            ("docs/requirements/current.md", ""),
            ("docs/design/current.yaml", ""),
            ("docs/design/current.md", ""),
            ("docs/review/current.yaml", ""),
            ("docs/review/current.md", ""),
            ("docs/dod/current.yaml", ""),
            ("docs/dod/current.md", ""),
        ]:
            path = self._sandbox_root / artifact[0]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(artifact[1], encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self._sandbox_root, ignore_errors=True)

    def test_main_seeds_empty_artifacts_from_metadata(self) -> None:
        metadata_path = self._sandbox_root / "framework" / "init-metadata.json"

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
            patch.object(init.subprocess, "run") as mocked_run,
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = init.main()

        self.assertEqual(exit_code, 0)
        mocked_run.assert_not_called()
        self.assertTrue(metadata_path.exists())

        requirements = json.loads((self._sandbox_root / "docs" / "requirements" / "current.yaml").read_text(encoding="utf-8"))
        design = json.loads((self._sandbox_root / "docs" / "design" / "current.yaml").read_text(encoding="utf-8"))
        review = json.loads((self._sandbox_root / "docs" / "review" / "current.yaml").read_text(encoding="utf-8"))
        dod = json.loads((self._sandbox_root / "docs" / "dod" / "current.yaml").read_text(encoding="utf-8"))
        requirements_md = (self._sandbox_root / "docs" / "requirements" / "current.md").read_text(encoding="utf-8")
        design_md = (self._sandbox_root / "docs" / "design" / "current.md").read_text(encoding="utf-8")

        self.assertEqual(requirements["title"], "Example Project")
        self.assertIn("Example bootstrap description", requirements["user_need"])
        self.assertEqual(design["title"], "Example Project")
        self.assertEqual(review["title"], "Example Project")
        self.assertEqual(dod["title"], "Example Project")
        self.assertIn("Current Requirements", requirements_md)
        self.assertIn("Example Project", design_md)
        self.assertIn("Seeded active artifacts", buffer.getvalue())
        self.assertIn("Setup complete.", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
