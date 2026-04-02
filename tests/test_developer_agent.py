from __future__ import annotations

from typing import Any

from agents.roles import DeveloperAgent
from state.factory import create_initial_state
from team_orchestrator.context_builders import DeveloperContextBuilder
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


def test_developer_context_builder_collects_build_inputs() -> None:
    builder = DeveloperContextBuilder()
    state = create_initial_state(
        "Implement the changes.",
        overrides={
            "requirements": {"summary": "Refactor the runtime.", "acceptance_criteria": ["Keep role boundaries."], "constraints": []},
            "design": {
                "approved_for_build": True,
                "architecture": ["Use executor-backed specialists."],
                "non_functional_requirements": ["Keep traceability visible."],
                "work_items": [{"id": "core", "description": "Implement runtime changes."}],
            },
            "coordination": {
                "parallel_development": True,
                "work_items": [{"id": "core", "description": "Implement runtime changes."}],
                "integration_owner": "designated-developer",
            },
            "meta": {"current_parallel_item": {"id": "core", "description": "Implement runtime changes."}},
        },
    )

    context = builder.build(role_key="developer", state=state, step_name="parallel-development")

    assert context["design"]["approved_for_build"] is True
    assert context["parallel_item"]["id"] == "core"
    assert context["coordination"]["parallel_development"] is True


def test_developer_agent_executes_through_role_executor_for_main_flow() -> None:
    backend = RecordingBackend(
        {
            "development": {
                "status": "implemented",
                "revision": 1,
                "strategy": "sequential",
                "worker_results": [],
                "changes": ["Implemented the requested runtime changes."],
                "integration_owner": "designated-developer",
                "blockers": [],
                "rework_target": None,
            },
            "support_request": None,
        }
    )
    agent = DeveloperAgent(backend=backend)
    state = create_initial_state(
        "Implement the changes.",
        overrides={"meta": {"current_step": "development"}},
    )

    update = agent.run(state)

    assert update["development"]["status"] == "implemented"
    assert backend.requests[0].role == "developer"
    assert backend.requests[0].tool_policy["allow_local_write"] is True
    assert backend.requests[0].tool_policy["allow_shell"] is True


def test_developer_agent_executes_through_role_executor_for_parallel_worker() -> None:
    backend = RecordingBackend(
        {
            "development_artifact": {
                "worker_id": "worker-a",
                "description": "Implement worker A.",
                "status": "implemented",
            },
            "support_request": None,
        }
    )
    agent = DeveloperAgent(backend=backend)
    state = create_initial_state(
        "Implement the changes.",
        overrides={
            "meta": {
                "current_step": "parallel-development",
                "current_parallel_item": {"id": "worker-a", "description": "Implement worker A."},
            }
        },
    )

    update = agent.run(state)

    assert update["development_artifact"]["worker_id"] == "worker-a"
    assert backend.requests[0].context["parallel_item"]["id"] == "worker-a"


def test_developer_agent_falls_back_to_deterministic_behavior_on_backend_failure() -> None:
    agent = DeveloperAgent(backend=FailingBackend())
    state = create_initial_state(
        "Implement the changes.",
        overrides={"meta": {"current_step": "development"}},
    )

    update = agent.run(state)

    assert update["development"]["status"] == "implemented"
