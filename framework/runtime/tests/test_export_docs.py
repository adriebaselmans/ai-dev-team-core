from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import artifacts
import export_docs


class ExportDocsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._sandbox_root = Path(__file__).resolve().parents[3] / ".tmp-export-docs-tests"
        shutil.rmtree(self._sandbox_root, ignore_errors=True)
        for path in [
            self._sandbox_root / "doc_templates" / "requirements",
            self._sandbox_root / "doc_templates" / "design",
            self._sandbox_root / "doc_templates" / "review",
            self._sandbox_root / "doc_templates" / "dod",
            self._sandbox_root / "docs" / "requirements",
            self._sandbox_root / "docs" / "design",
            self._sandbox_root / "docs" / "review",
            self._sandbox_root / "docs" / "dod",
            self._sandbox_root / "framework" / "schemas",
        ]:
            path.mkdir(parents=True, exist_ok=True)

        schemas = {
            "requirements": {
                "artifact_type": "requirements",
                "title": "Current Requirements",
                "required_fields": ["status", "title"],
                "field_types": {"status": "string", "title": "string"},
                "summary_fields": ["status", "title"],
                "markdown_sections": [
                    {"heading": "Status", "field": "status"},
                    {"heading": "Title", "field": "title"},
                ],
            },
            "design": {
                "artifact_type": "design",
                "title": "Current Design",
                "required_fields": ["title", "design_goal"],
                "field_types": {"title": "string", "design_goal": "string"},
                "summary_fields": ["title"],
                "markdown_sections": [
                    {"heading": "Title", "field": "title"},
                    {"heading": "Design Goal", "field": "design_goal"},
                ],
            },
            "review": {
                "artifact_type": "review",
                "title": "Current Review",
                "required_fields": ["status", "title"],
                "field_types": {"status": "string", "title": "string"},
                "summary_fields": ["status", "title"],
                "markdown_sections": [
                    {"heading": "Status", "field": "status"},
                    {"heading": "Title", "field": "title"},
                ],
            },
            "dod": {
                "artifact_type": "dod",
                "title": "Current Definition of Done",
                "required_fields": ["status", "title"],
                "field_types": {"status": "string", "title": "string"},
                "summary_fields": ["status", "title"],
                "markdown_sections": [
                    {"heading": "Status", "field": "status"},
                    {"heading": "Title", "field": "title"},
                ],
            },
        }
        for name, schema in schemas.items():
            (self._sandbox_root / "framework" / "schemas" / f"{name}.schema.yaml").write_text(
                yaml.safe_dump(schema, sort_keys=False),
                encoding="utf-8",
            )

        payloads = {
            "requirements": {"status": "Ready.", "title": "Example Requirements"},
            "design": {"title": "Example Design", "design_goal": "Do the thing."},
            "review": {"status": "Approved.", "title": "Example Review"},
            "dod": {"status": "Accepted.", "title": "Example DoD"},
        }
        for name, payload in payloads.items():
            (self._sandbox_root / "doc_templates" / name / "current.yaml").write_text(
                yaml.safe_dump(payload, sort_keys=False),
                encoding="utf-8",
            )

    def tearDown(self) -> None:
        shutil.rmtree(self._sandbox_root, ignore_errors=True)

    def test_export_docs_requires_release_branch(self) -> None:
        with patch.object(export_docs, "current_git_branch", return_value="main"):
            with self.assertRaisesRegex(RuntimeError, "release-only"):
                export_docs.export_all_docs(release_only=True)

    def test_export_docs_writes_generated_docs_on_release_branch(self) -> None:
        with (
            patch.object(artifacts, "repo_root", return_value=self._sandbox_root),
            patch.object(export_docs, "repo_root", return_value=self._sandbox_root),
            patch.object(export_docs, "current_git_branch", return_value="release/0.4"),
        ):
            written = export_docs.export_all_docs(release_only=True)

        self.assertEqual(
            [path.relative_to(self._sandbox_root).as_posix() for path in written],
            [
                "docs/requirements/index.md",
                "docs/design/index.md",
                "docs/review/index.md",
                "docs/dod/index.md",
            ],
        )
        generated = (self._sandbox_root / "docs" / "requirements" / "index.md").read_text(encoding="utf-8")
        self.assertIn("Generated from `doc_templates/requirements/current.yaml`.", generated)


if __name__ == "__main__":
    unittest.main()
