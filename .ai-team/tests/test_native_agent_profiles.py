from __future__ import annotations

from pathlib import Path

import yaml

from agents.discovery import discover_roles
from team_orchestrator.copilot_models import load_copilot_role_model_map
from team_orchestrator.runtimes import load_role_runtime_map


def _load_profile(root: Path, relative_path: str) -> tuple[dict[str, object], str]:
    text = (root / relative_path).read_text(encoding="utf-8")
    parts = text.split("---", 2)
    assert len(parts) == 3, f"{relative_path} must contain YAML frontmatter."
    frontmatter = yaml.safe_load(parts[1]) or {}
    assert isinstance(frontmatter, dict), f"{relative_path} frontmatter must be a mapping."
    return frontmatter, parts[2]


def _load_team_roles(root: Path) -> dict[str, dict[str, object]]:
    config = yaml.safe_load((root / ".ai-team" / "framework" / "runtime" / "team.yaml").read_text(encoding="utf-8"))
    assert isinstance(config, dict)
    roles = config["roles"]
    assert isinstance(roles, dict)
    return roles


def test_native_agent_profiles_cover_all_framework_roles() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime_map = load_role_runtime_map()

    for role in discover_roles():
        profile = runtime_map[role.key].agent_profile
        assert profile is not None
        assert (root / profile).exists()


def test_coordinator_agent_profile_declares_specialist_agents() -> None:
    root = Path(__file__).resolve().parents[2]
    frontmatter, profile = _load_profile(root, ".github/agents/coordinator.agent.md")

    assert frontmatter["target"] == "vscode"
    assert frontmatter["user-invocable"] is True
    assert frontmatter["disable-model-invocation"] is True
    assert "agent" in frontmatter["tools"]
    assert "edit" not in frontmatter["tools"]
    assert "requirements-engineer" in frontmatter["agents"]
    assert "architect" in frontmatter["agents"]
    assert "developer" in frontmatter["agents"]
    assert "reviewer" in frontmatter["agents"]
    assert "tester" in frontmatter["agents"]
    assert "dod-reviewer" in frontmatter["agents"]
    assert ".ai-team/framework/AGENTS.md" in profile


def test_specialist_profiles_reference_framework_role_docs() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime_map = load_role_runtime_map()

    for role_key, config in runtime_map.items():
        frontmatter, profile = _load_profile(root, str(config.agent_profile))
        assert frontmatter["target"] == "vscode"
        if role_key == "coordinator":
            assert ".ai-team/framework/AGENTS.md" in profile
        else:
            assert frontmatter["user-invocable"] is False
            assert f".ai-team/framework/roles/{role_key}.md" in profile


def test_only_coordinator_declares_subagents_or_handoffs() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime_map = load_role_runtime_map()

    for role_key, config in runtime_map.items():
        frontmatter, _ = _load_profile(root, str(config.agent_profile))
        if role_key == "coordinator":
            assert set(frontmatter.get("agents", [])) == {
                "requirements-engineer",
                "ux-ui-designer",
                "explorer",
                "scout",
                "architect",
                "developer",
                "reviewer",
                "tester",
                "dod-reviewer",
            }
            continue
        assert "agents" not in frontmatter
        assert "handoffs" not in frontmatter


def test_native_profile_tool_scopes_match_team_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime_map = load_role_runtime_map()
    team_roles = _load_team_roles(root)

    for role_key, config in runtime_map.items():
        frontmatter, _ = _load_profile(root, str(config.agent_profile))
        tools = set(frontmatter["tools"])
        role_contract = team_roles[role_key]
        writes = role_contract.get("writes", [])
        read_only = bool(role_contract.get("read_only", False))

        if read_only:
            assert "edit" not in tools
        elif writes:
            assert "edit" in tools


def test_native_profile_tool_aliases_cover_role_capabilities() -> None:
    root = Path(__file__).resolve().parents[2]
    expected_aliases = {
        "coordinator": {"read", "search", "agent"},
        "requirements-engineer": {"read", "edit", "search"},
        "ux-ui-designer": {"read", "search", "web"},
        "explorer": {"read", "search"},
        "scout": {"read", "search", "web"},
        "architect": {"read", "edit", "search", "web"},
        "developer": {"read", "edit", "search", "execute"},
        "reviewer": {"read", "edit", "search"},
        "tester": {"read", "edit", "search", "execute"},
        "dod-reviewer": {"read", "edit", "search"},
    }

    runtime_map = load_role_runtime_map()
    for role_key, expected in expected_aliases.items():
        frontmatter, _ = _load_profile(root, str(runtime_map[role_key].agent_profile))
        assert set(frontmatter["tools"]) == expected


def test_copilot_model_preferences_match_agent_profiles() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime_map = load_role_runtime_map()
    model_map = load_copilot_role_model_map()

    for role_key, config in runtime_map.items():
        frontmatter, _ = _load_profile(root, str(config.agent_profile))
        role_model_config = model_map[role_key]
        if role_model_config.inherit_picker:
            assert "model" not in frontmatter
            continue
        assert list(frontmatter["model"]) == list(role_model_config.model)
