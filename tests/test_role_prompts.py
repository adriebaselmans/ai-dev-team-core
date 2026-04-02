from __future__ import annotations

from agents.registry import build_default_agent_registry
from flows import default_flow_path
from state.factory import create_initial_state
from team_orchestrator.engine import Orchestrator
from team_orchestrator.flow_loader import load_flow
from team_orchestrator.prompts import load_role_prompt_map


def test_role_prompt_map_covers_all_active_roles() -> None:
    prompt_map = load_role_prompt_map()
    roles = set(build_default_agent_registry())
    assert roles.issubset(set(prompt_map))


def test_developer_prompt_layers_base_plus_role_prompt() -> None:
    prompt_map = load_role_prompt_map()
    developer_prompt = prompt_map["developer"]

    assert developer_prompt.layers == (
        "framework/prompts/base-system.md",
        "framework/prompts/specialist-base.md",
        "framework/roles/developer.md",
    )
    assert "You are part of the AI dev team framework." in developer_prompt.prompt
    assert "You are a specialist role inside the AI dev team framework." in developer_prompt.prompt
    assert "## Mission" in developer_prompt.prompt
    assert developer_prompt.prompt.index("You are part of the AI dev team framework.") < developer_prompt.prompt.index(
        "You are a specialist role inside the AI dev team framework."
    )


def test_trace_and_state_include_prompt_metadata() -> None:
    orchestrator = Orchestrator(load_flow(default_flow_path()), build_default_agent_registry())
    final_state = orchestrator.run(create_initial_state("Refactor the orchestration runtime."))

    developer_entry = next(entry for entry in final_state["trace"] if entry["role"] == "developer")
    assert developer_entry["prompt"]["layers"] == [
        "framework/prompts/base-system.md",
        "framework/prompts/specialist-base.md",
        "framework/roles/developer.md",
    ]
    assert final_state["meta"]["role_prompts"]["coordinator"]["layers"] == [
        "framework/prompts/base-system.md",
        "framework/prompts/coordinator-base.md",
        "framework/roles/coordinator.md",
    ]
