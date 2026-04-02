from __future__ import annotations

from typing import Any

from agents.roles import RequirementsEngineerAgent
from state.factory import create_initial_state
from team_orchestrator.context_builders import RequirementsContextBuilder
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


def test_requirements_context_builder_collects_upstream_context() -> None:
    builder = RequirementsContextBuilder()
    state = create_initial_state(
        "Build a task API.",
        overrides={
            "coordination": {"repo_mode": "existing", "ui_heavy": False},
            "repository": {"path": ".", "facts": ["Existing pytest suite is present."]},
            "analysis": {"status": "ready", "insights": ["Repository already has a CLI entry point."]},
            "ux_ui": {"status": "ready", "guidance": ["Keep flows readable if UI work appears later."]},
        },
    )

    context = builder.build(role_key="requirements-engineer", state=state, step_name="requirements")

    assert context["user_input"] == "Build a task API."
    assert context["repository"]["facts"] == ["Existing pytest suite is present."]
    assert context["repository_analysis"]["insights"] == ["Repository already has a CLI entry point."]


def test_requirements_agent_executes_through_role_executor() -> None:
    backend = RecordingBackend(
        {
            "requirements": {
                "ready": True,
                "summary": "Build a task API.",
                "acceptance_criteria": ["Create/list/update/delete tasks."],
                "constraints": ["Keep the implementation minimal."],
                "needs_user_input": False,
                "in_scope": ["REST endpoints"],
                "out_of_scope": ["Authentication"],
                "functional_requirements": ["Persist tasks in SQLite."],
                "assumptions": ["Single-user mode is acceptable."],
                "open_questions": [],
            },
            "support_request": None,
        }
    )
    agent = RequirementsEngineerAgent(backend=backend)
    state = create_initial_state(
        "Build a task API.",
        overrides={"meta": {"current_step": "requirements"}},
    )

    update = agent.run(state)

    assert update["requirements"]["ready"] is True
    assert backend.requests[0].role == "requirements-engineer"
    assert backend.requests[0].context["user_input"] == "Build a task API."


def test_requirements_agent_falls_back_to_deterministic_behavior_on_backend_failure() -> None:
    agent = RequirementsEngineerAgent(backend=FailingBackend())
    state = create_initial_state(
        "Build a task API.",
        overrides={"meta": {"current_step": "requirements"}},
    )

    update = agent.run(state)

    assert update["requirements"]["ready"] is True
    assert update["requirements"]["summary"] == "Build a task API."
