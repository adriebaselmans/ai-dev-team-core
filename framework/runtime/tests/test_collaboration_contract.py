from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_loader import load_team_spec, phase_spec
from task_builder import build_phase_dispatch_envelope, build_specialist_payload


class CollaborationContractTests(unittest.TestCase):
    def test_review_phase_dispatch_contract_focuses_on_code_review_and_developer_rework(self) -> None:
        team = load_team_spec()

        envelope = build_phase_dispatch_envelope(
            "review",
            team,
            {
                "phase": "review",
                "owner": "reviewer",
                "active_feature": "runtime workflow refinement",
                "next_action": "dispatch reviewer",
            },
        )

        self.assertEqual(envelope.collaboration_contract["focus"], "code-review-only")
        self.assertEqual(envelope.collaboration_contract["primary_partner"]["role"], "developer")
        self.assertIn("rework", envelope.collaboration_contract["primary_partner"]["purpose"])

    def test_tester_payload_requires_requirements_engineer_and_optionally_architect(self) -> None:
        team = load_team_spec()

        payload = build_specialist_payload(
            "tester",
            team,
            {"phase": "testing", "owner": "tester", "active_feature": "runtime workflow refinement"},
            "Validate acceptance criteria and produce the DoD record.",
        )

        self.assertEqual(payload["collaboration_contract"]["focus"], "acceptance-validation")
        required = payload["collaboration_contract"]["required"]
        optional = payload["collaboration_contract"]["optional"]
        self.assertEqual(required[0]["role"], "requirements-engineer")
        self.assertEqual(optional[0]["role"], "architect")

    def test_scout_payload_requires_architect_collaboration(self) -> None:
        team = load_team_spec()

        payload = build_specialist_payload(
            "scout",
            team,
            {
                "phase": "architecture",
                "owner": "architect",
                "active_feature": "current external research",
                "next_action": "dispatch scout",
            },
            "Gather current external evidence for the architect.",
        )

        self.assertEqual(payload["collaboration_contract"]["focus"], "external-research")
        required = payload["collaboration_contract"]["required"]
        self.assertEqual(required[0]["role"], "architect")
        self.assertEqual(payload["owned_outputs"], [])

    def test_testing_phase_contract_adds_acceptance_and_non_functional_validation_partners(self) -> None:
        contract = phase_spec("testing")["collaboration"]

        self.assertEqual(contract["validates_with"][0]["role"], "requirements-engineer")
        self.assertEqual(contract["consults_when_needed"][0]["role"], "architect")

    def test_architecture_phase_contract_can_request_scout_for_current_research(self) -> None:
        contract = phase_spec("architecture")["collaboration"]

        self.assertEqual(contract["optional_partners"][0]["role"], "scout")
        self.assertIn("current external evidence", contract["optional_partners"][0]["purpose"])


if __name__ == "__main__":
    unittest.main()

