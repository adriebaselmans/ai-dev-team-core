"""Single source of truth for blank phase-artifact payload shapes.

The same blank skeleton is needed in three places:

- ``init.py`` seeds the artifacts during bootstrap, optionally overlaying
  project metadata.
- ``team_orchestrator.artifact_sync`` writes pristine placeholders when no
  upstream role output exists yet.
- The test suite asserts the canonical shape and resets fixtures.

Keeping the shapes here prevents drift between those three call sites.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_BLANK_ARTIFACT_PAYLOADS: dict[str, dict[str, Any]] = {
    "requirements": {
        "status": "Pending.",
        "title": "",
        "user_need": "",
        "goal": "",
        "in_scope": [],
        "out_of_scope": [],
        "functional_requirements": [],
        "acceptance_criteria": [],
        "constraints": [],
        "assumptions": [],
        "open_questions": [],
        "definition_of_ready": "Not ready.",
    },
    "design": {
        "title": "",
        "design_goal": "",
        "architecture_approach": [],
        "affected_areas": [],
        "separation_of_concerns": [],
        "module_boundaries": [],
        "data_flow": [],
        "interfaces": [],
        "technology_and_environment_considerations": [],
        "technology_choices": [],
        "clean_code_constraints": [],
        "performance_considerations": [],
        "risks_and_tradeoffs": [],
        "non_goals": [],
    },
    "review": {
        "status": "Pending.",
        "title": "",
        "decision": "Not reviewed.",
        "findings": [],
        "residual_risks": [],
        "recommendation": "",
    },
    "dod": {
        "status": "Pending.",
        "title": "",
        "delivery_summary": [],
        "requirements_coverage": [],
        "what_was_built": [],
        "what_was_verified": [],
        "automated_regression_coverage": [],
        "acceptance_test_coverage": [],
        "known_gaps_or_risks": [],
        "decision": "Not evaluated.",
        "user_feedback_needed": [],
    },
}


ARTIFACT_NAMES: tuple[str, ...] = tuple(_BLANK_ARTIFACT_PAYLOADS)


def blank_artifact_payload(name: str) -> dict[str, Any]:
    """Return a deep copy of the blank payload for the given artifact."""
    try:
        return deepcopy(_BLANK_ARTIFACT_PAYLOADS[name])
    except KeyError as exc:
        raise KeyError(f"Unknown artifact '{name}'.") from exc


def blank_artifact_payloads() -> dict[str, dict[str, Any]]:
    """Return deep copies of all blank artifact payloads keyed by name."""
    return {name: blank_artifact_payload(name) for name in ARTIFACT_NAMES}
