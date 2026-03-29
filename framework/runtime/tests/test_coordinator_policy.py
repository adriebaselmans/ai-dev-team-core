from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_loader import load_team_spec
from task_builder import build_specialist_payload


class CoordinatorPolicyTests(unittest.TestCase):
    def test_coordinator_is_marked_read_only_and_owns_no_outputs(self) -> None:
        team = load_team_spec()

        self.assertTrue(team["roles"]["coordinator"]["read_only"])
        self.assertEqual(team["roles"]["coordinator"].get("writes"), [])

        payload = build_specialist_payload(
            "coordinator",
            team,
            {"phase": "dod-review", "owner": "coordinator", "active_feature": "framework rework"},
            "Present the final DoD review.",
        )

        self.assertEqual(payload["owned_outputs"], [])

    def test_read_only_coordinator_cannot_declare_owned_outputs(self) -> None:
        team = load_team_spec()
        team["roles"]["coordinator"]["writes"] = ["framework/runtime/state.json"]

        with self.assertRaisesRegex(ValueError, "Read-only role 'coordinator' cannot declare owned outputs"):
            build_specialist_payload(
                "coordinator",
                team,
                {"phase": "dod-review", "owner": "coordinator", "active_feature": "framework rework"},
                "Present the final DoD review.",
            )


if __name__ == "__main__":
    unittest.main()

