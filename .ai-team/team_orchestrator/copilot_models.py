from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class CopilotRoleModelConfig:
    role: str
    model: tuple[str, ...] = ()
    inherit_picker: bool = False
    reasoning_note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["model"] = list(self.model)
        return payload


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def copilot_role_models_path() -> Path:
    return repo_root() / ".ai-team" / "framework" / "config" / "copilot_role_models.yaml"


def load_copilot_role_model_map(
    path: str | Path | None = None,
) -> dict[str, CopilotRoleModelConfig]:
    config_path = Path(path) if path is not None else copilot_role_models_path()
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    roles = config.get("roles", {})
    if not isinstance(roles, dict):
        raise ValueError(f"Expected 'roles' mapping in {config_path}.")

    model_map: dict[str, CopilotRoleModelConfig] = {}
    for role_key, value in roles.items():
        if not isinstance(value, dict):
            raise ValueError(f"Copilot model config for role '{role_key}' must be a mapping.")
        model_value = value.get("model", [])
        if isinstance(model_value, str):
            model = (model_value,)
        elif isinstance(model_value, list):
            model = tuple(str(item) for item in model_value)
        else:
            raise ValueError(f"Role '{role_key}' has invalid model configuration in {config_path}.")
        model_map[str(role_key)] = CopilotRoleModelConfig(
            role=str(role_key),
            model=model,
            inherit_picker=bool(value.get("inherit_picker", False)),
            reasoning_note=str(value["reasoning_note"]) if value.get("reasoning_note") else None,
        )
    return model_map


def validate_copilot_role_model_map(
    model_map: dict[str, CopilotRoleModelConfig],
    role_keys: list[str],
) -> None:
    missing = sorted(set(role_keys) - set(model_map))
    if missing:
        raise KeyError(f"Missing Copilot role model mapping for roles: {', '.join(missing)}")
