from __future__ import annotations

from typing import Any

from agents.roles import DodReviewerAgent
from state.factory import create_initial_state
from team_orchestrator.context_builders import DoDReviewerContextBuilder
from team_orchestrator.execution import RoleExecutionError, RoleExecutionRequest


class RecordingBackend:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.requests: list[RoleExecutionRequest] = []

    def invoke(self, request: RoleExecutionRequest) -> dict[str, Any]:
        self.requests.append(request)
        return dict(self.response)


class FailingBackend:
    def invoke(self, request: RoleExecutionRequest) -> dict[str, Any]:
        raise RoleExecutionError("backend unavailable")


def test_dod_context_builder_collects_final_acceptance_context() -> None:
    builder = DoDReviewerContextBuilder()
    state = create_initial_state(
        "Check DoD.",
        overrides={
            "requirements": {"summary": "Build the task API.", "acceptance_criteria": ["CRUD tasks."], "constraints": []},
            "design": {
                "architecture": ["Use a deterministic orchestrator."],
                "non_functional_requirements": ["Keep traces visible."],
            },
            "development": {"status": "implemented", "revision": 2, "changes": ["Implemented the runtime changes."]},
            "review": {"decision": "approved", "feedback": "Ready."},
            "test_results": {"decision": "passed", "passed": True, "errors": []},
        },
    )

    context = builder.build(role_key="dod-reviewer", state=state, step_name="dod-review")

    assert context["development"]["revision"] == 2
    assert context["test_results"]["passed"] is True


def test_dod_reviewer_agent_executes_through_role_executor() -> None:
    backend = RecordingBackend(
        {
            "dod_review": {
                "decision": "accepted",
                "approved": True,
                "feedback": "Definition of Done is satisfied.",
                "blocking_findings": [],
                "rework_target": "developer",
            }
        }
    )
    agent = DodReviewerAgent(backend=backend)
    state = create_initial_state(
        "Check DoD.",
        overrides={"development": {"status": "implemented", "revision": 1}},
    )

    update = agent.run(state)

    assert update["dod_review"]["approved"] is True
    assert backend.requests[0].role == "dod-reviewer"


def test_dod_reviewer_agent_falls_back_to_deterministic_behavior_on_backend_failure() -> None:
    agent = DodReviewerAgent(backend=FailingBackend())
    state = create_initial_state(
        "Check DoD.",
        overrides={"development": {"status": "implemented", "revision": 1}},
    )

    update = agent.run(state)

    assert update["dod_review"]["decision"] in {"accepted", "rework"}
