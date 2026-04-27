from __future__ import annotations

from pathlib import Path

from agents.registry import build_default_agent_registry
from flows import default_flow_path
from state.factory import create_initial_state
from team_orchestrator.engine import Orchestrator
from team_orchestrator.flow_loader import load_flow
from team_orchestrator.runtimes import load_host_runtime_map, load_role_runtime_map


def test_runtime_map_covers_all_active_roles() -> None:
    runtime_map = load_role_runtime_map()
    roles = set(build_default_agent_registry())
    assert roles.issubset(set(runtime_map))


def test_host_runtime_map_declares_native_and_instruction_hosts() -> None:
    host_map = load_host_runtime_map()

    assert host_map["native-agent-host"].primary is True
    assert "custom-agents" in host_map["native-agent-host"].capabilities
    assert "instruction-file-host" in host_map


def test_trace_entries_include_role_runtime_metadata() -> None:
    orchestrator = Orchestrator(load_flow(default_flow_path()), build_default_agent_registry())
    final_state = orchestrator.run(create_initial_state("Refactor the orchestration runtime."))

    developer_entries = [entry for entry in final_state["trace"] if entry["role"] == "developer"]
    assert developer_entries
    for entry in developer_entries:
        assert entry["runtime"]["primary_host"] == "native-agent-host"
        assert "instruction-file-host" in entry["runtime"]["compatible_hosts"]


def test_runtime_agent_profile_paths_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime_map = load_role_runtime_map()

    for config in runtime_map.values():
        assert config.agent_profile
        assert (root / config.agent_profile).exists()
