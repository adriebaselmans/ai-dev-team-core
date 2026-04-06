from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RolePromptConfig:
    role: str
    layers: tuple[str, ...]
    prompt: str
    prompt_hash: str

    def as_dict(self, *, include_prompt: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "role": self.role,
            "layers": list(self.layers),
            "prompt_hash": self.prompt_hash,
        }
        if include_prompt:
            payload["prompt"] = self.prompt
        return payload


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def team_config_path(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / ".ai-team" / "framework" / "runtime" / "team.yaml"


def load_role_prompt_map(path: str | Path | None = None) -> dict[str, RolePromptConfig]:
    config_path = Path(path) if path is not None else team_config_path()
    root = config_path.resolve().parents[3]
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    bundles = config.get("prompt_bundles", {})
    if not isinstance(bundles, dict):
        raise ValueError(f"Expected 'prompt_bundles' mapping in {config_path}.")

    roles = config.get("roles", {})
    if not isinstance(roles, dict):
        raise ValueError(f"Expected 'roles' mapping in {config_path}.")

    resolved_bundle_cache: dict[str, list[Path]] = {}
    prompt_map: dict[str, RolePromptConfig] = {}

    for role_key, role_spec in roles.items():
        if not isinstance(role_spec, dict):
            raise ValueError(f"Role config for '{role_key}' must be a mapping.")
        prompt_spec = role_spec.get("prompt", {})
        if prompt_spec is None:
            prompt_spec = {}
        if not isinstance(prompt_spec, dict):
            raise ValueError(f"Prompt config for role '{role_key}' must be a mapping.")

        layer_paths: list[Path] = []
        for bundle_name in _normalize_names(prompt_spec.get("extends")):
            layer_paths.extend(_resolve_bundle(bundle_name, bundles, resolved_bundle_cache, root, stack=()))

        role_prompt_path = _resolve_path(
            root,
            prompt_spec.get("role_file", f".ai-team/framework/roles/{role_key}.md"),
        )
        if not role_prompt_path.exists():
            raise FileNotFoundError(f"Prompt layer for role '{role_key}' was not found: {role_prompt_path}")
        layer_paths.append(role_prompt_path)

        unique_paths = _dedupe_paths(layer_paths)
        rendered_prompt = _compose_prompt(unique_paths)
        prompt_map[str(role_key)] = RolePromptConfig(
            role=str(role_key),
            layers=tuple(_relative_posix(path, root) for path in unique_paths),
            prompt=rendered_prompt,
            prompt_hash=sha256(rendered_prompt.encode("utf-8")).hexdigest(),
        )

    return prompt_map


def validate_role_prompt_map(prompt_map: dict[str, RolePromptConfig], role_keys: list[str]) -> None:
    missing = sorted(set(role_keys) - set(prompt_map))
    if missing:
        raise KeyError(f"Missing prompt mapping for roles: {', '.join(missing)}")


def _resolve_bundle(
    bundle_name: str,
    bundles: dict[str, Any],
    cache: dict[str, list[Path]],
    root: Path,
    *,
    stack: tuple[str, ...],
) -> list[Path]:
    if bundle_name in cache:
        return list(cache[bundle_name])
    if bundle_name in stack:
        cycle = " -> ".join([*stack, bundle_name])
        raise ValueError(f"Prompt bundle cycle detected: {cycle}")

    try:
        bundle_spec = bundles[bundle_name]
    except KeyError as exc:
        raise KeyError(f"Unknown prompt bundle '{bundle_name}'.") from exc
    if not isinstance(bundle_spec, dict):
        raise ValueError(f"Prompt bundle '{bundle_name}' must be a mapping.")

    layer_paths: list[Path] = []
    next_stack = (*stack, bundle_name)
    for parent_name in _normalize_names(bundle_spec.get("extends")):
        layer_paths.extend(_resolve_bundle(parent_name, bundles, cache, root, stack=next_stack))
    for layer in _normalize_names(bundle_spec.get("layers")):
        layer_path = _resolve_path(root, layer)
        if not layer_path.exists():
            raise FileNotFoundError(f"Prompt bundle '{bundle_name}' references missing layer: {layer_path}")
        layer_paths.append(layer_path)

    resolved = _dedupe_paths(layer_paths)
    cache[bundle_name] = resolved
    return list(resolved)


def _compose_prompt(paths: list[Path]) -> str:
    parts = [path.read_text(encoding="utf-8").strip() for path in paths]
    return "\n\n".join(part for part in parts if part).strip() + "\n"


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def _normalize_names(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if not isinstance(value, list):
        raise ValueError("Prompt bundle references must be a string or list of strings.")
    names: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("Prompt bundle references must contain only strings.")
        cleaned = item.strip()
        if cleaned:
            names.append(cleaned)
    return names


def _resolve_path(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Prompt paths must be non-empty strings.")
    path = Path(value)
    return path if path.is_absolute() else root / path


def _relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()
