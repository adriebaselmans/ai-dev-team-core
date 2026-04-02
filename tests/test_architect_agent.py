from __future__ import annotations

from typing import Any

from agents.roles import ArchitectAgent
from state.factory import create_initial_state
from team_orchestrator.context_builders import ArchitectContextBuilder
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


def test_architect_context_builder_collects_requirements_and_support_outputs() -> None:
    builder = ArchitectContextBuilder()
    state = create_initial_state(
        "Refactor the runtime.",
        overrides={
            "coordination": {"repo_mode": "existing", "parallel_development": True},
            "requirements": {
                "ready": True,
                "summary": "Refactor the runtime.",
                "acceptance_criteria": ["Keep deterministic flow control."],
                "constraints": ["Coordinator stays read-only."],
                "functional_requirements": ["Preserve role-based execution."],
                "assumptions": ["Single repository scope."],
                "open_questions": [],
            },
            "ux_ui": {"status": "ready", "guidance": ["Keep traces readable."]},
            "analysis": {"status": "ready", "insights": ["Repo already uses YAML flow definitions."]},
            "research": {
                "status": "ready",
                "brief": ["Recent guidance favors structured outputs."],
                "verified_facts": ["Official docs emphasize structured schemas."],
                "sources": [{"title": "Docs", "url": "https://example.test", "date": "2026-04-01"}],
                "confidence": "high",
                "unknowns": [],
            },
        },
    )

    context = builder.build(role_key="architect", state=state, step_name="architecture")

    assert context["requirements"]["ready"] is True
    assert context["research"]["confidence"] == "high"
    assert context["repository_analysis"]["insights"] == ["Repo already uses YAML flow definitions."]


def test_architect_agent_executes_through_role_executor() -> None:
    backend = RecordingBackend(
        {
            "design": {
                "approved_for_build": True,
                "architecture": ["Use a deterministic orchestrator with executor-backed specialists."],
                "non_functional_requirements": ["Keep traceability visible."],
                "work_items": [{"id": "core", "description": "Implement the runtime changes."}],
                "module_boundaries": ["Keep orchestrator and execution layers separate."],
                "interfaces": ["Role executor returns validated structured updates."],
                "data_flow": ["requirements -> design -> development"],
                "risks_and_tradeoffs": ["Live backends require configuration."],
            },
            "support_request": None,
        }
    )
    agent = ArchitectAgent(backend=backend)
    state = create_initial_state(
        "Refactor the runtime.",
        overrides={
            "meta": {"current_step": "architecture"},
            "requirements": {"ready": True, "summary": "Refactor the runtime."},
        },
    )

    update = agent.run(state)

    assert update["design"]["approved_for_build"] is True
    assert backend.requests[0].role == "architect"
    assert backend.requests[0].context["requirements"]["summary"] == "Refactor the runtime."


def test_architect_agent_falls_back_to_deterministic_behavior_on_backend_failure() -> None:
    agent = ArchitectAgent(backend=FailingBackend())
    state = create_initial_state(
        "Refactor the runtime.",
        overrides={
            "meta": {"current_step": "architecture"},
            "requirements": {"ready": True, "summary": "Refactor the runtime."},
        },
    )

    update = agent.run(state)

    assert update["design"]["approved_for_build"] is True
    assert update["design"]["architecture"]
