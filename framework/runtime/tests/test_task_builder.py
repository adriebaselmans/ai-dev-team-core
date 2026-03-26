from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from task_builder import build_specialist_task_payload


class SpecialistTaskPayloadTests(unittest.TestCase):
    def test_build_specialist_payload_includes_role_skills_and_outputs(self) -> None:
        team = {
            "roles": {
                "explorer": {
                    "writes": ["framework/memory/repository-knowledge/"],
                    "primary_skill": ".github/skills/repository-exploration",
                    "supporting_skills": [".github/skills/repository-knowledge-compaction"],
                }
            }
        }

        payload = build_specialist_task_payload(
            "explorer",
            team,
            objective="Analyze target repository",
            active_feature="repo-analysis",
        )

        self.assertIn("Feature: `repo-analysis`", payload)
        self.assertIn("## Role\n`explorer`", payload)
        self.assertIn("`.github/skills/repository-exploration/SKILL.md`", payload)
        self.assertIn("`.github/skills/repository-knowledge-compaction/SKILL.md`", payload)
        self.assertIn("`framework/memory/repository-knowledge/`", payload)
        self.assertNotIn("Phase:", payload)


if __name__ == "__main__":
    unittest.main()
