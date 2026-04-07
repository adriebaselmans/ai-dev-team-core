from __future__ import annotations

from pathlib import Path

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


def test_codex_entry_contract_enforces_role_discipline() -> None:
    root = Path(__file__).resolve().parents[2]
    entry = (root / "AGENTS.md").read_text(encoding="utf-8")
    framework = (root / ".ai-team" / "framework" / "AGENTS.md").read_text(encoding="utf-8")
    coordinator = (root / ".ai-team" / "framework" / "roles" / "coordinator.md").read_text(encoding="utf-8")

    assert "State the active role before substantial work." in entry
    assert "If the coordinator starts implementing anyway, treat that as a workflow violation" in entry
    assert "Do not collapse multiple specialist phases into one implicit coordinator pass." in entry
    assert "Prefer success-first tool handling" in entry
    assert "do not collapse coordinator, architect, developer, reviewer, tester, or DoD reviewer" in framework
    assert "Prefer success-first tool handling" in framework
    assert "Do not treat review or testing as the first place compiler or type errors are discovered" in framework
    assert "a specialist phase counts as executed only when the active role has been explicitly switched" in framework
    assert "Treat any coordinator-side implementation edit as a workflow violation" in coordinator
