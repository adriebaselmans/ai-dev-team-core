from __future__ import annotations

from agents.registry import build_default_agent_registry
from framework.runtime.role_contracts import (
    load_role_output_schema,
    validate_role_output,
    validate_role_output_coverage,
)
from state.factory import create_initial_state


def _state_for_role(role_key: str) -> dict[str, object]:
    if role_key == "coordinator":
        return create_initial_state(
            "Refactor the orchestration runtime.",
            overrides={"meta": {"current_step": "intake"}},
        )
    if role_key == "requirements-engineer":
        return create_initial_state(
            "Refactor the orchestration runtime.",
            overrides={"meta": {"current_step": "requirements"}},
        )
    if role_key == "architect":
        return create_initial_state(
            "Refactor the orchestration runtime.",
            overrides={
                "meta": {"current_step": "architecture"},
                "requirements": {"ready": True, "summary": "Refactor the orchestration runtime."},
            },
        )
    if role_key == "developer":
        return create_initial_state(
            "Refactor the orchestration runtime.",
            overrides={"meta": {"current_step": "development"}},
        )
    if role_key == "reviewer":
        return create_initial_state(
            "Refactor the orchestration runtime.",
            overrides={"development": {"status": "implemented", "revision": 1}},
        )
    if role_key == "tester":
        return create_initial_state(
            "Refactor the orchestration runtime.",
            overrides={"development": {"status": "implemented", "revision": 1}},
        )
    if role_key == "dod-reviewer":
        return create_initial_state(
            "Refactor the orchestration runtime.",
            overrides={"development": {"status": "implemented", "revision": 1}},
        )
    return create_initial_state("Refactor the orchestration runtime.")


def test_role_output_contracts_cover_all_active_roles() -> None:
    validate_role_output_coverage(list(build_default_agent_registry()))


def test_default_role_updates_validate_against_output_contracts() -> None:
    registry = build_default_agent_registry()

    for role_key, agent in registry.items():
        state = _state_for_role(role_key)
        update = agent.run(state)
        errors = validate_role_output(role_key, update)
        assert errors == [], f"{role_key} returned invalid output: {errors}"


def test_developer_parallel_worker_output_validates_against_contract() -> None:
    registry = build_default_agent_registry()
    state = create_initial_state(
        "Implement the worker item.",
        overrides={
            "meta": {
                "current_step": "parallel-development",
                "current_parallel_item": {"id": "worker-a", "description": "Implement worker A."},
            }
        },
    )

    update = registry["developer"].run(state)
    errors = validate_role_output("developer", update)
    assert errors == []


def test_role_output_schema_materializes_shared_definitions() -> None:
    schema = load_role_output_schema("reviewer")

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert "definitions" in schema
    assert "review" in schema["properties"]


def test_side_effect_assessment_is_required_for_analysis_and_change_gates() -> None:
    contracts = {
        "explorer": "analysis",
        "architect": "design",
        "developer": "development",
        "reviewer": "review",
        "tester": "test_results",
        "dod-reviewer": "dod_review",
    }

    for role_key, payload_key in contracts.items():
        schema = load_role_output_schema(role_key)
        payload_ref = schema["properties"][payload_key]["$ref"]
        definition_key = payload_ref.rsplit("/", 1)[-1]
        definition = schema["definitions"][definition_key]
        assert "side_effect_assessment" in definition["required"]
