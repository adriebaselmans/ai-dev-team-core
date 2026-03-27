from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from task_builder import build_phase_dispatch_envelope
from spec_loader import load_team_spec


class PhaseDispatchEnvelopeTests(unittest.TestCase):
    def test_build_phase_dispatch_envelope_uses_model_selection_and_context_slice(self) -> None:
        envelope = build_phase_dispatch_envelope(
            "requirements",
            load_team_spec(),
            {
                "phase": "requirements",
                "owner": "requirements-engineer",
                "active_feature": "framework rework",
                "next_action": "dispatch requirements specialist",
            },
        )

        self.assertEqual(envelope.role, "requirements-engineer")
        self.assertEqual(envelope.phase, "requirements")
        self.assertEqual(envelope.model_selection.provider, "openai")
        self.assertIn("requirements", envelope.context_slice)


if __name__ == "__main__":
    unittest.main()
