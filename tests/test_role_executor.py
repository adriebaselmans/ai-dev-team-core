from __future__ import annotations

from typing import Any

import pytest

from state.factory import create_initial_state
from team_orchestrator.execution import (
    RoleExecutionContractError,
    RoleExecutionRequest,
    RoleExecutor,
    ToolPolicy,
)


class StaticContextBuilder:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
        self.calls: list[tuple[str, str]] = []

    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        self.calls.append((role_key, step_name))
        return dict(self.context)


class RecordingBackend:
    def __init__(self, *, response: dict[str, Any], repaired: dict[str, Any] | None = None) -> None:
        self.response = response
        self.repaired = repaired
        self.requests: list[RoleExecutionRequest] = []
        self.repair_requests: list[tuple[dict[str, Any], list[str]]] = []

    def invoke(self, request: RoleExecutionRequest) -> dict[str, Any]:
        self.requests.append(request)
        return dict(self.response)

    def repair(
        self,
        request: RoleExecutionRequest,
        *,
        invalid_output: dict[str, Any],
        validation_errors: list[str],
    ) -> dict[str, Any] | None:
        self.repair_requests.append((dict(invalid_output), list(validation_errors)))
        return None if self.repaired is None else dict(self.repaired)


def test_role_executor_builds_request_and_validates_output() -> None:
    executor = RoleExecutor()
    backend = RecordingBackend(
        response={
            "review": {
                "decision": "approved",
                "approved": True,
                "feedback": "Approved for testing.",
                "score": 0.95,
                "blocking_findings": [],
                "rework_target": "developer",
            }
        }
    )
    context_builder = StaticContextBuilder({"input": "Review the implementation."})

    result = executor.execute(
        role_key="reviewer",
        state=create_initial_state("Review the implementation."),
        step_name="review",
        context_builder=context_builder,
        backend=backend,
        tool_policy=ToolPolicy(allow_local_read=True),
    )

    assert result.update["review"]["approved"] is True
    assert result.metadata.validation_status == "valid"
    assert result.metadata.repair_count == 0
    assert backend.requests[0].role == "reviewer"
    assert backend.requests[0].step_name == "review"
    assert backend.requests[0].tool_policy["allow_local_read"] is True
    assert context_builder.calls == [("reviewer", "review")]


def test_role_executor_uses_single_repair_pass_for_invalid_output() -> None:
    executor = RoleExecutor()
    backend = RecordingBackend(
        response={"review": {"approved": True}},
        repaired={
            "review": {
                "decision": "approved",
                "approved": True,
                "feedback": "Approved after repair.",
                "score": 0.9,
                "blocking_findings": [],
                "rework_target": "developer",
            }
        },
    )

    result = executor.execute(
        role_key="reviewer",
        state=create_initial_state("Review the implementation."),
        step_name="review",
        context_builder=StaticContextBuilder({"input": "Review the implementation."}),
        backend=backend,
        tool_policy=ToolPolicy(allow_local_read=True),
    )

    assert result.metadata.validation_status == "repaired"
    assert result.metadata.repair_count == 1
    assert len(backend.repair_requests) == 1


def test_role_executor_raises_on_unrepairable_contract_violation() -> None:
    executor = RoleExecutor()
    backend = RecordingBackend(response={"review": {"approved": True}})

    with pytest.raises(RoleExecutionContractError):
        executor.execute(
            role_key="reviewer",
            state=create_initial_state("Review the implementation."),
            step_name="review",
            context_builder=StaticContextBuilder({"input": "Review the implementation."}),
            backend=backend,
            tool_policy=ToolPolicy(allow_local_read=True),
        )


def test_role_executor_uses_backend_registry_when_backend_not_supplied() -> None:
    class StaticRegistry:
        def __init__(self, backend: RecordingBackend) -> None:
            self.backend = backend
            self.role_keys: list[str] = []

        def create_for_role(self, role_config: Any) -> RecordingBackend:
            self.role_keys.append(role_config.role)
            return self.backend

    backend = RecordingBackend(
        response={
            "review": {
                "decision": "approved",
                "approved": True,
                "feedback": "Approved from registry backend.",
                "score": 0.91,
                "blocking_findings": [],
                "rework_target": "developer",
            }
        }
    )
    executor = RoleExecutor(backend_registry=StaticRegistry(backend))

    result = executor.execute(
        role_key="reviewer",
        state=create_initial_state("Review the implementation."),
        step_name="review",
        context_builder=StaticContextBuilder({"input": "Review the implementation."}),
        backend=None,
        tool_policy=ToolPolicy(allow_local_read=True),
    )

    assert result.update["review"]["approved"] is True
