from __future__ import annotations

from typing import Any

from agents.roles import ReviewerAgent
from state.factory import create_initial_state
from team_orchestrator.context_builders import ReviewerContextBuilder
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


def test_reviewer_context_builder_collects_review_inputs() -> None:
    builder = ReviewerContextBuilder()
    state = create_initial_state(
        "Review the implementation.",
        overrides={
            "requirements": {"summary": "Build the task API.", "acceptance_criteria": ["CRUD tasks."], "constraints": []},
            "design": {
                "architecture": ["Use a deterministic orchestrator."],
                "non_functional_requirements": ["Keep traces visible."],
                "work_items": [{"id": "core", "description": "Implement core logic."}],
            },
            "development": {
                "status": "implemented",
                "revision": 2,
                "strategy": "sequential",
                "worker_results": [],
                "changes": ["Implemented the runtime changes."],
            },
        },
    )

    context = builder.build(role_key="reviewer", state=state, step_name="review")

    assert context["development"]["revision"] == 2
    assert context["design"]["architecture"] == ["Use a deterministic orchestrator."]


def test_reviewer_agent_executes_through_role_executor() -> None:
    backend = RecordingBackend(
        {
            "review": {
                "decision": "approved",
                "approved": True,
                "feedback": "Ready for testing.",
                "score": 0.96,
                "blocking_findings": [],
                "rework_target": "developer",
                "residual_risks": [],
            },
            "support_request": None,
        }
    )
    agent = ReviewerAgent(backend=backend)
    state = create_initial_state(
        "Review the implementation.",
        overrides={"development": {"status": "implemented", "revision": 1}},
    )

    update = agent.run(state)

    assert update["review"]["approved"] is True
    assert backend.requests[0].role == "reviewer"


def test_reviewer_agent_falls_back_to_deterministic_behavior_on_backend_failure() -> None:
    agent = ReviewerAgent(backend=FailingBackend())
    state = create_initial_state(
        "Review the implementation.",
        overrides={"development": {"status": "implemented", "revision": 1}},
    )

    update = agent.run(state)

    assert update["review"]["decision"] in {"approved", "rework"}
