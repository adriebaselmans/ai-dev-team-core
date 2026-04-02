from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    backend: str
    options: dict[str, Any] | None = None
    env: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["options"] = dict(self.options or {})
        payload["env"] = dict(self.env or {})
        return payload


@dataclass(frozen=True)
class RoleModelConfig:
    role: str
    provider: str
    backend: str
    model: str
    mode: str
    placeholder: bool = False
    options: dict[str, Any] | None = None
    provider_options: dict[str, Any] | None = None
    env: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["options"] = dict(self.options or {})
        payload["provider_options"] = dict(self.provider_options or {})
        payload["env"] = dict(self.env or {})
        return payload


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def models_config_path() -> Path:
    return repo_root() / "framework" / "config" / "models.yaml"


def load_provider_map(path: str | Path | None = None) -> dict[str, ProviderConfig]:
    config_path = Path(path) if path is not None else models_config_path()
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    providers = config.get("providers", {})
    if not isinstance(providers, dict):
        raise ValueError(f"Expected 'providers' mapping in {config_path}.")

    provider_map: dict[str, ProviderConfig] = {}
    for provider_name, value in providers.items():
        if not isinstance(value, dict):
            raise ValueError(f"Provider config for '{provider_name}' must be a mapping.")
        provider_map[str(provider_name)] = ProviderConfig(
            name=str(provider_name),
            backend=str(value["backend"]),
            options=dict(value.get("options", {})),
            env={str(key): str(item) for key, item in dict(value.get("env", {})).items()},
        )
    return provider_map


def load_role_model_map(path: str | Path | None = None) -> dict[str, RoleModelConfig]:
    config_path = Path(path) if path is not None else models_config_path()
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    provider_map = load_provider_map(config_path)
    roles = config.get("roles", {})
    if not isinstance(roles, dict):
        raise ValueError(f"Expected 'roles' mapping in {config_path}.")

    model_map: dict[str, RoleModelConfig] = {}
    for role_key, value in roles.items():
        if not isinstance(value, dict):
            raise ValueError(f"Model config for role '{role_key}' must be a mapping.")
        provider_name = str(value["provider"])
        try:
            provider = provider_map[provider_name]
        except KeyError as exc:
            raise KeyError(
                f"Role '{role_key}' references unknown provider '{provider_name}'."
            ) from exc
        model_map[str(role_key)] = RoleModelConfig(
            role=str(role_key),
            provider=provider_name,
            backend=provider.backend,
            model=str(value["model"]),
            mode=str(value.get("mode", config.get("default_mode", "one-shot"))),
            placeholder=bool(value.get("placeholder", False)),
            options=dict(value.get("options", {})),
            provider_options=dict(provider.options or {}),
            env=dict(provider.env or {}),
        )
    return model_map


def validate_role_model_map(model_map: dict[str, RoleModelConfig], role_keys: list[str]) -> None:
    missing = sorted(set(role_keys) - set(model_map))
    if missing:
        raise KeyError(f"Missing model mapping for roles: {', '.join(missing)}")
