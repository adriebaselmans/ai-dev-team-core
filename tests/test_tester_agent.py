from __future__ import annotations

from typing import Any

from agents.roles import TesterAgent as RuntimeTesterAgent
from state.factory import create_initial_state
from team_orchestrator.context_builders import TesterContextBuilder
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


def test_tester_context_builder_collects_acceptance_context() -> None:
    builder = TesterContextBuilder()
    state = create_initial_state(
        "Validate the implementation.",
        overrides={
            "requirements": {"summary": "Build the task API.", "acceptance_criteria": ["CRUD tasks."], "constraints": []},
            "design": {"non_functional_requirements": ["Keep traceability visible."], "work_items": []},
            "development": {
                "status": "implemented",
                "revision": 2,
                "strategy": "sequential",
                "changes": ["Implemented the runtime changes."],
            },
            "review": {"decision": "approved", "feedback": "Ready for testing.", "blocking_findings": []},
        },
    )

    context = builder.build(role_key="tester", state=state, step_name="testing")

    assert context["development"]["revision"] == 2
    assert context["review"]["decision"] == "approved"


def test_tester_agent_executes_through_role_executor() -> None:
    backend = RecordingBackend(
        {
            "test_results": {
                "decision": "passed",
                "passed": True,
                "errors": [],
                "automated": True,
                "rework_target": "developer",
            },
            "support_request": None,
        }
    )
    agent = RuntimeTesterAgent(backend=backend)
    state = create_initial_state(
        "Validate the implementation.",
        overrides={"development": {"status": "implemented", "revision": 1}},
    )

    update = agent.run(state)

    assert update["test_results"]["passed"] is True
    assert backend.requests[0].role == "tester"


def test_tester_agent_falls_back_to_deterministic_behavior_on_backend_failure() -> None:
    agent = RuntimeTesterAgent(backend=FailingBackend())
    state = create_initial_state(
        "Validate the implementation.",
        overrides={"development": {"status": "implemented", "revision": 1}},
    )

    update = agent.run(state)

    assert update["test_results"]["decision"] in {"passed", "failed"}
