from __future__ import annotations

from agents.discovery import discover_roles
from team_orchestrator.copilot_models import (
    load_copilot_role_model_map,
    validate_copilot_role_model_map,
)


def test_copilot_model_map_covers_all_framework_roles() -> None:
    model_map = load_copilot_role_model_map()
    validate_copilot_role_model_map(model_map, [role.key for role in discover_roles()])


def test_architect_and_developer_have_explicit_copilot_model_preferences() -> None:
    model_map = load_copilot_role_model_map()

    assert model_map["architect"].model
    assert model_map["developer"].model
    assert model_map["architect"].inherit_picker is False
    assert model_map["developer"].inherit_picker is False
