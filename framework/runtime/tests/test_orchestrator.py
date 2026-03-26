from __future__ import annotations

import argparse
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import orchestrator
from validators import ValidationResult


class SpecialistTaskCommandTests(unittest.TestCase):
    def test_specialist_task_prints_payload_for_explorer(self) -> None:
        args = argparse.Namespace(
            role="explorer",
            objective="Analyze repo",
            feature=None,
            input=[],
            output=[],
            completion=None,
        )
        team = {
            "roles": {
                "explorer": {
                    "writes": ["framework/memory/repository-knowledge/"],
                    "primary_skill": ".github/skills/repository-exploration",
                    "supporting_skills": [".github/skills/repository-knowledge-compaction"],
                }
            }
        }
        state = {"active_feature": "feature-x"}

        with patch.object(orchestrator, "load_team_spec", return_value=team), patch.object(
            orchestrator, "load_state", return_value=state
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = orchestrator.cmd_specialist_task(args)

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("`explorer`", output)
        self.assertIn("`Analyze repo`", output)
        self.assertIn("feature-x", output)
        self.assertNotIn("Phase:", output)

    def test_validate_repository_knowledge_returns_success(self) -> None:
        with patch.object(orchestrator, "validate_repository_knowledge_store") as validator:
            validator.return_value = ValidationResult(
                valid=True,
                messages=["Repository knowledge store is valid."],
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = orchestrator.cmd_validate_repository_knowledge(argparse.Namespace())

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Repository knowledge store is valid.", output)


if __name__ == "__main__":
    unittest.main()
