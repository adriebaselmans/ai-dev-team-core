from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from spec_loader import phase_spec, repo_root


STATE_PATH = repo_root() / "framework" / "runtime" / "state.json"


DEFAULT_STATE: dict[str, Any] = {
    "version": 2,
    "runtime": "model-agnostic",
    "active_feature": None,
    "phase": "idle",
    "owner": "coordinator",
    "state": "ready for first user need",
    "next_action": "receive a user need and start requirements clarification",
    "last_completed_phase": None,
    "pending_trigger": None,
    "user_input_required": False,
    "artifacts": {},
    "last_transition": None,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return deepcopy(DEFAULT_STATE)
    with STATE_PATH.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    state = deepcopy(DEFAULT_STATE)
    state.update(raw)
    return state


def save_state(state: dict[str, Any]) -> dict[str, Any]:
    state_to_save = deepcopy(DEFAULT_STATE)
    state_to_save.update(state)
    STATE_PATH.write_text(json.dumps(state_to_save, indent=2) + "\n", encoding="utf-8")
    return state_to_save


def mark_phase_validation(state: dict[str, Any], phase: str, valid: bool, messages: list[str]) -> dict[str, Any]:
    artifacts = deepcopy(state.get("artifacts", {}))
    artifacts[phase] = {
        "valid": valid,
        "messages": messages,
        "validated_at": now_iso(),
    }
    state["artifacts"] = artifacts
    return state


def transition_state(
    state: dict[str, Any],
    *,
    phase: str,
    state_text: str,
    next_action: str,
    last_completed_phase: str | None = None,
    pending_trigger: str | None = None,
    user_input_required: bool | None = None,
) -> dict[str, Any]:
    state["phase"] = phase
    state["owner"] = phase_spec(phase)["owner"]
    state["state"] = state_text
    state["next_action"] = next_action
    state["last_transition"] = now_iso()
    state["pending_trigger"] = pending_trigger
    if last_completed_phase is not None:
        state["last_completed_phase"] = last_completed_phase
    if user_input_required is not None:
        state["user_input_required"] = user_input_required
    return state
