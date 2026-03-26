from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validators


BRIEF_TEXT = """# Example

## Repository Identity
- Name: example
- Source: C:/tmp/example
- Revision: abc123
- Last Updated: 2026-03-26

## Purpose
- Example purpose

## Stack and Tooling
- Python

## Top-Level Architecture
- Service plus CLI

## Key Directories and Entry Points
- src/

## Important Flows for Current Work
- Request path

## Conventions and Constraints
- Keep modules small

## Build, Test, and Run Commands
- python -m unittest

## Risks and Extension Points
- Extension point here

## Open Questions
- None
"""


class RepositoryKnowledgeValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._sandbox_root = Path(__file__).resolve().parents[3] / ".tmp-runtime-tests"
        shutil.rmtree(self._sandbox_root, ignore_errors=True)
        self._sandbox_root.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self._sandbox_root, ignore_errors=True)

    def _write_store(self, root: Path, *, include_repo: bool = False, valid_facts: bool = True) -> None:
        store = root / "framework" / "memory" / "repository-knowledge"
        store.mkdir(parents=True, exist_ok=True)
        (store / "README.md").write_text("# Store\n", encoding="utf-8")
        (store / "TEMPLATE.md").write_text("# Template\n", encoding="utf-8")
        (store / "index.md").write_text("# Repository Knowledge Index\n\n## Entries\n- example\n", encoding="utf-8")
        if include_repo:
            repo_dir = store / "example"
            repo_dir.mkdir()
            (repo_dir / "brief.md").write_text(BRIEF_TEXT, encoding="utf-8")
            facts = {
                "name": "example",
                "source": "C:/tmp/example",
                "last_updated": "2026-03-26",
                "open_questions": [],
            }
            if not valid_facts:
                facts = {"name": "example"}
            (repo_dir / "facts.json").write_text(json.dumps(facts), encoding="utf-8")

    def test_repository_knowledge_store_accepts_empty_initialized_store(self) -> None:
        root = self._sandbox_root / "case-empty"
        self._write_store(root, include_repo=False)
        with patch.object(validators, "repo_root", return_value=root):
            result = validators.validate_repository_knowledge_store()

        self.assertTrue(result.valid)
        self.assertEqual(result.messages, ["Repository knowledge store is valid."])

    def test_repository_knowledge_store_rejects_invalid_facts(self) -> None:
        root = self._sandbox_root / "case-invalid"
        self._write_store(root, include_repo=True, valid_facts=False)
        with patch.object(validators, "repo_root", return_value=root):
            result = validators.validate_repository_knowledge_store()

        self.assertFalse(result.valid)
        self.assertIn("example facts.json is missing 'source'.", result.messages)
        self.assertIn("example facts.json is missing 'last_updated'.", result.messages)


if __name__ == "__main__":
    unittest.main()
