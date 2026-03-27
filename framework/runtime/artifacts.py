from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from spec_loader import load_artifact_schema, repo_root


ARTIFACT_FILES = {
    "requirements": {
        "yaml": "docs/requirements/current.yaml",
        "markdown": "docs/requirements/current.md",
    },
    "design": {
        "yaml": "docs/design/current.yaml",
        "markdown": "docs/design/current.md",
    },
    "review": {
        "yaml": "docs/review/current.yaml",
        "markdown": "docs/review/current.md",
    },
    "dod": {
        "yaml": "docs/dod/current.yaml",
        "markdown": "docs/dod/current.md",
    },
}


def artifact_paths(name: str) -> dict[str, Path]:
    try:
        mapping = ARTIFACT_FILES[name]
    except KeyError as exc:
        raise KeyError(f"Unknown artifact: {name}") from exc
    return {kind: repo_root() / rel_path for kind, rel_path in mapping.items()}


def load_artifact(name: str) -> dict[str, Any]:
    yaml_path = artifact_paths(name)["yaml"]
    with yaml_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {yaml_path}")
    return data


def save_artifact(name: str, data: dict[str, Any]) -> None:
    validate_artifact_data(name, data)
    paths = artifact_paths(name)
    paths["yaml"].write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    paths["markdown"].write_text(render_artifact_markdown(name, data), encoding="utf-8")


def artifact_summary(name: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = data or load_artifact(name)
    schema = load_artifact_schema(name)
    summary_fields = schema.get("summary_fields", [])
    return {field: payload.get(field) for field in summary_fields if field in payload}


def validate_artifact_data(name: str, data: dict[str, Any]) -> list[str]:
    schema = load_artifact_schema(name)
    messages: list[str] = []
    required_fields = schema.get("required_fields", [])
    for field in required_fields:
        if field not in data:
            messages.append(f"{name} artifact is missing '{field}'.")
            continue
        value = data[field]
        if value in ("", None):
            messages.append(f"{name} artifact field '{field}' is empty.")

    field_types = schema.get("field_types", {})
    for field, expected in field_types.items():
        if field not in data:
            continue
        value = data[field]
        if expected == "string" and not isinstance(value, str):
            messages.append(f"{name} artifact field '{field}' must be a string.")
        if expected == "list" and not isinstance(value, list):
            messages.append(f"{name} artifact field '{field}' must be a list.")
    return messages


def _render_scalar(value: Any) -> str:
    if value in ("", None):
        return "- None"
    if isinstance(value, bool):
        return f"- {'true' if value else 'false'}"
    return f"- {value}"


def _render_value(value: Any, level: int = 0) -> list[str]:
    indent = "  " * level
    if isinstance(value, list):
        if not value:
            return [f"{indent}- None"]
        lines: list[str] = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{indent}-")
                lines.extend(_render_value(item, level + 1))
            else:
                lines.append(f"{indent}- {item}")
        return lines
    if isinstance(value, dict):
        if not value:
            return [f"{indent}- None"]
        lines: list[str] = []
        for key, item in value.items():
            label = key.replace("_", " ").title()
            if isinstance(item, (dict, list)):
                lines.append(f"{indent}- {label}:")
                lines.extend(_render_value(item, level + 1))
            else:
                lines.append(f"{indent}- {label}: {item}")
        return lines
    return [f"{indent}{_render_scalar(value)}".replace(f"{indent}-", f"{indent}-", 1)]


def render_artifact_markdown(name: str, data: dict[str, Any]) -> str:
    schema = load_artifact_schema(name)
    title = schema.get("title", name.title())
    sections = schema.get("markdown_sections", [])
    lines = [f"# {title}", "", "Derived from the structured YAML artifact.", ""]
    for section in sections:
        heading = section["heading"]
        field = section["field"]
        lines.append(f"## {heading}")
        lines.extend(_render_value(data.get(field)))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_all_artifacts() -> None:
    for name in ARTIFACT_FILES:
        save_artifact(name, load_artifact(name))
