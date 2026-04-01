from __future__ import annotations

from agents.discovery import discover_roles
from agents.registry import build_default_agent_registry
from state.factory import create_initial_state


def test_role_discovery_preserves_existing_roles_and_adds_dod_gate() -> None:
    roles = {role.key for role in discover_roles()}
    assert roles == {
        "coordinator",
        "requirements-engineer",
        "ux-ui-designer",
        "scout",
        "architect",
        "developer",
        "reviewer",
        "tester",
        "dod-reviewer",
        "explorer",
    }


def test_default_agent_registry_covers_discovered_roles() -> None:
    registry = build_default_agent_registry()
    state = create_initial_state("Refactor the orchestration runtime.")

    for role in discover_roles():
        assert role.key in registry
        agent = registry[role.key]
        update = agent.run(state)
        assert isinstance(update, dict)
        assert set(update).issubset(agent.owned_fields)


def test_gate_roles_return_structured_decisions() -> None:
    registry = build_default_agent_registry()
    state = create_initial_state(
        "Improve review and validation loops.",
        overrides={"development": {"status": "implemented", "revision": 2}},
    )

    review = registry["reviewer"].run(state)["review"]
    test_results = registry["tester"].run(state)["test_results"]
    dod_review = registry["dod-reviewer"].run(state)["dod_review"]

    assert set(review) == {"decision", "approved", "feedback", "score", "blocking_findings", "rework_target"}
    assert set(test_results) == {"decision", "passed", "errors", "automated", "rework_target"}
    assert set(dod_review) == {"decision", "approved", "feedback", "blocking_findings", "rework_target"}
