from __future__ import annotations

from typing import Any
from uuid import uuid4

from context_slicer import build_context_slice
from execution import DispatchEnvelope, model_selection_for_role
from skill_loader import load_role_skill_contracts, validate_skill_inputs, validate_skill_outputs
from spec_loader import phase_spec


PHASE_OBJECTIVES = {
    "requirements": "Produce an implementation-ready requirements baseline.",
    "architecture": "Produce an implementation-safe design for the current requirements baseline.",
    "development": "Implement the approved design and add supporting unit tests.",
    "review": "Review the implementation and produce a clear technical review decision.",
    "testing": "Validate the implementation and produce the current Definition of Done record.",
}


def _owned_outputs(phase: str, role_spec: dict[str, Any]) -> list[str]:
    phase_outputs = phase_spec(phase).get("artifact")
    outputs = list(role_spec.get("writes", []))
    if isinstance(phase_outputs, str):
        outputs.append(f"docs/{phase_outputs}/current.yaml")
        outputs.append(f"docs/{phase_outputs}/current.md")
    return list(dict.fromkeys(outputs))


def build_phase_dispatch_envelope(
    phase: str,
    team_spec: dict[str, Any],
    state: dict[str, Any],
) -> DispatchEnvelope:
    role = phase_spec(phase)["owner"]
    role_spec = team_spec["roles"][role]
    contracts = load_role_skill_contracts(role_spec)
    context_slice = build_context_slice(role, state)
    available_inputs = _available_inputs_for_role(role, phase)
    messages = validate_skill_inputs(contracts, available_inputs)
    messages.extend(validate_skill_outputs(contracts))
    if messages:
        raise ValueError("; ".join(messages))

    return DispatchEnvelope(
        role=role,
        phase=phase,
        objective=PHASE_OBJECTIVES.get(phase, "Complete the assigned phase work."),
        context_slice=context_slice,
        owned_outputs=_owned_outputs(phase, role_spec),
        skill_contracts=contracts,
        model_selection=model_selection_for_role(role),
        correlation_id=uuid4().hex,
    )


def build_specialist_payload(role: str, team_spec: dict[str, Any], state: dict[str, Any], objective: str) -> dict[str, Any]:
    role_spec = team_spec["roles"][role]
    contracts = load_role_skill_contracts(role_spec)
    context_slice = build_context_slice(role, state)
    return {
        "role": role,
        "objective": objective,
        "context_slice": context_slice,
        "skill_contracts": contracts,
        "owned_outputs": list(role_spec.get("writes", [])),
    }


def _available_inputs_for_role(role: str, phase: str) -> set[str]:
    inputs = {
        "user need from the coordinator",
        "docs/requirements/current.md",
        "docs/requirements/current.yaml",
        "docs/design/current.md",
        "docs/design/current.yaml",
        "docs/review/current.md",
        "docs/review/current.yaml",
        "docs/dod/current.md",
        "docs/dod/current.yaml",
        "relevant project memory in framework/memory/",
        "project memory in framework/memory/",
        "framework/clean-code.md",
        "framework/runtime/review-template.md",
        "current dod artifact",
        "implementation and existing tests",
        "relevant code in src/",
        "relevant implementation and tests in src/",
    }
    inputs.update({"state", role, phase})
    return inputs
