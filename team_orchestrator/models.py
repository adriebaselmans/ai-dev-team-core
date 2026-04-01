from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RoleModelConfig:
    role: str
    provider: str
    model: str
    mode: str
    placeholder: bool = False
    options: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["options"] = dict(self.options or {})
        return payload


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def models_config_path() -> Path:
    return repo_root() / "framework" / "config" / "models.yaml"


def load_role_model_map(path: str | Path | None = None) -> dict[str, RoleModelConfig]:
    config_path = Path(path) if path is not None else models_config_path()
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    roles = config.get("roles", {})
    if not isinstance(roles, dict):
        raise ValueError(f"Expected 'roles' mapping in {config_path}.")

    model_map: dict[str, RoleModelConfig] = {}
    for role_key, value in roles.items():
        if not isinstance(value, dict):
            raise ValueError(f"Model config for role '{role_key}' must be a mapping.")
        model_map[str(role_key)] = RoleModelConfig(
            role=str(role_key),
            provider=str(value["provider"]),
            model=str(value["model"]),
            mode=str(value.get("mode", config.get("default_mode", "one-shot"))),
            placeholder=bool(value.get("placeholder", False)),
            options=dict(value.get("options", {})),
        )
    return model_map


def validate_role_model_map(model_map: dict[str, RoleModelConfig], role_keys: list[str]) -> None:
    missing = sorted(set(role_keys) - set(model_map))
    if missing:
        raise KeyError(f"Missing model mapping for roles: {', '.join(missing)}")
