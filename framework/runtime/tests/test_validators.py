from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import memory_store
import validators
from spec_loader import phase_canonical_source


BRIEF_TEXT = """# Example

## Repository Identity
- Name: example

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


class RuntimeValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._sandbox_root = Path(tempfile.mkdtemp(prefix='runtime-tests-', dir=Path(__file__).resolve().parents[3]))

    def tearDown(self) -> None:
        shutil.rmtree(self._sandbox_root, ignore_errors=True)

    def _write_store(self, root: Path) -> None:
        store = root / 'framework' / 'memory' / 'repository-knowledge'
        store.mkdir(parents=True, exist_ok=True)
        (store / 'README.md').write_text('# Store\n', encoding='utf-8')
        (store / 'TEMPLATE.md').write_text('# Template\n', encoding='utf-8')
        (store / 'index.md').write_text('# Repository Knowledge Index\n\n## Entries\n- example\n', encoding='utf-8')
        repo_dir = store / 'example'
        repo_dir.mkdir(exist_ok=True)
        (repo_dir / 'brief.md').write_text(BRIEF_TEXT, encoding='utf-8')
        facts = {
            'name': 'example',
            'source': 'C:/tmp/example',
            'last_updated': '2026-03-27',
            'open_questions': [],
        }
        (repo_dir / 'facts.json').write_text(json.dumps(facts), encoding='utf-8')

    def _write_required_development_paths(self, root: Path, *, omit: str | None = None) -> None:
        for relative_path in validators.DEVELOPMENT_REQUIRED_PATHS:
            if relative_path == omit:
                continue
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('# placeholder\n', encoding='utf-8')

    def test_validate_transition_rejects_virgin_requirements(self) -> None:
        with (
            patch.object(validators, 'load_artifact', return_value={'definition_of_ready': 'Not ready.'}),
            patch.object(validators, 'validate_artifact_data', return_value=[]),
        ):
            result = validators.validate_transition('requirements_ready', 'requirements')
        self.assertFalse(result.valid)
        self.assertIn("Definition of Ready must be 'Ready.'.", result.messages)

    def test_repository_knowledge_store_accepts_valid_store(self) -> None:
        root = self._sandbox_root / 'case-valid'
        self._write_store(root)
        with patch.object(validators, 'repo_root', return_value=root):
            result = validators.validate_repository_knowledge_store()
        self.assertTrue(result.valid)

    def test_memory_store_writes_and_reads_briefs(self) -> None:
        root = self._sandbox_root / 'case-memory'
        with patch.object(memory_store, 'repo_root', return_value=root):
            memory_store.append_memory_record(
                kind='phase-brief',
                phase='requirements',
                summary='Brief',
                payload={'x': 1},
                tags=['compact'],
            )
            result = memory_store.latest_brief()

        self.assertIsNotNone(result)
        self.assertEqual(result['phase'], 'requirements')

    def test_validate_development_requires_concrete_test_outputs(self) -> None:
        root = self._sandbox_root / 'case-development'
        self._write_required_development_paths(root, omit='framework/runtime/tests/test_task_builder.py')

        with patch.object(validators, 'repo_root', return_value=root):
            result = validators.validate_development()

        self.assertFalse(result.valid)
        self.assertIn('Missing required development output: framework/runtime/tests/test_task_builder.py', result.messages)

    def test_phase_specs_declare_canonical_sources(self) -> None:
        self.assertEqual(phase_canonical_source('development'), 'artifacts')
        self.assertEqual(phase_canonical_source('dod-review'), 'state')


if __name__ == '__main__':
    unittest.main()
