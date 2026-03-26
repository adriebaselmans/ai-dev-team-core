from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def runtime_dir() -> Path:
    return Path(__file__).resolve().parent


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_team_spec() -> dict[str, Any]:
    return load_yaml(runtime_dir() / "team.yaml")


def load_workflow_spec() -> dict[str, Any]:
    return load_yaml(runtime_dir() / "workflow.yaml")


def phase_spec(phase: str) -> dict[str, Any]:
    workflow = load_workflow_spec()
    specs = workflow.get("phase_specs", {})
    if phase not in specs:
        raise KeyError(f"Unknown phase: {phase}")
    return specs[phase]
