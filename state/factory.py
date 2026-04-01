from __future__ import annotations

from copy import deepcopy
from typing import Any

from state.merge import merge_state


DEFAULT_STATE: dict[str, Any] = {
    "input": "",
    "repository": {
        "mode": None,
        "path": None,
        "facts": [],
    },
    "coordination": None,
    "requirements": None,
    "ux_ui": None,
    "analysis": None,
    "research": None,
    "design": None,
    "development": None,
    "review": None,
    "test_results": None,
    "dod_review": None,
    "support_request": None,
    "trace": [],
    "meta": {
        "flow_name": None,
        "roles": [],
        "role_models": {},
        "current_step": None,
        "last_role": None,
        "last_next_step": None,
        "iteration": 0,
        "max_iterations": 5,
        "executed_steps": 0,
        "max_steps": 40,
        "max_step_visits": 8,
        "visit_counts": {},
        "step_history": [],
        "completed_support_requests": [],
        "terminated": False,
        "completed": False,
        "termination_reason": None,
        "autonomous": True,
    },
}


def create_initial_state(
    user_input: str,
    *,
    max_iterations: int = 5,
    max_steps: int = 40,
    max_step_visits: int = 8,
    autonomous: bool = True,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = deepcopy(DEFAULT_STATE)
    state["input"] = user_input
    state["meta"]["max_iterations"] = max_iterations
    state["meta"]["max_steps"] = max_steps
    state["meta"]["max_step_visits"] = max_step_visits
    state["meta"]["autonomous"] = autonomous
    if overrides:
        state = merge_state(state, overrides)
    return state


def prepare_state(state: dict[str, Any], *, role_keys: list[str], flow_name: str) -> dict[str, Any]:
    prepared = merge_state(DEFAULT_STATE, state)
    prepared["meta"]["roles"] = list(role_keys)
    prepared["meta"]["flow_name"] = flow_name
    return prepared
