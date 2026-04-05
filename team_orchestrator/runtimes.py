from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class HostRuntimeConfig:
    name: str
    kind: str
    primary: bool = False
    capabilities: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["capabilities"] = list(self.capabilities)
        payload["notes"] = list(self.notes)
        return payload


@dataclass(frozen=True)
class RoleRuntimeConfig:
    role: str
    primary_host: str
    compatible_hosts: tuple[str, ...] = ()
    agent_profile: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["compatible_hosts"] = list(self.compatible_hosts)
        return payload


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def runtimes_config_path() -> Path:
    return repo_root() / "framework" / "config" / "runtimes.yaml"


def load_host_runtime_map(path: str | Path | None = None) -> dict[str, HostRuntimeConfig]:
    config_path = Path(path) if path is not None else runtimes_config_path()
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    hosts = config.get("hosts", {})
    if not isinstance(hosts, dict):
        raise ValueError(f"Expected 'hosts' mapping in {config_path}.")

    host_map: dict[str, HostRuntimeConfig] = {}
    for host_name, value in hosts.items():
        if not isinstance(value, dict):
            raise ValueError(f"Runtime host config for '{host_name}' must be a mapping.")
        host_map[str(host_name)] = HostRuntimeConfig(
            name=str(host_name),
            kind=str(value["kind"]),
            primary=bool(value.get("primary", False)),
            capabilities=tuple(str(item) for item in value.get("capabilities", [])),
            notes=tuple(str(item) for item in value.get("notes", [])),
        )
    return host_map


def load_role_runtime_map(path: str | Path | None = None) -> dict[str, RoleRuntimeConfig]:
    config_path = Path(path) if path is not None else runtimes_config_path()
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    host_map = load_host_runtime_map(config_path)
    roles = config.get("roles", {})
    if not isinstance(roles, dict):
        raise ValueError(f"Expected 'roles' mapping in {config_path}.")

    runtime_map: dict[str, RoleRuntimeConfig] = {}
    for role_key, value in roles.items():
        if not isinstance(value, dict):
            raise ValueError(f"Runtime config for role '{role_key}' must be a mapping.")
        primary_host = str(value["primary_host"])
        if primary_host not in host_map:
            raise KeyError(
                f"Role '{role_key}' references unknown primary host '{primary_host}'."
            )
        compatible_hosts = tuple(str(item) for item in value.get("compatible_hosts", []))
        missing_hosts = sorted(set(compatible_hosts) - set(host_map))
        if missing_hosts:
            raise KeyError(
                f"Role '{role_key}' references unknown compatible hosts: {', '.join(missing_hosts)}"
            )
        runtime_map[str(role_key)] = RoleRuntimeConfig(
            role=str(role_key),
            primary_host=primary_host,
            compatible_hosts=compatible_hosts,
            agent_profile=str(value["agent_profile"]) if value.get("agent_profile") else None,
        )
    return runtime_map


def validate_role_runtime_map(
    runtime_map: dict[str, RoleRuntimeConfig],
    role_keys: list[str],
) -> None:
    missing = sorted(set(role_keys) - set(runtime_map))
    if missing:
        raise KeyError(f"Missing runtime mapping for roles: {', '.join(missing)}")
