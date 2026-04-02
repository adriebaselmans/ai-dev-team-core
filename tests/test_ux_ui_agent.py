from __future__ import annotations

from typing import Any

from agents.registry import build_default_agent_registry
from agents.roles import UXUIDesignerAgent
from flows import default_flow_path
from state.factory import create_initial_state
from team_orchestrator.context_builders import UXUIContextBuilder
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


def test_ux_ui_context_builder_includes_ui_scope_inputs() -> None:
    builder = UXUIContextBuilder()
    state = create_initial_state(
        "Clarify the UI expectations.",
        overrides={
            "coordination": {"ui_heavy": True},
            "requirements": {
                "summary": "Improve the UI flow.",
                "acceptance_criteria": ["Flow should remain readable."],
                "constraints": ["Keep accessibility visible."],
            },
            "analysis": {"status": "ready", "insights": ["Repo already has flow traces."]},
            "design": {"non_functional_requirements": ["Maintain readable state transitions."]},
        },
    )

    context = builder.build(role_key="ux-ui-designer", state=state, step_name="ux-ui")

    assert context["ui_heavy"] is True
    assert context["requirements"]["summary"] == "Improve the UI flow."
    assert context["repository_analysis"]["insights"] == ["Repo already has flow traces."]


def test_ux_ui_agent_executes_through_role_executor_when_active() -> None:
    backend = RecordingBackend(
        {
            "ux_ui": {
                "status": "ready",
                "guidance": [
                    "Keep state transitions readable.",
                    "Treat accessibility as part of acceptance.",
                ],
                "requested_by": None,
            }
        }
    )
    agent = UXUIDesignerAgent(backend=backend)
    state = create_initial_state(
        "Improve the UI flow.",
        overrides={
            "meta": {"current_step": "ux-ui"},
            "coordination": {"ui_heavy": True},
        },
    )

    update = agent.run(state)

    assert update["ux_ui"]["status"] == "ready"
    assert backend.requests[0].role == "ux-ui-designer"
    assert backend.requests[0].tool_policy["allow_local_read"] is True


def test_support_flow_executes_ux_ui_and_resumes_requester() -> None:
    registry = build_default_agent_registry()
    registry["ux-ui-designer"] = UXUIDesignerAgent(
        backend=RecordingBackend(
            {
                "ux_ui": {
                    "status": "ready",
                    "guidance": ["Clarify accessibility expectations for the UI-heavy feature."],
                    "requested_by": "developer",
                }
            }
        )
    )
    orchestrator = Orchestrator(load_flow(default_flow_path()), registry)
    final_state = orchestrator.run(
        create_initial_state(
            "Implement a UI-heavy flow.",
            overrides={
                "coordination": {"ui_heavy": True},
                "scenarios": {
                    "support_requests": [
                        {
                            "id": "dev-ui-question",
                            "requested_by": "developer",
                            "support_role": "ux-ui-designer",
                            "question": "Clarify the accessibility expectations.",
                            "resume_step": "development",
                        }
                    ]
                },
            },
        )
    )

    roles = [entry["role"] for entry in final_state["trace"]]
    assert "ux-ui-designer" in roles
    assert final_state["ux_ui"]["status"] == "ready"
    assert "dev-ui-question" in final_state["meta"]["completed_support_requests"]
