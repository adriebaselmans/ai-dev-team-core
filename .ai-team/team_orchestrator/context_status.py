from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from typing import Any

import yaml

VALID_MODES = {"disabled", "detected", "enabled", "required"}
VALID_KINDS = {
    "command-output",
    "context-compression",
    "memory-retrieval",
    "output-style",
    "semantic-code-tools",
}


@dataclass(frozen=True)
class ContextPaths:
    root: Path
    context_dir: Path
    policy_path: Path
    adapters_path: Path


def default_context_paths() -> ContextPaths:
    root = Path(__file__).resolve().parents[2]
    context_dir = root / ".ai-team" / "context"
    return ContextPaths(
        root=root,
        context_dir=context_dir,
        policy_path=context_dir / "policy.yaml",
        adapters_path=context_dir / "adapters.yaml",
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _command_available(command: str) -> bool:
    executable = command.split()[0]
    return which(executable) is not None


def _path_available(root: Path, relative_path: str) -> bool:
    return (root / relative_path).exists()


def _skill_available(root: Path, relative_path: str) -> bool:
    skill_path = root / relative_path
    return skill_path.exists()


def _adapter_available(root: Path, adapter: dict[str, Any]) -> bool:
    detect = adapter.get("detect")
    if not isinstance(detect, dict):
        return True
    if command := detect.get("command"):
        return _command_available(str(command))
    if path := detect.get("path"):
        return _path_available(root, str(path))
    if skill := detect.get("skill"):
        return _skill_available(root, str(skill))
    return True


def load_context_config(paths: ContextPaths | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = paths or default_context_paths()
    return _load_yaml(resolved.policy_path), _load_yaml(resolved.adapters_path)


def _safe_load_context_config(paths: ContextPaths) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    try:
        policy = _load_yaml(paths.policy_path)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        policy = {}
        errors.append(f"Policy validation failed: {exc}")
    try:
        adapters = _load_yaml(paths.adapters_path)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        adapters = {}
        errors.append(f"Adapter config validation failed: {exc}")
    return policy, adapters, errors


def build_context_status(paths: ContextPaths | None = None) -> dict[str, Any]:
    resolved = paths or default_context_paths()
    policy, adapters_config = load_context_config(resolved)
    adapters = adapters_config.get("adapters", {})
    adapter_status: dict[str, dict[str, Any]] = {}

    for name, adapter in adapters.items():
        if not isinstance(adapter, dict):
            continue
        mode = adapter.get("mode", "disabled")
        available = _adapter_available(resolved.root, adapter)
        active = mode in {"enabled", "required"} or (mode == "detected" and available)
        adapter_status[name] = {
            "kind": adapter.get("kind"),
            "mode": mode,
            "available": available,
            "active": active,
            "fallback": adapter.get("fallback"),
        }

    return {
        "context_dir": resolved.context_dir.relative_to(resolved.root).as_posix(),
        "policy": resolved.policy_path.relative_to(resolved.root).as_posix(),
        "adapters": resolved.adapters_path.relative_to(resolved.root).as_posix(),
        "default_output_mode": policy.get("output_policy", {}).get("default_mode"),
        "memory_store": policy.get("memory_policy", {}).get("canonical_store"),
        "adapter_status": adapter_status,
    }


def build_context_doctor(paths: ContextPaths | None = None) -> dict[str, Any]:
    resolved = paths or default_context_paths()
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    for label, path in {"policy": resolved.policy_path, "adapters": resolved.adapters_path}.items():
        exists = path.exists()
        relative = path.relative_to(resolved.root).as_posix()
        checks.append({"name": f"{label}-exists", "passed": exists, "path": relative})
        if not exists:
            errors.append(f"Missing {label} file: {relative}")

    if errors:
        return {"passed": False, "checks": checks, "errors": errors}

    policy, adapters_config, load_errors = _safe_load_context_config(resolved)
    errors.extend(load_errors)
    if load_errors:
        return {"passed": False, "checks": checks, "errors": errors}
    adapters = adapters_config.get("adapters", {})
    if not isinstance(adapters, dict) or not adapters:
        errors.append("adapters.yaml must define at least one adapter")
    else:
        for name, adapter in adapters.items():
            if not isinstance(adapter, dict):
                errors.append(f"Adapter {name} must be a mapping")
                continue
            mode = adapter.get("mode")
            kind = adapter.get("kind")
            available = _adapter_available(resolved.root, adapter)
            mode_ok = mode in VALID_MODES
            kind_ok = kind in VALID_KINDS
            fallback_ok = bool(adapter.get("fallback")) or adapter.get("optional") is False
            required_ok = mode != "required" or available
            checks.extend(
                [
                    {"name": f"{name}-mode", "passed": mode_ok, "value": mode},
                    {"name": f"{name}-kind", "passed": kind_ok, "value": kind},
                    {"name": f"{name}-fallback", "passed": fallback_ok, "value": adapter.get("fallback")},
                    {"name": f"{name}-required-available", "passed": required_ok, "available": available},
                ]
            )
            if not mode_ok:
                errors.append(f"Adapter {name} has invalid mode {mode!r}")
            if not kind_ok:
                errors.append(f"Adapter {name} has invalid kind {kind!r}")
            if not fallback_ok:
                errors.append(f"Adapter {name} needs a fallback or optional: false")
            if not required_ok:
                errors.append(f"Required adapter {name} is unavailable")

    generated_index = policy.get("memory_policy", {}).get("generated_index")
    if generated_index:
        ignored = _is_ignored_by_git(resolved.root, str(generated_index))
        checks.append({"name": "generated-memory-index-ignored", "passed": ignored, "path": generated_index})
        if not ignored:
            errors.append(f"Generated memory index is not ignored by git: {generated_index}")

    profile_roles = _profile_roles(policy)
    flow_roles = _flow_roles(resolved.root / ".ai-team" / "flows" / "software_delivery.yaml")
    missing_roles = sorted(flow_roles - profile_roles)
    profiles_cover_flow = not missing_roles
    checks.append({"name": "profiles-cover-flow", "passed": profiles_cover_flow, "missing_roles": missing_roles})
    if missing_roles:
        errors.append(f"Context profiles missing flow roles: {', '.join(missing_roles)}")

    return {"passed": not errors, "checks": checks, "errors": errors}


def _profile_roles(policy: dict[str, Any]) -> set[str]:
    profiles = policy.get("profiles", {})
    if not isinstance(profiles, dict):
        return set()
    return {str(profile.get("role")) for profile in profiles.values() if isinstance(profile, dict) and profile.get("role")}


def _flow_roles(flow_path: Path) -> set[str]:
    flow = _load_yaml(flow_path)
    steps = flow.get("steps", {})
    if not isinstance(steps, dict):
        return set()
    roles = {
        str(step.get("agent"))
        for step in steps.values()
        if isinstance(step, dict) and step.get("kind") in {"agent", "parallel-agent"} and step.get("agent")
    }
    roles.add("explorer")
    return roles


def _is_ignored_by_git(root: Path, relative_path: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", relative_path],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False
    return result.returncode == 0
