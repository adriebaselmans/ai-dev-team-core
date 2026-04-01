from __future__ import annotations

from agents.registry import build_default_agent_registry
from flows import default_flow_path
from state.factory import create_initial_state
from team_orchestrator.engine import Orchestrator
from team_orchestrator.flow_loader import load_flow
from team_orchestrator.models import load_role_model_map


def test_model_map_covers_all_active_roles() -> None:
    model_map = load_role_model_map()
    roles = set(build_default_agent_registry())
    assert roles.issubset(set(model_map))


def test_trace_entries_include_role_model_metadata() -> None:
    orchestrator = Orchestrator(load_flow(default_flow_path()), build_default_agent_registry())
    final_state = orchestrator.run(create_initial_state("Refactor the orchestration runtime."))

    developer_entries = [entry for entry in final_state["trace"] if entry["role"] == "developer"]
    assert developer_entries
    for entry in developer_entries:
        assert entry["model"]["provider"] == "openai"
        assert entry["model"]["model"] == "gpt-5.4"
