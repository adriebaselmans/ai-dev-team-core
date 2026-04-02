from __future__ import annotations

from framework.runtime.spec_loader import load_team_spec


def _collaboration_roles(payload: dict[str, object], key: str) -> set[str]:
    collaboration = payload.get("collaboration", {})
    if not isinstance(collaboration, dict):
        return set()
    entries = collaboration.get(key, [])
    if not isinstance(entries, list):
        return set()
    roles: set[str] = set()
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("role"), str):
            roles.add(entry["role"])
    return roles


def test_scout_support_contract_covers_architect_and_developer() -> None:
    team_spec = load_team_spec()
    roles = team_spec["roles"]

    scout_optional = _collaboration_roles(roles["scout"], "optional")
    developer_optional = _collaboration_roles(roles["developer"], "optional")

    assert "architect" in scout_optional
    assert "developer" in scout_optional
    assert "scout" in developer_optional
