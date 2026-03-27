from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from spec_loader import load_models_config


@dataclass(frozen=True)
class ModelSelection:
    provider: str
    model: str
    mode: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DispatchEnvelope:
    role: str
    phase: str
    objective: str
    context_slice: dict[str, Any]
    owned_outputs: list[str]
    skill_contracts: list[dict[str, Any]]
    model_selection: ModelSelection
    correlation_id: str


@dataclass(frozen=True)
class DispatchReceipt:
    status: str
    provider: str
    model: str
    summary: str
    changed_artifacts: list[str]
    blockers: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionBackend:
    def dispatch(self, envelope: DispatchEnvelope) -> DispatchReceipt:
        raise NotImplementedError


class MockExecutionBackend(ExecutionBackend):
    def dispatch(self, envelope: DispatchEnvelope) -> DispatchReceipt:
        return DispatchReceipt(
            status="dispatched",
            provider=envelope.model_selection.provider,
            model=envelope.model_selection.model,
            summary=f"Dispatched {envelope.role} for phase {envelope.phase}.",
            changed_artifacts=envelope.owned_outputs,
            blockers=[],
        )


def model_selection_for_role(role: str) -> ModelSelection:
    config = load_models_config()
    roles = config.get("roles", {})
    if role not in roles:
        raise KeyError(f"Role '{role}' has no model configuration.")
    selection = roles[role]
    if not isinstance(selection, dict):
        raise ValueError(f"Role '{role}' model selection must be a mapping.")
    return ModelSelection(
        provider=selection["provider"],
        model=selection["model"],
        mode=selection.get("mode", config.get("default_mode", "one-shot")),
        options=dict(selection.get("options", {})),
    )


def backend_for_provider(provider: str) -> ExecutionBackend:
    providers = load_models_config().get("providers", {})
    if provider not in providers:
        raise KeyError(f"Unknown provider: {provider}")
    return MockExecutionBackend()


def dispatch(envelope: DispatchEnvelope) -> DispatchReceipt:
    backend = backend_for_provider(envelope.model_selection.provider)
    return backend.dispatch(envelope)
