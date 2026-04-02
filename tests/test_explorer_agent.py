from __future__ import annotations

from typing import Any

from agents.registry import build_default_agent_registry
from agents.roles import ExplorerAgent
from flows import default_flow_path
from state.factory import create_initial_state
from team_orchestrator.context_builders import ExplorerContextBuilder
from team_orchestrator.engine import Orchestrator
from team_orchestrator.execution import RoleExecutionRequest
from team_orchestrator.flow_loader import load_flow


class RecordingBackend:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.requests: list[RoleExecutionRequest] = []

    def invoke(self, request: RoleExecutionRequest) -> dict[str, Any]:
        self.requests.append(request)
        return dict(self.response)


def test_explorer_context_builder_captures_repo_context() -> None:
    builder = ExplorerContextBuilder()
    state = create_initial_state(
        "Ground this work in the existing repository.",
        overrides={
            "coordination": {"repo_mode": "existing", "ui_heavy": False},
            "repository": {"path": ".", "mode": "existing", "facts": ["Uses YAML flow definitions."]},
            "meta": {"roles": ["coordinator", "explorer"], "current_step": "initial-exploration"},
        },
    )

    context = builder.build(role_key="explorer", state=state, step_name="initial-exploration")

    assert context["coordination"]["repo_mode"] == "existing"
    assert context["repository"]["facts"] == ["Uses YAML flow definitions."]
    assert context["roles"] == ["coordinator", "explorer"]


def test_explorer_agent_executes_through_role_executor_when_active() -> None:
    backend = RecordingBackend(
        {
            "analysis": {
                "status": "ready",
                "repository_roles": ["coordinator", "explorer"],
                "insights": ["The repository already contains runtime tests and flow definitions."],
                "requested_by": None,
            }
        }
    )
    agent = ExplorerAgent(backend=backend)
    state = create_initial_state(
        "Explore the repository.",
        overrides={
            "meta": {"current_step": "initial-exploration"},
            "coordination": {"repo_mode": "existing"},
            "repository": {"path": "."},
        },
    )

    update = agent.run(state)

    assert update["analysis"]["status"] == "ready"
    assert backend.requests[0].role == "explorer"
    assert backend.requests[0].tool_policy["allow_local_read"] is True
    assert backend.requests[0].tool_policy["allow_external_research"] is False


def test_initial_exploration_flow_executes_real_explorer() -> None:
    registry = build_default_agent_registry()
    registry["explorer"] = ExplorerAgent(
        backend=RecordingBackend(
            {
                "analysis": {
                    "status": "ready",
                    "repository_roles": ["coordinator", "explorer"],
                    "insights": ["Existing runtime files should be preserved during refactor."],
                    "requested_by": None,
                }
            }
        )
    )
    orchestrator = Orchestrator(load_flow(default_flow_path()), registry)
    final_state = orchestrator.run(
        create_initial_state(
            "Refactor the runtime.",
            overrides={
                "repository": {"path": "."},
                "coordination": {"repo_mode": "existing"},
            },
        )
    )

    roles = [entry["role"] for entry in final_state["trace"]]
    assert "explorer" in roles
    assert final_state["analysis"]["status"] == "ready"
    assert final_state["meta"]["completed"] is True
