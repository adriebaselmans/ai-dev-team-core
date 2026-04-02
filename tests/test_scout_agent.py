from __future__ import annotations

from typing import Any

from agents.registry import build_default_agent_registry
from agents.roles import ScoutAgent
from flows import default_flow_path
from state.factory import create_initial_state
from team_orchestrator.context_builders import ScoutContextBuilder
from team_orchestrator.engine import Orchestrator
from team_orchestrator.flow_loader import load_flow
from team_orchestrator.execution import RoleExecutionRequest


class RecordingBackend:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.requests: list[RoleExecutionRequest] = []

    def invoke(self, request: RoleExecutionRequest) -> dict[str, Any]:
        self.requests.append(request)
        return dict(self.response)


def test_scout_context_builder_includes_requester_specific_context() -> None:
    builder = ScoutContextBuilder()
    state = create_initial_state(
        "Check current framework guidance.",
        overrides={
            "support_request": {
                "id": "arch-scout-1",
                "pending": True,
                "requested_by": "architect",
                "support_role": "scout",
                "question": "What changed in the framework recently?",
                "resume_step": "architecture",
                "reason": "Fresh guidance may change the design.",
            },
            "coordination": {"repo_mode": "existing", "ui_heavy": False},
            "repository": {"path": ".", "facts": ["Uses a YAML flow."]},
            "requirements": {
                "summary": "Refactor the orchestration runtime.",
                "acceptance_criteria": ["Keep the flow deterministic."],
                "constraints": ["Do not widen scope."],
            },
            "design": {
                "non_functional_requirements": ["Keep support-role traces visible."],
                "work_items": [{"id": "core", "description": "Refine the architecture."}],
            },
            "analysis": {"status": "ready", "insights": ["Repository already has runtime tests."]},
        },
    )

    context = builder.build(role_key="scout", state=state, step_name="support-execute")

    assert context["question"] == "What changed in the framework recently?"
    assert context["repository"]["facts"] == ["Uses a YAML flow."]
    assert context["requester_context"]["work_items"] == [
        {"id": "core", "description": "Refine the architecture."}
    ]


def test_scout_agent_executes_through_role_executor_when_requested() -> None:
    backend = RecordingBackend(
        {
            "research": {
                "status": "ready",
                "brief": ["Current guidance favors structured role outputs."],
                "requested_by": "architect",
                "verified_facts": ["The official docs now emphasize structured outputs."],
                "sources": [
                    {
                        "title": "Official structured outputs guide",
                        "url": "https://example.test/structured-outputs",
                        "date": "2026-04-01",
                    }
                ],
                "confidence": "high",
                "unknowns": [],
            }
        }
    )
    agent = ScoutAgent(backend=backend)
    state = create_initial_state(
        "Research current guidance.",
        overrides={
            "meta": {"current_step": "support-execute"},
            "support_request": {
                "id": "arch-scout-2",
                "pending": True,
                "requested_by": "architect",
                "support_role": "scout",
                "question": "What is the current official guidance?",
                "resume_step": "architecture",
                "reason": "Fresh guidance could change the design.",
            },
        },
    )

    update = agent.run(state)

    assert update["research"]["status"] == "ready"
    assert update["research"]["confidence"] == "high"
    assert backend.requests[0].role == "scout"
    assert backend.requests[0].tool_policy["allow_external_research"] is True
    assert backend.requests[0].context["question"] == "What is the current official guidance?"


def test_support_flow_executes_scout_and_resumes_requester() -> None:
    registry = build_default_agent_registry()
    registry["scout"] = ScoutAgent(
        backend=RecordingBackend(
            {
                "research": {
                    "status": "ready",
                    "brief": ["Found relevant current external evidence."],
                    "requested_by": "architect",
                    "verified_facts": ["A recent version changed the recommended pattern."],
                    "sources": [
                        {
                            "title": "Official release notes",
                            "url": "https://example.test/release-notes",
                            "date": "2026-03-31",
                        }
                    ],
                    "confidence": "high",
                    "unknowns": [],
                }
            }
        )
    )
    orchestrator = Orchestrator(load_flow(default_flow_path()), registry)
    final_state = orchestrator.run(
        create_initial_state(
            "Refactor with one Scout-supported architecture question.",
            overrides={
                "scenarios": {
                    "support_requests": [
                        {
                            "id": "arch-current-guidance",
                            "requested_by": "architect",
                            "support_role": "scout",
                            "question": "Check current external guidance before finalizing the design.",
                            "resume_step": "architecture",
                        }
                    ]
                }
            },
        )
    )

    roles = [entry["role"] for entry in final_state["trace"]]
    assert "scout" in roles
    assert final_state["research"]["status"] == "ready"
    assert "arch-current-guidance" in final_state["meta"]["completed_support_requests"]
    assert final_state["meta"]["completed"] is True
